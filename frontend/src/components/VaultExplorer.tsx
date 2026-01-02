import React, { useState, useEffect } from 'react';
import { getVaultFiles, readVaultFile, getConfig, saveConfig, createVaultFile } from '../api';
import { TreeNode, SyncData } from '../types';

interface FileNodeProps {
    node: TreeNode;
    onFileSelect: (node: TreeNode) => void;
    onRefresh: () => void;
}

const FileNode: React.FC<FileNodeProps> = ({ node, onFileSelect, onRefresh }) => {
    const [isOpen, setIsOpen] = useState(node.name === 'World' || node.name === 'Novel'); // Open main folders by default
    const [isCreating, setIsCreating] = useState(false);
    const [newFileName, setNewFileName] = useState('');

    const toggleCreate = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsCreating(!isCreating);
        if (!isOpen) setIsOpen(true); // Auto-open folder when creating
    };

    const handleCreate = async (e: React.FormEvent | React.KeyboardEvent) => {
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
            <div className="folder-item" onClick={() => setIsOpen(!isOpen)}>
                <div className="folder-info">
                    <span className="folder-icon">{isOpen ? '📂' : '📁'}</span>
                    <span className="folder-name">{node.name}</span>
                </div>
                <button
                    className="btn-plus"
                    onClick={toggleCreate}
                    title="New File"
                >
                    +
                </button>
            </div>

            {isCreating && (
                <div className="new-file-input">
                    <input
                        type="text"
                        autoFocus
                        placeholder="file name..."
                        value={newFileName}
                        onChange={e => setNewFileName(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleCreate(e)}
                    />
                </div>
            )}

            {isOpen && (
                <div className="folder-children">
                    {node.children && node.children.length > 0 ? (
                        node.children.map((child, idx) => (
                            <FileNode key={idx} node={child} onFileSelect={onFileSelect} onRefresh={onRefresh} />
                        ))
                    ) : (
                        <div className="empty-folder-msg">
                            (Empty Folder)
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

interface VaultExplorerProps {
    onFileSelect: (name: string, content: string, path: string) => void;
    refreshTrigger: number;
    activeProject: string | null;
    syncing: boolean;
    progress: SyncData;
}

const VaultExplorer: React.FC<VaultExplorerProps> = ({
    onFileSelect,
    refreshTrigger,
    activeProject,
    syncing,
    progress
}) => {
    const [filesTree, setFilesTree] = useState<TreeNode[]>([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

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
        } catch (err: any) {
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

    const handleFileClick = async (node: TreeNode) => {
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
            <div className="vault-explorer empty">
                <div className="empty-icon">📖</div>
                <div className="empty-text">
                    Select a project to explore<br />the library.
                </div>
            </div>
        );
    }

    return (
        <div className="vault-explorer">
            <div className="vault-header">
                <h3>Vault / Library</h3>
                <button className="btn-sm" onClick={() => setIsEditingPath(!isEditingPath)}>⚙️</button>
            </div>

            {isEditingPath && (
                <div className="path-editor">
                    <label>Vault Location:</label>
                    <div className="path-input-group">
                        <input
                            type="text"
                            value={vaultPath}
                            onChange={(e) => setVaultPath(e.target.value)}
                        />
                        <button className="btn-sm" onClick={handleSavePath}>Save</button>
                    </div>
                </div>
            )}

            <div className="vault-toolbar">
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
        </div >
    );
};

export default VaultExplorer;
