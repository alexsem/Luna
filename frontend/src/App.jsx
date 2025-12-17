import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import MoodDisplay from './components/MoodDisplay';
import ProjectManager from './components/ProjectManager';
import { checkHealth } from './api';
import './index.css';

function App() {
  const [mood, setMood] = useState('neutral');
  const [status, setStatus] = useState('offline');
  const [currentHistory, setCurrentHistory] = useState([]);
  const [projectContext, setProjectContext] = useState('');

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

  const handleProjectLoaded = (name, summary) => {
    setProjectContext(summary);
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <MoodDisplay mood={mood} status={status} />
        <ProjectManager
          history={currentHistory}
          onProjectLoaded={handleProjectLoaded}
        />
      </div>
      <ChatInterface
        setMood={setMood}
        onHistoryChange={setCurrentHistory}
        projectContext={projectContext}
      />
    </div>
  );
}

export default App;
