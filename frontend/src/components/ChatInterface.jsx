import React, { useState, useEffect, useRef } from 'react';
import { sendChat, stopGeneration } from '../api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ChatInterface = ({ setMood, onHistoryChange, projectContext, externalPrompt, onConfigClear }) => {
    const [history, setHistory] = useState([]);
    const [input, setInput] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const bottomRef = useRef(null);

    // Update parent with history whenever it changes
    useEffect(() => {
        if (onHistoryChange) onHistoryChange(history);
    }, [history, onHistoryChange]);

    // Handle External Prompts (from Drafting Board)
    useEffect(() => {
        if (externalPrompt) {
            handleSend(externalPrompt);
            // Clear the trigger in parent to avoid loops
            if (onConfigClear) onConfigClear();
        }
    }, [externalPrompt]);

    // Inject Project Context when loaded
    useEffect(() => {
        if (projectContext) {
            // Prepend a system message
            const contextMsg = { role: 'system', content: `[PROJECT SUMMARY LOADED]: ${projectContext}` };
            setHistory(prev => [...prev, contextMsg]);
        }
    }, [projectContext]);

    // Scroll to bottom on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history]);

    const handleSend = async (textOverride = null) => {
        const textToSend = textOverride || input;
        if (!textToSend.trim() || isGenerating) return;

        const userMsg = { role: 'user', content: textToSend };
        const newHistory = [...history, userMsg];

        setHistory(newHistory);
        setInput('');
        setIsGenerating(true);
        setMood('thinking'); // Set immediate "focused" state

        // Placeholder for IA message
        setHistory(prev => [...prev, { role: 'ia', content: '' }]);

        let currentResponse = '';

        await sendChat(
            userMsg.content,
            newHistory,
            (chunk) => {
                currentResponse += chunk;
                setHistory(prev => {
                    const updated = [...prev];
                    updated[updated.length - 1] = { role: 'ia', content: currentResponse };
                    return updated;
                });
            },
            (mood) => {
                // Immediate empathetic reaction to user input
                if (mood) setMood(mood);
            },
            () => {
                // onDone
                setIsGenerating(false);
                // Only reset to neutral if it was a specialized task
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

    const handleKeyDown = (e) => {
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
                updated[updated.length - 1].content += " [STOPPED]";
                return updated;
            });
        }
    };

    return (
        <div className="main-content">
            <div className="chat-history">
                {history.length === 0 && (
                    <div style={{ textAlign: 'center', color: '#555', marginTop: '100px' }}>
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
                    style={{ resize: 'none' }}
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
