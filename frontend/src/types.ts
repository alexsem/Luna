export interface ProjectMeta {
    description: string;
    summary: string;
    config: ProjectConfig;
}

export interface ProjectConfig {
    vault_path?: string;
    [key: string]: any;
}

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface SyncData {
    status: 'progress' | 'done';
    file?: string;
    current?: number;
    total?: number;
}

export interface HealthResponse {
    status: 'online' | 'offline';
    ollama: string;
}

export interface TreeNode {
    name: string;
    type: 'file' | 'directory';
    path: string;
    children?: TreeNode[];
}

export type Mood = 'neutral' | 'happy' | 'thinking' | 'sad' | 'surprised' | 'angry' | 'scared';
