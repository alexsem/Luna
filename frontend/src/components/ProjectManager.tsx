import React, { useState, useEffect } from 'react';
import { getProjects, createProject, deleteProject, loadProject, updateProject, getConfig } from '../api';
import { useAppContext } from '../AppContext';
import { ChatMessage, ProjectConfig } from '../types';

interface ProjectManagerProps {
    history: ChatMessage[];
    onProjectLoaded: (name: string, summary: string, vaultPath?: string) => void;
}

interface EditingProject {
    name: string;
    path: string;
    description: string;
}

const ProjectManager: React.FC<ProjectManagerProps> = ({ history, onProjectLoaded }) => {
    const { activeProject, setActiveProject } = useAppContext();
    const [projects, setProjects] = useState<string[]>([]);
    const [newProjectName, setNewProjectName] = useState('');
    const [projectDescription, setProjectDescription] = useState('');
    const [vaultPath, setVaultPath] = useState('');
    const [loading, setLoading] = useState(false);

    // UI state for menus and editing
    const [menuOpen, setMenuOpen] = useState<string | null>(null); // name of the project whose menu is open
    const [editingProject, setEditingProject] = useState<EditingProject | null>(null);

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');

    useEffect(() => {
        fetchProjects();
        fetchCurrentConfig();
    }, []);

    const fetchCurrentConfig = async () => {
        const cfg = await getConfig();
        if (cfg.vault_path) setVaultPath(cfg.vault_path);
    };

    const fetchProjects = async () => {
        const list = await getProjects();
        setProjects(list);
    };

    const handleCreate = async () => {
        if (!newProjectName.trim()) return;
        setLoading(true);
        const config: ProjectConfig = { vault_path: vaultPath };
        const res = await createProject(newProjectName, history, config);
        setLoading(false);
        if (res.status === 'created') {
            setNewProjectName('');
            setProjectDescription('');
            setShowModal(false);
            fetchProjects();
            setActiveProject(newProjectName);
        }
    };

    const handleDelete = async (name: string, deleteFiles: boolean) => {
        const msg = deleteFiles
            ? `WARNING: This will delete ALL files in ${name}'s folder. Are you absolutely sure?`
            : `Delete metadata for "${name}"? (Your files will remain untouched)`;

        if (window.confirm(msg)) {
            await deleteProject(name, deleteFiles);
            if (activeProject === name) setActiveProject(null);
            fetchProjects();
        }
        setMenuOpen(null);
    };

    const handleUpdatePath = async () => {
        if (!editingProject) return;
        await updateProject(editingProject.name, {
            vault_path: editingProject.path,
        }, []); // History update could be added here if needed
        setEditingProject(null);
        setShowModal(false);
        fetchProjects();
    };

    const handleSelect = async (name: string) => {
        setLoading(true);
        const res = await loadProject(name);
        setLoading(false);
        if (res) {
            setActiveProject(name);
            const vp = res.config?.vault_path;
            const desc = res.summary || '';
            onProjectLoaded(name, desc, vp);
        }
    };

    const openCreateModal = () => {
        setModalMode('create');
        setShowModal(true);
    };

    const openEditModal = async (name: string) => {
        const proj = await loadProject(name);
        setEditingProject({
            name,
            path: proj.config?.vault_path || '',
            description: proj.summary || ''
        });
        setModalMode('edit');
        setShowModal(true);
        setMenuOpen(null);
    };

    return (
        <div className="project-manager">
            <div className="pm-header">
                <h3>PROJECTS</h3>
                <button
                    onClick={openCreateModal}
                    title="New Project"
                    className="btn-plus-pm"
                >
                    +
                </button>
            </div>

            <div className="project-list">
                {projects.length === 0 && <div className="empty-projects">No projects found</div>}
                {projects.map(name => (
                    <div key={name} className="project-item-container">
                        <div
                            className={`project-item ${activeProject === name ? 'active' : ''}`}
                            onClick={() => handleSelect(name)}
                        >
                            <span className="project-name">{name}</span>
                            <button
                                onClick={(e) => { e.stopPropagation(); setMenuOpen(menuOpen === name ? null : name); }}
                                className="options-trigger"
                            >
                                ⋮
                            </button>
                        </div>

                        {/* Context Menu */}
                        {menuOpen === name && (
                            <div className="pm-context-menu">
                                <button className="menu-btn" onClick={() => openEditModal(name)}>✏️ Edit Project</button>
                                <button className="menu-btn danger" onClick={() => handleDelete(name, false)}>🗑️ Delete Metadata</button>
                                <button className="menu-btn critical" onClick={() => handleDelete(name, true)}>🔥 Delete Everything</button>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Project Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{modalMode === 'create' ? '✨ New Project' : `✏️ Edit ${editingProject?.name}`}</h2>
                            <button onClick={() => setShowModal(false)} className="close-btn">&times;</button>
                        </div>

                        {modalMode === 'create' ? (
                            <div className="modal-body">
                                <div className="form-group">
                                    <label>Project Name</label>
                                    <input
                                        type="text"
                                        className="input-dark"
                                        placeholder="Arkeia, Red Mars, etc."
                                        value={newProjectName}
                                        onChange={(e) => setNewProjectName(e.target.value)}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Workspace Path (Absolute)</label>
                                    <input
                                        type="text"
                                        className="input-dark"
                                        placeholder="C:\Users\Name\Documents\Novel"
                                        value={vaultPath}
                                        onChange={(e) => setVaultPath(e.target.value)}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Project Description / Lore Summary</label>
                                    <textarea
                                        className="input-dark"
                                        placeholder="A story about..."
                                        value={projectDescription}
                                        onChange={(e) => setProjectDescription(e.target.value)}
                                        rows={4}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="modal-body">
                                <div className="form-group">
                                    <label>Workspace Path (Absolute)</label>
                                    <input
                                        className="input-dark"
                                        value={editingProject?.path || ''}
                                        onChange={e => editingProject && setEditingProject({ ...editingProject, path: e.target.value })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Project Description</label>
                                    <textarea
                                        className="input-dark"
                                        value={editingProject?.description || ''}
                                        onChange={e => editingProject && setEditingProject({ ...editingProject, description: e.target.value })}
                                        rows={6}
                                    />
                                </div>
                            </div>
                        )}

                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                            <button
                                className="btn btn-primary"
                                onClick={modalMode === 'create' ? handleCreate : handleUpdatePath}
                                disabled={loading}
                            >
                                {loading ? 'Saving...' : 'Save Project'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProjectManager;
