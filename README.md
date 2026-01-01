# Luna - Author Edition 🖋️📖🕯️

Luna is a premium, minimalist creative writing suite powered by local AI. Designed for novelists and world-builders, it transforms the writing process into an interactive partnership where Lore and Plot are seamlessly integrated.

## 🚀 Key Features

### 🏛️ Workspace Management
- **One-Click Initialization**: Generate physical project folders with dedicated `World/` (Lore) and `Novel/` (Drafts) subdirectories automatically.
- **Physical Integration**: Projects aren't just metadata; they are folders on your disk. Edit paths, migrate files, or delete with full physical cleanup support.
- **Context Injection**: Load projects to instantly sync Luna's memory with your specific story world.

### 📁 Hierarchical Vault Explorer
- **Directory Tree**: Navigate your entire lore database with a modern, recursive file explorer.
- **Dynamic Creation**: Create new `.md` files directly within your folders (like `World/Places/`) from the sidebar.
- **Smart Refresh**: The vault dynamically updates based on the currently active project.

### ✍️ The Drafting Board
- **Book-Like Aesthetic**: A distraction-free writing environment using high-quality typography (Merriweather).
- **Markdown Preview**: Toggle between raw drafting and a beautifully rendered book-preview mode.
- **PR-Style Grammar Review**: (Unique ✨) Transform "Fix Grammar" into an interactive session. See word-level diffs in Red (removed), Green (added), and Yellow (fixes)—then Accept or Discard changes with one click.

### 🎭 Core Intelligence
- **Ollama Powered**: Runs 100% locally on your machine for total privacy.
- **Mood Analysis**: Luna's avatar reacts emotionally to your prose and conversation in real-time.
- **Analysis Tools**: Direct buttons in the editor for AI-driven Fact Checking and Grammar Polish.

---

## 🛠️ Setup Instructions

### Prerequisites
1. **Ollama**: Must be installed and running.
   - Install from [ollama.com](https://ollama.com).
   - Pull the model used (default `llama3.2`):
     ```bash
     ollama pull llama3.2
     ```
2. **Node.js**: For the React frontend.
3. **Python & uv**: For the backend logic.

### Installation

#### 1. Backend Setup
```bash
# Install dependencies and sync environment
uv sync

# Create .env from template
cp .env.template .env
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
```

### Running the Application

**Terminal 1 (Backend):**
```bash
uv run backend/app.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Visit **http://localhost:5173** to enter the Author Edition.

---

## 📖 Usage Workflow

1. **Create a Project**: Enter a name and a base path (e.g., `C:\Writing\MyNovel`). Luna will build your workspace.
2. **Build Your World**: Add lore files in the **World** folder via the Vault Explorer.
3. **Draft Your Story**: Select a file in **Novel** to open it on the Drafting Board.
4. **Collaborate with Luna**: Use the Chat for brainstorming or the **Fix Grammar** button for professional-grade editing with diffing.

---
*Created by Alexsem | Powered by Luna Author Suite*

