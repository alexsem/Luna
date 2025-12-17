import React, { useState, useEffect } from 'react';
import { getProjects, createProject, deleteProject, loadProject } from '../api';

const ProjectManager = ({ history, onProjectLoaded }) => {
    const [projects, setProjects] = useState([]);
    const [newProjectName, setNewProjectName] = useState('');
    const [activeProject, setActiveProject] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        const list = await getProjects();
        setProjects(list);
    };

    const handleCreate = async () => {
        if (!newProjectName.trim()) return;
        setLoading(true);
        // history prop comes from App/ChatInterface? 
        // Actually we need the history to summarize.
        // We should probably get history from a prop or context.
        const res = await createProject(newProjectName, history);
        setLoading(false);
        if (res.status === 'created') {
            setNewProjectName('');
            fetchProjects();
            setActiveProject(newProjectName);
        }
    };

    const handleDelete = async (name, e) => {
        e.stopPropagation();
        if (window.confirm(`Delete project "${name}"?`)) {
            await deleteProject(name);
            if (activeProject === name) setActiveProject(null);
            fetchProjects();
        }
    };

    const handleSelect = async (name) => {
        setLoading(true);
        const res = await loadProject(name);
        setLoading(false);
        if (res.summary) {
            setActiveProject(name);
            onProjectLoaded(name, res.summary);
        }
    };

    return (
        <div className="project-manager" style={{ width: '100%', marginTop: '20px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <h3 style={{ color: '#aaa', fontSize: '0.9rem', borderBottom: '1px solid #444', paddingBottom: '5px' }}>PROJECTS</h3>

            <div className="project-list" style={{ flex: 1, overflowY: 'auto', maxHeight: '300px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {projects.map(name => (
                    <div
                        key={name}
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
                            onClick={(e) => handleDelete(name, e)}
                            style={{ background: 'transparent', border: 'none', color: '#cf6679', cursor: 'pointer', padding: '0 5px', fontSize: '1.2rem' }}
                        >
                            &times;
                        </button>
                    </div>
                ))}
                {projects.length === 0 && <div style={{ color: '#666', fontSize: '0.8rem', fontStyle: 'italic' }}>No projects saved.</div>}
            </div>

            <div className="new-project" style={{ display: 'flex', gap: '5px', marginTop: '10px' }}>
                <input
                    type="text"
                    placeholder="New Project Name"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    style={{
                        flex: 1,
                        background: '#222',
                        border: '1px solid #444',
                        color: 'white',
                        padding: '5px',
                        borderRadius: '4px',
                        fontSize: '0.8rem'
                    }}
                />
                <button
                    onClick={handleCreate}
                    disabled={loading}
                    style={{
                        background: '#bb86fc',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '5px 10px',
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        opacity: loading ? 0.5 : 1
                    }}
                >
                    {loading ? '...' : '+'}
                </button>
            </div>
        </div>
    );
};

export default ProjectManager;
