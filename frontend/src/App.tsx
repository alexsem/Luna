import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import MoodDisplay from './components/MoodDisplay';
import ProjectManager from './components/ProjectManager';
import VaultExplorer from './components/VaultExplorer';
import DraftingBoard from './components/DraftingBoard';
import { useAppContext } from './AppContext';
import { ChatMessage, SyncData } from './types';
import { syncVault as apiSyncVault } from './api';
import './index.css';

const App: React.FC = () => {
  const {
    mood, setMood,
    status,
    activeProject, setActiveProject,
    projectContext, setProjectContext
  } = useAppContext();

  const [currentHistory, setCurrentHistory] = useState<ChatMessage[]>([]);

  // Sync State
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState<SyncData>({ status: 'done', current: 0, total: 100, file: '' });

  // Author Mode State
  const [activeFile, setActiveFile] = useState<{ path: string | null; content: string }>({ path: null, content: '' });
  const [externalPrompt, setExternalPrompt] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState('');

  const [refreshVault, setRefreshVault] = useState(0); // Trigger for VaultExplorer

  const handleProjectLoaded = (name: string, summary: string, vaultPath?: string) => {
    setActiveProject(name);
    setProjectContext(summary);
    if (vaultPath) {
      setRefreshVault(prev => prev + 1);
    }
  };

  const handleSyncKnowledgeBase = async () => {
    if (syncing) return;
    setSyncing(true);
    setSyncProgress({ status: 'progress', current: 0, total: 100, file: 'Starting...' });

    setMood('thinking');

    const res = await apiSyncVault((data: SyncData) => {
      if (data.status === 'progress') {
        setSyncProgress(prev => ({ ...prev, file: data.file, current: (prev.current || 0) + 1 }));
      }
      if (data.status === 'done') {
        setSyncing(false);
        setRefreshVault(prev => prev + 1);
        setMood('neutral', 10000);
        alert(`Knowledge Base Updated! Processed ${data.total} files.`);
      }
    });

    if (res.error) {
      alert(`Sync Error: ${res.error}`);
    }

    setSyncing(false);
    setMood('neutral', 10000);
  };

  const handleVaultFileLoaded = (filename: string, content: string, path: string) => {
    setActiveFile({ path: path, content: content });
  };

  const handleDraftingAnalysis = (prompt: string) => {
    setExternalPrompt(prompt);
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <MoodDisplay />

        <ProjectManager
          history={currentHistory}
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

      <div className="main-content">
        {/* Left: Editor */}
        <div className="editor-section">
          <DraftingBoard
            initialContent={activeFile.content}
            filePath={activeFile.path}
            onRequestAnalysis={handleDraftingAnalysis}
            onSaveStatus={setSaveStatus}
            onSyncKnowledgeBase={handleSyncKnowledgeBase}
            syncing={syncing}
          />
          <div className="status-bar">
            {saveStatus}
          </div>
        </div>

        {/* Right: Chat */}
        <div className="chat-section">
          <ChatInterface
            onHistoryChange={setCurrentHistory}
            externalPrompt={externalPrompt}
            onConfigClear={() => setExternalPrompt(null)}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
