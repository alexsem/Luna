import React, { useState, useEffect } from 'react';
import { getProjects, createProject, deleteProject, loadProject, updateProject } from '../api';

const ProjectManager = ({ history, onProjectLoaded, activeProject, setActiveProject }) => {
    const [projects, setProjects] = useState([]);
    const [newProjectName, setNewProjectName] = useState('');
    const [projectDescription, setProjectDescription] = useState('');
    const [vaultPath, setVaultPath] = useState('');
    const [loading, setLoading] = useState(false);

    // UI state for menus and editing
    const [menuOpen, setMenuOpen] = useState(null); // name of the project whose menu is open
    const [editingProject, setEditingProject] = useState(null); // { name, path, description }

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'

    useEffect(() => {
        fetchProjects();
        fetchCurrentConfig();
    }, []);

    const fetchCurrentConfig = async () => {
        const { getConfig } = await import('../api');
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
        // trigger_init: true tells backend to create the subfolders
        const res = await createProject(newProjectName, history, { vault_path: vaultPath }, true, projectDescription);
        setLoading(false);
        if (res.status === 'created') {
            setNewProjectName('');
            setProjectDescription('');
            setShowModal(false);
            fetchProjects();
            setActiveProject(newProjectName);
        }
    };

    const handleDelete = async (name, deleteFiles) => {
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
            description: editingProject.description
        });
        setEditingProject(null);
        setShowModal(false);
        fetchProjects();
    };

    const handleSelect = async (name) => {
        setLoading(true);
        const res = await loadProject(name);
        setLoading(false);
        if (res) {
            setActiveProject(name);
            const vp = res.config?.vault_path;
            const desc = res.description || res.summary || '';
            onProjectLoaded(name, desc, vp);
        }
    };

    const openCreateModal = () => {
        setModalMode('create');
        setShowModal(true);
    };

    const openEditModal = async (name) => {
        const proj = await loadProject(name);
        setEditingProject({ name, path: proj.config.vault_path, description: proj.description });
        setModalMode('edit');
        setShowModal(true);
        setMenuOpen(null);
    };

    return (
        <div className="project-manager" style={{ width: '100%', marginTop: '20px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #444' }}>
                <h3 style={{ color: '#aaa', fontSize: '0.8rem', paddingBottom: '5px', margin: 0, letterSpacing: '1px' }}>PROJECTS</h3>
                <button
                    onClick={openCreateModal}
                    title="New Project"
                    style={{ background: 'transparent', border: 'none', color: '#bb86fc', cursor: 'pointer', fontSize: '1.2rem', padding: '0 5px' }}
                >
                    +
                </button>
            </div>

            <div className="project-list" style={{ marginBottom: '10px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {projects.length === 0 && <div style={{ color: '#666', fontSize: '0.8rem', fontStyle: 'italic', padding: '5px' }}>No projects found</div>}
                {projects.map(name => (
                    <div key={name} style={{ position: 'relative' }}>
                        <div
                            className={`project-item ${activeProject === name ? 'active' : ''}`}
                            onClick={() => handleSelect(name)}
                            style={{
                                padding: '10px',
                                borderRadius: '4px',
                                background: activeProject === name ? '#3700b3' : '#2c2c2c',
                                cursor: 'pointer',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                fontSize: '0.9rem',
                                border: '1px solid #444',
                                color: '#fff',
                                transition: 'all 0.2s ease'
                            }}
                        >
                            <span style={{ fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
                            <button
                                onClick={(e) => { e.stopPropagation(); setMenuOpen(menuOpen === name ? null : name); }}
                                style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', padding: '5px', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', outline: 'none' }}
                                className="options-trigger"
                            >
                                ⋮
                            </button>
                        </div>

                        {/* Context Menu */}
                        {menuOpen === name && (
                            <div style={{
                                position: 'absolute',
                                right: 0,
                                top: 'calc(100% + 5px)',
                                zIndex: 100,
                                background: '#2d2d2d',
                                border: '1px solid #555',
                                borderRadius: '6px',
                                padding: '4px',
                                minWidth: '160px',
                                boxShadow: '0 8px 16px rgba(0,0,0,0.6)'
                            }}>
                                <button className="menu-btn" onClick={() => openEditModal(name)}>✏️ Edit Project</button>
                                <button className="menu-btn" style={{ color: '#cf6679' }} onClick={() => handleDelete(name, false)}>🗑️ Delete Metadata</button>
                                <button className="menu-btn" style={{ color: '#ff4d4d', fontWeight: 'bold' }} onClick={() => handleDelete(name, true)}>🔥 Delete Everything</button>
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
                            <button onClick={() => setShowModal(false)} style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1.2rem' }}>&times;</button>
                        </div>

                        {modalMode === 'create' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '10px 0' }}>
                                <div className="form-group">
                                    <label style={{ fontSize: '0.8rem', color: '#888', display: 'block', marginBottom: '5px' }}>Project Name</label>
                                    <input
                                        type="text"
                                        className="input-dark"
                                        placeholder="Arkeia, Red Mars, etc."
                                        value={newProjectName}
                                        onChange={(e) => setNewProjectName(e.target.value)}
                                        style={{ margin: 0 }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label style={{ fontSize: '0.8rem', color: '#888', display: 'block', marginBottom: '5px' }}>Workspace Path (Absolute)</label>
                                    <input
                                        type="text"
                                        className="input-dark"
                                        placeholder="C:\Users\Name\Documents\Novel"
                                        value={vaultPath}
                                        onChange={(e) => setVaultPath(e.target.value)}
                                        style={{ margin: 0 }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label style={{ fontSize: '0.8rem', color: '#888', display: 'block', marginBottom: '5px' }}>Project Description / Lore Summary</label>
                                    <textarea
                                        className="input-dark"
                                        placeholder="A story about..."
                                        value={projectDescription}
                                        onChange={(e) => setProjectDescription(e.target.value)}
                                        rows={4}
                                        style={{ margin: 0, resize: 'none' }}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '10px 0' }}>
                                <div className="form-group">
                                    <label style={{ fontSize: '0.8rem', color: '#888', display: 'block', marginBottom: '5px' }}>Workspace Path (Absolute)</label>
                                    <input
                                        className="input-dark"
                                        value={editingProject.path}
                                        onChange={e => setEditingProject({ ...editingProject, path: e.target.value })}
                                        style={{ margin: 0 }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label style={{ fontSize: '0.8rem', color: '#888', display: 'block', marginBottom: '5px' }}>Project Description</label>
                                    <textarea
                                        className="input-dark"
                                        value={editingProject.description}
                                        onChange={e => setEditingProject({ ...editingProject, description: e.target.value })}
                                        rows={6}
                                        style={{ margin: 0, resize: 'none' }}
                                    />
                                </div>
                            </div>
                        )}

                        <div className="modal-footer">
                            <button className="btn" onClick={() => setShowModal(false)} style={{ background: '#444', color: '#fff' }}>Cancel</button>
                            <button
                                className="btn"
                                onClick={modalMode === 'create' ? handleCreate : handleUpdatePath}
                                disabled={loading}
                            >
                                {loading ? 'Saving...' : 'Save Project'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                .menu-btn { width: 100%; text-align: left; padding: 10px; background: transparent; border: none; color: #ccc; cursor: pointer; border-radius: 4px; font-size: 0.8rem; }
                .menu-btn:hover { background: #333; color: white; }
                .input-dark { width: 100%; background: #222; border: 1px solid #444; color: white; padding: 10px; border-radius: 6px; font-size: 0.9rem; outline: none; transition: border-color 0.2s; }
                .input-dark:focus { border-color: var(--primary-color); }
                .project-item:hover { transform: translateX(2px); }
                .options-trigger:hover { background: rgba(255, 255, 255, 0.1); color: white !important; }
            `}</style>
        </div>
    );
};

export default ProjectManager;
