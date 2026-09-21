#!/bin/bash

# Quick setup script for local development

echo "🎓 Setting up InvestLab for local development..."

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }

echo "✅ All required tools are installed"

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your BOT_TOKEN and WEBAPP_URL"
    echo "   Get BOT_TOKEN from https://t.me/botfather"
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Next steps:"
echo ""
echo "1. Edit .env file:"
echo "   - Get BOT_TOKEN from @BotFather"
echo "   - Set WEBAPP_URL (for local dev: http://localhost:5173)"
echo "   - Generate API_SECRET_KEY: openssl rand -hex 32"
echo ""
echo "2. Start backend services:"
echo "   docker-compose up -d"
echo ""
echo "3. Start frontend dev server:"
echo "   cd frontend && npm run dev"
echo ""
echo "4. Open bot in Telegram and send /start"
echo ""
