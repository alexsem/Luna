import React, { useState, useEffect } from 'react';
import { getVaultFiles, readVaultFile, syncVault, getConfig, saveConfig, createVaultFile } from '../api';

const FileNode = ({ node, onFileSelect, onRefresh }) => {
    const [isOpen, setIsOpen] = useState(node.name === 'World' || node.name === 'Novel'); // Open main folders by default
    const [isCreating, setIsCreating] = useState(false);
    const [newFileName, setNewFileName] = useState('');

    const toggleCreate = (e) => {
        e.stopPropagation();
        setIsCreating(!isCreating);
        if (!isOpen) setIsOpen(true); // Auto-open folder when creating
    };

    const handleCreate = async (e) => {
        e.stopPropagation();
        if (!newFileName) return;
        const res = await createVaultFile(`${node.path}/${newFileName}`);
        if (res.status === 'created') {
            setNewFileName('');
            setIsCreating(false);
            onRefresh();
        } else {
            alert(res.error || "Failed to create file");
        }
    };

    if (node.type === 'file') {
        return (
            <div className="file-item" onClick={() => onFileSelect(node)} title={node.path}>
                <span className="file-icon">📄</span>
                <span className="file-name">{node.name}</span>
            </div>
        );
    }

    return (
        <div className="folder-node">
            <div className="folder-item" onClick={() => setIsOpen(!isOpen)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span className="folder-icon">{isOpen ? '📂' : '📁'}</span>
                    <span className="folder-name" style={{ fontWeight: 'bold' }}>{node.name}</span>
                </div>
                <button
                    className="btn-plus"
                    onClick={(e) => { e.stopPropagation(); setIsCreating(!isCreating); }}
                    title="New File"
                >
                    +
                </button>
            </div>

            {isCreating && (
                <div className="new-file-input" style={{ marginLeft: '20px', padding: '5px' }}>
                    <input
                        type="text"
                        autoFocus
                        placeholder="file name..."
                        value={newFileName}
                        onChange={e => setNewFileName(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleCreate(e)}
                        style={{ width: '80%', background: '#222', border: '1px solid #444', color: 'white', fontSize: '0.8rem', padding: '2px' }}
                    />
                </div>
            )}

            {isOpen && (
                <div className="folder-children" style={{ marginLeft: '15px', borderLeft: '1px solid #333', paddingLeft: '5px' }}>
                    {node.children && node.children.length > 0 ? (
                        node.children.map((child, idx) => (
                            <FileNode key={idx} node={child} onFileSelect={onFileSelect} onRefresh={onRefresh} />
                        ))
                    ) : (
                        <div style={{ padding: '4px', fontSize: '0.75rem', color: '#666', fontStyle: 'italic' }}>
                            (Empty Folder)
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const VaultExplorer = ({ onFileSelect, refreshTrigger, activeProject }) => {
    const [filesTree, setFilesTree] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [progress, setProgress] = useState({ current: 0, total: 100, file: '' });

    const [vaultPath, setVaultPath] = useState('');
    const [isEditingPath, setIsEditingPath] = useState(false);

    const loadFiles = async () => {
        if (!activeProject) {
            setFilesTree([]);
            return;
        }
        setLoading(true);
        setError('');
        try {
            const cfg = await getConfig();
            if (cfg.vault_path) setVaultPath(cfg.vault_path);

            const tree = await getVaultFiles();
            setFilesTree(tree);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSavePath = async () => {
        try {
            await saveConfig(vaultPath);
            setIsEditingPath(false);
            loadFiles();
        } catch (err) {
            alert("Failed to save config");
        }
    };

    const handleFileClick = async (node) => {
        try {
            const data = await readVaultFile(node.path);
            if (data.content !== undefined) {
                onFileSelect(node.name, data.content, node.path);
            }
        } catch (err) {
            console.error(err);
            alert("Failed to read file");
        }
    };

    useEffect(() => {
        loadFiles();
    }, [refreshTrigger, activeProject]);

    if (!activeProject) {
        return (
            <div className="vault-explorer" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '200px', opacity: 0.6 }}>
                <div style={{ fontSize: '2rem', marginBottom: '10px' }}>📖</div>
                <div style={{ textAlign: 'center', fontSize: '0.85rem', color: '#aaa', lineHeight: '1.4' }}>
                    Select a project to explore<br />the library.
                </div>
            </div>
        );
    }

    return (
        <div className="vault-explorer">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h3 style={{ margin: 0 }}>Vault / Library</h3>
                <button className="btn-sm" onClick={() => setIsEditingPath(!isEditingPath)}>⚙️</button>
            </div>

            {isEditingPath && (
                <div style={{ marginBottom: '10px', padding: '10px', background: '#333', borderRadius: '4px' }}>
                    <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '5px', color: '#ccc' }}>Vault Location:</label>
                    <div style={{ display: 'flex', gap: '5px' }}>
                        <input
                            type="text"
                            value={vaultPath}
                            onChange={(e) => setVaultPath(e.target.value)}
                            style={{ flex: 1, padding: '4px', borderRadius: '4px', border: '1px solid #555', background: '#222', color: 'white' }}
                        />
                        <button className="btn-sm" onClick={handleSavePath}>Save</button>
                    </div>
                </div>
            )}

            <div style={{ display: 'flex', gap: '5px', marginBottom: '10px' }}>
                <button className="btn-sm" onClick={loadFiles}>Refresh</button>
            </div>

            {syncing && (
                <div className="sync-status">
                    <span className="loader">Syncing... {progress.file ? `(${progress.file})` : ''}</span>
                    <progress value={progress.current || 0} max={progress.total || 100} className="progress-bar"></progress>
                </div>
            )}

            {loading && <div className="loader">Loading...</div>}
            {error && <div className="error-msg">{error}</div>}

            <div className="file-list">
                {filesTree.length === 0 && !loading && <span className="empty-msg">No files found.</span>}
                {filesTree.map((node, idx) => (
                    <FileNode key={idx} node={node} onFileSelect={handleFileClick} onRefresh={loadFiles} />
                ))}
            </div>

            <style>{`
                .folder-item { padding: 4px; cursor: pointer; border-radius: 4px; transition: background 0.2s; }
                .folder-item:hover { background: #333; }
                .btn-plus { background: transparent; border: none; color: #888; cursor: pointer; padding: 0 8px; font-weight: bold; border-radius: 4px; }
                .btn-plus:hover { background: #444; color: #bb86fc; }
                .folder-children { padding-top: 2px; }
            `}</style>
        </div >
    );
};

export default VaultExplorer;
