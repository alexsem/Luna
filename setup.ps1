# LUNA Author Edition - Setup Script for Windows (PowerShell)
# This script installs backend dependencies, frontend packages, and pulls required AI models.

Write-Host "🖋️📖🕯️ Initializing LUNA Author Edition Setup..." -ForegroundColor Cyan

# 1. Check for Prerequisites
$prereqs = @{
    "uv"     = "uv --version"
    "node"   = "node --version"
    "docker" = "docker --version"
}

foreach ($item in $prereqs.GetEnumerator()) {
    try {
        Invoke-Expression $item.Value | Out-Null
    } catch {
        Write-Warning "Missing prerequisite: $($item.Key). Please install it before proceeding."
        exit 1
    }
}

# 2. Setup Backend
Write-Host "`n🐍 Setting up Python Backend..." -ForegroundColor Green
if (Test-Path ".env.template") {
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.template" ".env"
        Write-Host "Created .env from template." -ForegroundColor Gray
    }
}
uv sync

# 3. Setup Frontend
Write-Host "`n⚛️ Setting up React Frontend..." -ForegroundColor Green
Set-Location frontend
npm install
Set-Location ..

# 4. Pull AI Models
Write-Host "`n🤖 Pulling Ollama Models (Llama 3.2 & Nomic Embed)..." -ForegroundColor Green
ollama pull llama3.2
ollama pull nomic-embed-text

# 5. Start Infrastructure
Write-Host "`n🐳 Starting ChromaDB via Docker..." -ForegroundColor Green
docker-compose up -d

Write-Host "`n✨ Setup Complete! ✨" -ForegroundColor Cyan
Write-Host "To run LUNA:"
Write-Host "Terminal 1: uv run backend/app.py"
Write-Host "Terminal 2: cd frontend; npm run dev"
