import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import * as Diff from 'diff';
import { saveVaultFile, fixGrammar } from '../api';

const DraftingBoard = ({ onRequestAnalysis, initialContent, filePath, onSaveStatus, onSyncKnowledgeBase, syncing }) => {
    const [draft, setDraft] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [previewMode, setPreviewMode] = useState(false);

    // Review Mode State
    const [isReviewing, setIsReviewing] = useState(false);
    const [originalDraft, setOriginalDraft] = useState('');
    const [diffResult, setDiffResult] = useState([]);
    const [correctedText, setCorrectedText] = useState('');
    const [loadingReview, setLoadingReview] = useState(false);

    // Load content when file changes
    useEffect(() => {
        setDraft(initialContent || '');
        setPreviewMode(false);
        setIsReviewing(false); // Reset review on file change
    }, [initialContent, filePath]);

    const handleAction = async (type) => {
        if (!draft.trim()) return;

        if (type === 'grammar') {
            setLoadingReview(true);
            try {
                const res = await fixGrammar(draft);
                if (res.fixed) {
                    setOriginalDraft(draft);
                    setCorrectedText(res.fixed);
                    const diff = Diff.diffWords(draft, res.fixed);
                    setDiffResult(diff);
                    setIsReviewing(true);
                }
            } catch (err) {
                alert("Failed to get grammar suggestions.");
            } finally {
                setLoadingReview(false);
            }
        } else {
            // Fact check still uses chat
            let prefix = "";
            if (type === 'fact_check') prefix = "#task:fact_check\n\n";
            onRequestAnalysis(`${prefix}${draft}`);
        }
    };

    const handleAccept = () => {
        setDraft(correctedText);
        setIsReviewing(false);
    };

    const handleDiscard = () => {
        setIsReviewing(false);
    };

    const handleSave = async () => {
        if (!filePath) return;
        setIsSaving(true);
        if (onSaveStatus) onSaveStatus('Saving...');

        try {
            await saveVaultFile(filePath, draft);
            if (onSaveStatus) onSaveStatus('Saved');
            setTimeout(() => onSaveStatus(''), 2000);
        } catch (error) {
            console.error(error);
            if (onSaveStatus) onSaveStatus('Error saving');
        } finally {
            setIsSaving(false);
        }
    };

    const handleKeyDown = (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            handleSave();
        }
    };

    return (
        <div className="drafting-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '20px', gap: '10px' }}>

            {/* Header / Toolbar */}
            <div className="drafting-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#252526', padding: '10px', borderRadius: '5px' }}>
                <div style={{ fontWeight: 'bold', color: '#ccc', display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <span>{filePath ? filePath : "Untitled Draft"}</span>

                    {!isReviewing && (
                        <div style={{ display: 'flex', background: '#111', borderRadius: '4px', overflow: 'hidden', border: '1px solid #444' }}>
                            <button onClick={() => setPreviewMode(false)} className={`mode-toggle-btn ${!previewMode ? 'active' : ''}`}>WRITE</button>
                            <button onClick={() => setPreviewMode(true)} className={`mode-toggle-btn ${previewMode ? 'active' : ''}`}>PREVIEW</button>
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                    {isReviewing ? (
                        <>
                            <button className="btn btn-sm" onClick={handleAccept} style={{ background: '#03dac6', color: '#000' }}>✔️ Apply All</button>
                            <button className="btn btn-sm" onClick={handleDiscard} style={{ background: '#666' }}>✖️ Discard</button>
                        </>
                    ) : (
                        <>
                            <button
                                className="btn btn-sm"
                                onClick={onSyncKnowledgeBase}
                                disabled={syncing}
                                style={{ background: syncing ? '#444' : '#6200ee', color: '#fff' }}
                            >
                                🔄 {syncing ? 'Updating...' : 'Update Knowledge Base'}
                            </button>
                            <button className="btn btn-sm" onClick={() => handleAction('fact_check')}>🔍 Fact Check</button>
                            <button className="btn btn-sm" onClick={() => handleAction('grammar')} disabled={loadingReview}>
                                {loadingReview ? '...' : '✨ Fix Grammar'}
                            </button>
                            <button className="btn" onClick={handleSave} disabled={!filePath || isSaving}>
                                {isSaving ? "Saving..." : "💾 Save"}
                            </button>
                        </>
                    )}
                </div>
            </div>

            <div className="editor-wrapper" style={{ flex: 1, position: 'relative', minHeight: 0 }}>
                {isReviewing ? (
                    <div
                        className="review-diff-view"
                        style={{
                            width: '100%',
                            height: '100%',
                            backgroundColor: '#1E1E1E',
                            color: '#E0E0E0',
                            border: '1px solid #bb86fc', // Highlight review mode
                            borderRadius: '5px',
                            padding: '20px',
                            overflowY: 'auto',
                            fontFamily: "'Merriweather', 'Georgia', serif",
                            lineHeight: '1.6',
                            whiteSpace: 'pre-wrap',
                            fontSize: '16px'
                        }}
                    >
                        {diffResult.map((part, index) => {
                            let color = 'transparent';
                            let textDecoration = 'none';

                            if (part.added) {
                                color = 'rgba(0, 255, 0, 0.2)'; // Green for addition
                            } else if (part.removed) {
                                color = 'rgba(255, 0, 0, 0.2)'; // Red for removal
                                textDecoration = 'line-through';
                            } else if (part.count < 3 && !part.added && !part.removed) {
                                // Suboptimal yellow heuristic: if a part is tiny and unchanged, 
                                // but we could also detect if it's sandwiched between add/remove.
                                // For simplicity/clarity, let's stick to PR colors primarily.
                            }

                            return (
                                <span
                                    key={index}
                                    style={{
                                        backgroundColor: color,
                                        textDecoration: textDecoration,
                                        borderRadius: '2px'
                                    }}
                                >
                                    {part.value}
                                </span>
                            );
                        })}
                    </div>
                ) : (
                    <>
                        {!previewMode ? (
                            <textarea
                                className="drafting-editor"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    backgroundColor: '#1E1E1E',
                                    color: '#E0E0E0',
                                    border: '1px solid #333',
                                    borderRadius: '5px',
                                    padding: '20px',
                                    fontSize: '16px',
                                    fontFamily: "'Merriweather', 'Georgia', serif",
                                    lineHeight: '1.6',
                                    resize: 'none',
                                    outline: 'none'
                                }}
                                placeholder="Select a file from the Vault to start writing..."
                                value={draft}
                                onChange={(e) => setDraft(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        ) : (
                            <div
                                className="markdown-preview"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    backgroundColor: '#1E1E1E',
                                    color: '#E0E0E0',
                                    border: '1px solid #333',
                                    borderRadius: '5px',
                                    padding: '30px',
                                    overflowY: 'auto',
                                    fontFamily: "'Merriweather', 'Georgia', serif",
                                    lineHeight: '1.8'
                                }}
                            >
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{draft}</ReactMarkdown>
                            </div>
                        )}
                    </>
                )}
            </div>

            <style>{`
                .mode-toggle-btn {
                    padding: 4px 12px;
                    border: none;
                    background: transparent;
                    color: #888;
                    cursor: pointer;
                    fontSize: 0.75rem;
                    fontWeight: bold;
                    transition: all 0.2s;
                }
                .mode-toggle-btn.active {
                    background: #bb86fc;
                    color: #000;
                }
            `}</style>
        </div>
    );
};

export default DraftingBoard;
