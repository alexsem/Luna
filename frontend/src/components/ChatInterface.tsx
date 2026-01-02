import React, { useState, useEffect, useRef } from 'react';
import { sendChat, stopGeneration } from '../api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAppContext } from '../AppContext';
import { ChatMessage, Mood } from '../types';

interface ChatInterfaceProps {
    onHistoryChange?: (history: ChatMessage[]) => void;
    externalPrompt?: string | null;
    onConfigClear?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
    onHistoryChange,
    externalPrompt,
    onConfigClear
}) => {
    const { setMood, projectContext } = useAppContext();
    const [history, setHistory] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Update parent with history whenever it changes
    useEffect(() => {
        if (onHistoryChange) {
            onHistoryChange(history);
        }
    }, [history, onHistoryChange]);

    // Handle External Prompts (from Drafting Board)
    useEffect(() => {
        if (externalPrompt) {
            handleSend(externalPrompt);
            if (onConfigClear) onConfigClear();
        }
    }, [externalPrompt]);

    // Inject Project Context when loaded
    useEffect(() => {
        if (projectContext) {
            const contextMsg: ChatMessage = { role: 'system', content: `[PROJECT SUMMARY LOADED]: ${projectContext}` };
            setHistory(prev => [...prev, contextMsg]);
        }
    }, [projectContext]);

    // Scroll to bottom on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history]);

    const handleSend = async (textOverride: string | null = null) => {
        const textToSend = textOverride || input;
        if (!textToSend.trim() || isGenerating) return;

        const userMsg: ChatMessage = { role: 'user', content: textToSend };
        const newHistory = [...history, userMsg];

        setHistory(newHistory);
        setInput('');
        setIsGenerating(true);
        setMood('thinking');

        // Placeholder for AI message (assistant)
        setHistory(prev => [...prev, { role: 'assistant', content: '' }]);

        let currentResponse = '';

        sendChat(
            userMsg.content,
            newHistory,
            (chunk) => {
                currentResponse += chunk;
                setHistory(prev => {
                    const updated = [...prev];
                    updated[updated.length - 1] = { role: 'assistant', content: currentResponse };
                    return updated;
                });
            },
            (mood) => {
                if (mood) setMood(mood as Mood);
            },
            () => {
                setIsGenerating(false);
                if (textToSend.trim().startsWith("#task:")) {
                    setMood('neutral', 10000);
                }
            },
            (error) => {
                setIsGenerating(false);
                setHistory(prev => [...prev, { role: 'system', content: `Error: ${error}` }]);
            }
        );
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleStop = async () => {
        if (isGenerating) {
            await stopGeneration();
            setIsGenerating(false);
            setHistory(prev => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg) lastMsg.content += " [STOPPED]";
                return updated;
            });
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-history">
                {history.length === 0 && (
                    <div className="empty-chat">
                        <p>Initiate conversation sequence...</p>
                    </div>
                )}

                {history.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                        </ReactMarkdown>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>

            <div className="input-area">
                <textarea
                    className="chat-input"
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                />

                {isGenerating ? (
                    <button className="btn btn-stop" onClick={handleStop}>Stop</button>
                ) : (
                    <button className="btn" onClick={() => handleSend()}>Send</button>
                )}
            </div>
        </div>
    );
};

export default ChatInterface;
