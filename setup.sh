#!/bin/bash

# LUNA Author Edition - Setup Script for Linux/macOS
# This script installs backend dependencies, frontend packages, and pulls required AI models.

set -e # Exit on error

echo "🖋️📖🕯️ Initializing LUNA Author Edition Setup..."

# 1. Check for Prerequisites
command -v uv >/dev/null 2>&1 || { echo >&2 "Missing prerequisite: uv. Please install it."; exit 1; }
command -v node >/dev/null 2>&1 || { echo >&2 "Missing prerequisite: node. Please install it."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "Missing prerequisite: docker-compose. Please install it."; exit 1; }

# 2. Setup Backend
echo -e "\n🐍 Setting up Python Backend..."
if [ -f .env.template ] && [ ! -f .env ]; then
    cp .env.template .env
    echo "Created .env from template."
fi
uv sync

# 3. Setup Frontend
echo -e "\n⚛️ Setting up React Frontend..."
cd frontend
npm install
cd ..

# 4. Pull AI Models
echo -e "\n🤖 Pulling Ollama Models (Llama 3.2 & Nomic Embed)..."
ollama pull llama3.2
ollama pull nomic-embed-text

# 5. Start Infrastructure
echo -e "\n🐳 Starting ChromaDB via Docker..."
docker-compose up -d

echo -e "\n✨ Setup Complete! ✨"
echo "To run LUNA:"
echo "Terminal 1: uv run backend/app.py"
echo "Terminal 2: cd frontend && npm run dev"
