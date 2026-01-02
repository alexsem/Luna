import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { checkHealth } from './api';
import { HealthResponse, Mood } from './types';

interface AppContextType {
    status: 'online' | 'offline';
    mood: Mood;
    setMood: (newMood: Mood, timeout?: number) => void;
    activeProject: string | null;
    setActiveProject: (name: string | null) => void;
    projectContext: string;
    setProjectContext: (context: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [status, setStatus] = useState<'online' | 'offline'>('offline');
    const [mood, _setMood] = useState<Mood>('neutral');
    const [activeProject, setActiveProject] = useState<string | null>(null);
    const [projectContext, setProjectContext] = useState<string>('');
    const moodTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

    const setMood = (newMood: Mood, timeout: number = 0) => {
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

    useEffect(() => {
        const pollHealth = async () => {
            const res = await checkHealth();
            setStatus(res.status === 'online' ? 'online' : 'offline');
        };

        pollHealth();
        const interval = setInterval(pollHealth, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <AppContext.Provider value={{
            status,
            mood,
            setMood,
            activeProject,
            setActiveProject,
            projectContext,
            setProjectContext
        }}>
            {children}
        </AppContext.Provider>
    );
};

export const useAppContext = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useAppContext must be used within an AppProvider');
    }
    return context;
};
