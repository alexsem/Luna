import React, { useState, useEffect, useRef } from 'react';
import { sendChat, stopGeneration } from '../api';

const ChatInterface = ({ setMood, onHistoryChange, projectContext }) => {
    const [history, setHistory] = useState([]);
    const [input, setInput] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const bottomRef = useRef(null);

    // Update parent with history whenever it changes
    useEffect(() => {
        if (onHistoryChange) onHistoryChange(history);
    }, [history, onHistoryChange]);

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

    const handleSend = async () => {
        if (!input.trim() || isGenerating) return;

        const userMsg = { role: 'user', content: input };
        const newHistory = [...history, userMsg];

        setHistory(newHistory);
        setInput('');
        setIsGenerating(true);

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
                setIsGenerating(false);
                if (mood) setMood(mood);
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
                        {msg.content}
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
                    <button className="btn" onClick={handleSend}>Send</button>
                )}
            </div>
        </div>
    );
};

export default ChatInterface;
