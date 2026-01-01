import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import MoodDisplay from './components/MoodDisplay';
import ProjectManager from './components/ProjectManager';
import { checkHealth } from './api';
import VaultExplorer from './components/VaultExplorer';
import DraftingBoard from './components/DraftingBoard';
import './index.css';

function App() {
  const [mood, setMood] = useState('neutral');
  const [status, setStatus] = useState('offline');
  const [currentHistory, setCurrentHistory] = useState([]);
  const [projectContext, setProjectContext] = useState('');

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
    setProjectContext(summary);
    if (vaultPath) {
      // Trigger VaultExplorer refresh
      setRefreshVault(prev => prev + 1);
    }
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
          onProjectLoaded={handleProjectLoaded}
        />

        <div className="divider"></div>

        <VaultExplorer onFileSelect={handleVaultFileLoaded} refreshTrigger={refreshVault} />
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
