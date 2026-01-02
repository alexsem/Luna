import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import MoodDisplay from './components/MoodDisplay';
import ProjectManager from './components/ProjectManager';
import { checkHealth } from './api';
import VaultExplorer from './components/VaultExplorer';
import DraftingBoard from './components/DraftingBoard';
import './index.css';

function App() {
  const [mood, _setMood] = useState('neutral');
  const moodTimeoutRef = React.useRef(null);

  const setMood = (newMood, timeout = 0) => {
    if (moodTimeoutRef.current) {
      clearTimeout(moodTimeoutRef.current);
      moodTimeoutRef.current = null;
    }

    _setMood(newMood);

    if (timeout > 0) {
      moodTimeoutRef.current = setTimeout(() => {
        _setMood('neutral');
      }, timeout);
    }
  };

  const [status, setStatus] = useState('offline');
  const [currentHistory, setCurrentHistory] = useState([]);
  const [projectContext, setProjectContext] = useState('');
  const [activeProject, setActiveProject] = useState(null);

  // Sync State
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState({ current: 0, total: 100, file: '' });

  // Author Mode State
  const [activeFile, setActiveFile] = useState({ path: null, content: '' });
  const [externalPrompt, setExternalPrompt] = useState(null);
  const [saveStatus, setSaveStatus] = useState('');

  const [refreshVault, setRefreshVault] = useState(0); // Trigger for VaultExplorer

  useEffect(() => {
    // Initial health check
    checkHealth().then(res => {
      setStatus(res.status === 'online' ? 'online' : 'offline');
    });

    // Poll every 10s
    const interval = setInterval(() => {
      checkHealth().then(res => {
        setStatus(res.status === 'online' ? 'online' : 'offline');
      });
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleProjectLoaded = (name, summary, vaultPath) => {
    setActiveProject(name);
    setProjectContext(summary);
    if (vaultPath) {
      // Trigger VaultExplorer refresh
      setRefreshVault(prev => prev + 1);
    }
  };

  const handleSyncKnowledgeBase = async () => {
    if (syncing) return;
    setSyncing(true);
    setSyncProgress({ current: 0, total: 100, file: 'Starting...' });

    const { syncVault: apiSyncVault } = await import('./api');
    setMood('thinking');

    await apiSyncVault((data) => {
      if (data.status === 'progress') {
        setSyncProgress(prev => ({ ...prev, file: data.file, current: prev.current + 1 }));
      }
      if (data.status === 'done') {
        setSyncing(false);
        setRefreshVault(prev => prev + 1);
        setMood('neutral', 10000); // Wait 10s
        alert(`Knowledge Base Updated! Processed ${data.total} files.`);
      }
    });
    setSyncing(false);
    setMood('neutral', 10000);
  };

  const handleVaultFileLoaded = (filename, content, path) => {
    // INSTEAD of just context, we open it in the Editor
    setActiveFile({ path: path, content: content });
  };

  const handleDraftingAnalysis = (prompt) => {
    setExternalPrompt(prompt);
  };

  return (
    <div className="app-container">
      <div className="sidebar" style={{ display: 'flex', flexDirection: 'column' }}>
        <MoodDisplay mood={mood} status={status} />

        <ProjectManager
          history={currentHistory}
          activeProject={activeProject}
          setActiveProject={setActiveProject}
          onProjectLoaded={handleProjectLoaded}
        />

        <div className="divider"></div>

        <VaultExplorer
          onFileSelect={handleVaultFileLoaded}
          refreshTrigger={refreshVault}
          activeProject={activeProject}
          syncing={syncing}
          progress={syncProgress}
        />
      </div>

      {/* Main Content Area: Fixed Split View */}
      <div style={{ display: 'flex', width: '100%', height: '100%' }}>
        {/* Left: Editor */}
        <div style={{ flex: 1, borderRight: '1px solid #444', display: 'flex', flexDirection: 'column' }}>
          <DraftingBoard
            initialContent={activeFile.content}
            filePath={activeFile.path}
            onRequestAnalysis={handleDraftingAnalysis}
            onSaveStatus={setSaveStatus}
            onSyncKnowledgeBase={handleSyncKnowledgeBase}
            syncing={syncing}
          />
          <div style={{ padding: '5px 20px', fontSize: '0.8rem', color: '#888', borderTop: '1px solid #333' }}>
            {saveStatus}
          </div>
        </div>

        {/* Right: Chat */}
        <div style={{ flex: 1, maxWidth: '450px', display: 'flex', flexDirection: 'column' }}>
          <ChatInterface
            setMood={setMood}
            onHistoryChange={setCurrentHistory}
            projectContext={projectContext}
            externalPrompt={externalPrompt}
            onConfigClear={() => setExternalPrompt(null)}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
