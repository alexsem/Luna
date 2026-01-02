import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import * as Diff from 'diff';
import { saveVaultFile, fixGrammar } from '../api';

interface DraftingBoardProps {
    onRequestAnalysis: (prompt: string) => void;
    initialContent: string;
    filePath: string | null;
    onSaveStatus: (status: string) => void;
    onSyncKnowledgeBase: () => void;
    syncing: boolean;
}

const DraftingBoard: React.FC<DraftingBoardProps> = ({
    onRequestAnalysis,
    initialContent,
    filePath,
    onSaveStatus,
    onSyncKnowledgeBase,
    syncing
}) => {
    const [draft, setDraft] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [previewMode, setPreviewMode] = useState(false);

    // Review Mode State
    const [isReviewing, setIsReviewing] = useState(false);
    const [, setOriginalDraft] = useState('');
    const [diffResult, setDiffResult] = useState<Diff.Change[]>([]);
    const [correctedText, setCorrectedText] = useState('');
    const [loadingReview, setLoadingReview] = useState(false);

    // Load content when file changes
    useEffect(() => {
        setDraft(initialContent || '');
        setPreviewMode(false);
        setIsReviewing(false); // Reset review on file change
    }, [initialContent, filePath]);

    const handleAction = async (type: 'grammar' | 'fact_check') => {
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

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            handleSave();
        }
    };

    return (
        <div className="drafting-board">
            <div className="drafting-toolbar">
                <div className="toolbar-left">
                    <span className="file-path">{filePath ? filePath : "Untitled Draft"}</span>

                    {!isReviewing && (
                        <div className="mode-selector">
                            <button onClick={() => setPreviewMode(false)} className={`mode-btn ${!previewMode ? 'active' : ''}`}>WRITE</button>
                            <button onClick={() => setPreviewMode(true)} className={`mode-btn ${previewMode ? 'active' : ''}`}>PREVIEW</button>
                        </div>
                    )}
                </div>

                <div className="toolbar-right">
                    {isReviewing ? (
                        <>
                            <button className="btn btn-sm btn-success" onClick={handleAccept}>✔️ Apply All</button>
                            <button className="btn btn-sm btn-secondary" onClick={handleDiscard}>✖️ Discard</button>
                        </>
                    ) : (
                        <>
                            <button
                                className="btn btn-sm btn-primary"
                                onClick={onSyncKnowledgeBase}
                                disabled={syncing}
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

            <div className="editor-container">
                {isReviewing ? (
                    <div className="review-diff-view">
                        {diffResult.map((part, index) => {
                            let className = '';
                            if (part.added) className = 'diff-added';
                            else if (part.removed) className = 'diff-removed';

                            return (
                                <span key={index} className={className}>
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
                                placeholder="Select a file from the Vault to start writing..."
                                value={draft}
                                onChange={(e) => setDraft(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        ) : (
                            <div className="markdown-preview">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{draft}</ReactMarkdown>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default DraftingBoard;
