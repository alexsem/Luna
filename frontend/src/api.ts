import { HealthResponse, ChatMessage, SyncData, ProjectMeta, ProjectConfig } from './types';

declare const __BACKEND_PORT__: number;
const PORT = typeof __BACKEND_PORT__ !== 'undefined' ? __BACKEND_PORT__ : 5000;
const API_URL = `http://localhost:${PORT}`;

/**
 * Checks the health of the backend and Ollama.
 */
export const checkHealth = async (): Promise<HealthResponse> => {
    try {
        const response = await fetch(`${API_URL}/health`);
        return await response.json();
    } catch (error) {
        console.error("Health check failed:", error);
        return { status: "offline", ollama: "unknown" };
    }
};

/**
 * Sends a chat message and handles the streaming response.
 */
export const sendChat = (
    prompt: string,
    history: ChatMessage[],
    onChunk: (chunk: string) => void,
    onMood: (mood: string) => void,
    onDone: () => void,
    onError: (error: string) => void
): AbortController => {
    const controller = new AbortController();

    fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, history }),
        signal: controller.signal
    }).then(async (response) => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) throw new Error("Response body is null");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (data.type === 'chunk') {
                        onChunk(data.content);
                    } else if (data.type === 'mood') {
                        if (onMood) onMood(data.content);
                    } else if (data.type === 'done') {
                        onDone();
                    } else if (data.type === 'error') {
                        onError(data.content);
                    } else if (data.type === 'stop') {
                        onDone();
                    }
                } catch (e) {
                    console.error("JSON parse error", e, line);
                }
            }
        }
    }).catch(err => {
        if (err.name === 'AbortError') {
            console.log("Fetch aborted");
        } else {
            onError(err.message);
        }
    });

    return controller;
};

export const stopGeneration = async (): Promise<void> => {
    try {
        await fetch(`${API_URL}/stop`, { method: 'POST' });
    } catch (e) {
        console.error("Failed to stop", e);
    }
};

export const getProjects = async (): Promise<string[]> => {
    const res = await fetch(`${API_URL}/projects`);
    return await res.json();
};

export const createProject = async (name: string, history: ChatMessage[], config: ProjectConfig = {}): Promise<any> => {
    const res = await fetch(`${API_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, history, config })
    });
    return await res.json();
};

export const deleteProject = async (name: string, deleteFiles = false): Promise<any> => {
    const res = await fetch(`${API_URL}/projects/${name}${deleteFiles ? '?delete_files=true' : ''}`, {
        method: 'DELETE'
    });
    return await res.json();
};

export const updateProject = async (name: string, config: ProjectConfig, history: ChatMessage[] = []): Promise<any> => {
    const res = await fetch(`${API_URL}/projects/${name}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config, history })
    });
    return await res.json();
};

export const loadProject = async (name: string): Promise<ProjectMeta> => {
    const res = await fetch(`${API_URL}/projects/${name}/load`, {
        method: 'POST'
    });
    return await res.json();
};

export const getVaultFiles = async (): Promise<any[]> => {
    const res = await fetch(`${API_URL}/vault/files`);
    if (!res.ok) {
        throw new Error("Failed to fetch vault files");
    }
    return await res.json();
};

export const readVaultFile = async (path: string): Promise<{ content?: string; error?: string }> => {
    try {
        const response = await fetch(`${API_URL}/vault/read`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "Failed to read file");
        }
        return await response.json();
    } catch (error: any) {
        console.error("Vault Read Error:", error);
        return { error: error.message };
    }
};

export const saveVaultFile = async (path: string, content: string): Promise<any> => {
    try {
        const response = await fetch(`${API_URL}/vault/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, content })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to save file');
        }
        return await response.json();
    } catch (error) {
        console.error("Save Error:", error);
        throw error;
    }
};

export const syncVault = async (onProgress?: (data: SyncData) => void): Promise<any> => {
    try {
        const response = await fetch(`${API_URL}/vault/sync`, {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error("Failed to start sync");
        }

        if (!response.body) throw new Error("Sync response body is null");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (onProgress) onProgress(data);
                } catch (e) {
                    console.error("Error parsing sync chunk:", e);
                }
            }
        }
        return { status: "done" };

    } catch (error: any) {
        console.error("Vault Sync Error:", error);
        return { error: error.message };
    }
};

export const getConfig = async (): Promise<any> => {
    const res = await fetch(`${API_URL}/config`);
    return await res.json();
};

export const saveConfig = async (vault_path: string): Promise<any> => {
    const res = await fetch(`${API_URL}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vault_path })
    });
    return await res.json();
};

export const createVaultFile = async (path: string): Promise<any> => {
    const res = await fetch(`${API_URL}/vault/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
    });
    return await res.json();
};

export const fixGrammar = async (content: string): Promise<{ fixed?: string; original?: string; error?: string }> => {
    const res = await fetch(`${API_URL}/vault/fix-grammar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    });
    return await res.json();
};
