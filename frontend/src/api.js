
const PORT = typeof __BACKEND_PORT__ !== 'undefined' ? __BACKEND_PORT__ : 5000;
const API_URL = `http://localhost:${PORT}`;


/**
 * Checks the health of the backend and Ollama.
 * @returns {Promise<{status: string, ollama: string}>}
 */
export const checkHealth = async () => {
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
 * @param {string} prompt - The user's message.
 * @param {Array} history - The chat history.
 * @param {Function} onChunk - Callback for each text chunk received.
 * @param {Function} onDone - Callback when generation is complete (returns final mood).
 * @param {Function} onError - Callback for errors.
 * @returns {AbortController} - Controller to abort the fetch if needed.
 */
export const sendChat = (prompt, history, onChunk, onDone, onError) => {
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

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Handle multiple JSON objects in one chunk or split across chunks
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep the last incomplete line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (data.type === 'chunk') {
                        onChunk(data.content);
                    } else if (data.type === 'done') {
                        onDone(data.mood);
                    } else if (data.type === 'error') {
                        onError(data.content);
                    } else if (data.type === 'stop') {
                        // Handled conceptually as done, but maybe we want to know it was stopped
                        onDone(null);
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

export const stopGeneration = async () => {
    try {
        await fetch(`${API_URL}/stop`, { method: 'POST' });
    } catch (e) {
        console.error("Failed to stop", e);
    }
};

export const getProjects = async () => {
    const res = await fetch(`${API_URL}/projects`);
    return await res.json();
};

export const createProject = async (name, history) => {
    const res = await fetch(`${API_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, history })
    });
    return await res.json();
};

export const deleteProject = async (name) => {
    const res = await fetch(`${API_URL}/projects/${name}`, {
        method: 'DELETE'
    });
    return await res.json();
};

export const loadProject = async (name) => {
    const res = await fetch(`${API_URL}/projects/${name}/load`, {
        method: 'POST'
    });
    return await res.json();
};
