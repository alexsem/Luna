# Luna - Creative Writer Assistant

Luna is an advanced, dual-purpose AI companion designed to assist with creative writing. This application features a modern web interface with real-time mood analysis and project management capabilities.

## Features

### 🧠 Intelligent Conversationalist
- **Luna**: A persona designed to be creative, inspirational, and helpful.
- **Ollama Integration**: Powered by local LLMs (e.g., Llama 3) via Ollama.

### 🎭 Real-Time Mood Analysis
- **Emotional Awareness**: The application analyzes the sentiment of the conversation in real-time.
- **Visual Feedback**: Luna's avatar changes (Happy, Sad, Neutral) based on the context of the chat.

### 📁 Project Management
- **Save Contexts**: Save your current brainstorming session or story arc as a named project.
- **Summarization**: Automatically generates detailed summaries of your conversations to preserve context.
- **Context Injection**: Load a project to instantly give Luna the context of previous sessions.
- **Sidebar UI**: Easily manage your projects from the application sidebar.

### 💻 Modern Tech Stack
- **Frontend**: React + Vite (Dark Mode Aesthetic)
- **Backend**: Python (Flask) with `uv` dependency management
- **Communication**: Streaming responses for a fluid chat experience.

---

## Setup Instructions

### Prerequisites
1. **Ollama**: Must be installed and running.
   - Install from [ollama.com](https://ollama.com).
   - Pull the model used (default `llama3.2` or configurable in `.env`):
     ```bash
     ollama pull llama3.2
     ```
2. **Node.js**: For the frontend.
3. **Python & uv**: For the backend.

### Installation

#### 1. Backend Setup
Navigate to the root directory and install dependencies using `uv`:

```bash
# Install dependencies and sync environment
uv sync
```

# Create a .env file from the template and modify as needed
cp .env.template .env
```

### `.env.template` Example
```ini
# Example .env file - copy this to .env and modify as needed
OLLAMA_URL=http://localhost:11434/api/generate
MODEL=llama3.2
APP_LANG=ENG
MAX_HISTORY_MESSAGES=10
BACKEND_PORT=5000
FRONTEND_PORT=5173
```

#### 2. Frontend Setup
Navigate to the `frontend` directory and install dependencies:

```bash
cd frontend
npm install
```

### Running the Application

You need to run both the backend and frontend servers.

**Terminal 1 (Backend):**
```bash
# From root directory
uv run backend/app.py
```
*Backend runs on http://localhost:5000*

**Terminal 2 (Frontend):**
```bash
# From frontend directory
cd frontend
npm run dev
```
*Frontend runs on http://localhost:5173*

Open your browser to **http://localhost:5173** to start chatting with Luna!

---

## Usage - Luna: Your Creative Writer Assistant

1. **Start Chatting**: Type in the main chat box.
2. **Watch the Mood**: Luna's face updates when she replies.
3. **Manage Projects**:
   - **Create**: Enter a name in the Sidebar input and click `+`.
   - **Load**: Click a project name to inject its summary into the current chat.
   - **Delete**: Click the `x` next to a project to remove it.

## License
[MIT License](LICENSE)
