import React, { useState, useEffect } from 'react';
import { getProjects, createProject, deleteProject, loadProject, updateProject } from '../api';

const ProjectManager = ({ history, onProjectLoaded }) => {
    const [projects, setProjects] = useState([]);
    const [newProjectName, setNewProjectName] = useState('');
    const [vaultPath, setVaultPath] = useState('');
    const [activeProject, setActiveProject] = useState(null);
    const [loading, setLoading] = useState(false);

    // UI state for menus and editing
    const [menuOpen, setMenuOpen] = useState(null); // name of the project whose menu is open
    const [editingProject, setEditingProject] = useState(null); // { name, path }

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
        const res = await createProject(newProjectName, history, { vault_path: vaultPath }, true);
        setLoading(false);
        if (res.status === 'created') {
            setNewProjectName('');
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
        await updateProject(editingProject.name, { vault_path: editingProject.path });
        setEditingProject(null);
        fetchProjects();
    };

    const handleSelect = async (name) => {
        setLoading(true);
        const res = await loadProject(name);
        setLoading(false);
        if (res.summary) {
            setActiveProject(name);
            const vp = res.config?.vault_path;
            onProjectLoaded(name, res.summary, vp);
        }
    };

    return (
        <div className="project-manager" style={{ width: '100%', marginTop: '20px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <h3 style={{ color: '#aaa', fontSize: '0.9rem', borderBottom: '1px solid #444', paddingBottom: '5px' }}>PROJECTS</h3>

            <div className="project-list" style={{ flex: 1, overflowY: 'auto', maxHeight: '300px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {projects.map(name => (
                    <div key={name} style={{ position: 'relative' }}>
                        <div
                            className={`project-item ${activeProject === name ? 'active' : ''}`}
                            onClick={() => handleSelect(name)}
                            style={{
                                padding: '8px',
                                borderRadius: '4px',
                                background: activeProject === name ? '#3700b3' : '#2c2c2c',
                                cursor: 'pointer',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                fontSize: '0.9rem'
                            }}
                        >
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
                            <button
                                onClick={(e) => { e.stopPropagation(); setMenuOpen(menuOpen === name ? null : name); }}
                                style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', padding: '0 5px' }}
                            >
                                ⋮
                            </button>
                        </div>

                        {/* Context Menu */}
                        {menuOpen === name && (
                            <div style={{ position: 'absolute', right: 0, top: '100%', zIndex: 10, background: '#1E1E1E', border: '1px solid #444', borderRadius: '4px', padding: '5px', minWidth: '150px', boxShadow: '0 2px 10px rgba(0,0,0,0.5)' }}>
                                <button className="menu-btn" onClick={() => { setEditingProject({ name, path: '' }); setMenuOpen(null); }}>✏️ Edit Project</button>
                                <button className="menu-btn" style={{ color: '#cf6679' }} onClick={() => handleDelete(name, false)}>🗑️ Delete Metadata</button>
                                <button className="menu-btn" style={{ color: '#ff4d4d', fontWeight: 'bold' }} onClick={() => handleDelete(name, true)}>🔥 Delete Everything</button>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Edit Modal / Inline */}
            {editingProject && (
                <div style={{ padding: '10px', background: '#333', borderRadius: '4px', fontSize: '0.8rem' }}>
                    <strong>Edit {editingProject.name} Path:</strong>
                    <input
                        className="input-dark"
                        value={editingProject.path}
                        onChange={e => setEditingProject({ ...editingProject, path: e.target.value })}
                        placeholder="Absolute Path"
                    />
                    <div style={{ display: 'flex', gap: '5px', marginTop: '5px' }}>
                        <button className="btn-sm" onClick={handleUpdatePath}>Save</button>
                        <button className="btn-sm" onClick={() => setEditingProject(null)}>Cancel</button>
                    </div>
                </div>
            )}

            <div className="new-project" style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginTop: '10px' }}>
                <div style={{ display: 'flex', gap: '5px' }}>
                    <input
                        type="text"
                        placeholder="Project Name"
                        value={newProjectName}
                        onChange={(e) => setNewProjectName(e.target.value)}
                        style={{ flex: 1, background: '#222', border: '1px solid #444', color: 'white', padding: '5px', borderRadius: '4px', fontSize: '0.8rem' }}
                    />
                    <button onClick={handleCreate} disabled={loading} style={{ background: '#bb86fc', border: 'none', borderRadius: '4px', padding: '5px 10px', cursor: 'pointer', fontWeight: 'bold', opacity: loading ? 0.5 : 1 }}>
                        {loading ? '...' : '+'}
                    </button>
                </div>
                <input
                    type="text"
                    placeholder="Base Workspace Path"
                    value={vaultPath}
                    onChange={(e) => setVaultPath(e.target.value)}
                    style={{ background: '#222', border: '1px solid #444', color: '#888', padding: '4px', borderRadius: '4px', fontSize: '0.7rem' }}
                />
            </div>

            <style>{`
                .menu-btn { width: 100%; text-align: left; padding: 8px; background: transparent; border: none; color: #ccc; cursor: pointer; border-radius: 4px; font-size: 0.8rem; }
                .menu-btn:hover { background: #333; color: white; }
                .input-dark { width: 100%; background: #222; border: 1px solid #444; color: white; padding: 5px; border-radius: 4px; margin-top: 5px; }
            `}</style>
        </div>
    );
};

export default ProjectManager;
