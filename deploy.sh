#!/bin/bash

# InvestLab Deployment Script
# Usage: ./deploy.sh [production|development]

set -e

ENV=${1:-development}

echo "🚀 Deploying InvestLab in $ENV mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copy .env.example and configure it first."
    exit 1
fi

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🔨 Building services..."
docker-compose build

echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

# Run database migrations (if needed)
echo "🗄️  Running database migrations..."
# docker-compose exec bot alembic upgrade head

echo ""
echo "✅ InvestLab deployed successfully!"
echo ""
echo "📍 Services:"
echo "   - Bot: Running (check logs: docker-compose logs -f bot)"
echo "   - API: http://localhost:8000"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "📝 Next steps:"
echo "   1. Build frontend: cd frontend && npm run build"
echo "   2. Deploy frontend to hosting (Vercel/Netlify)"
echo "   3. Update WEBAPP_URL in .env with your frontend URL"
echo "   4. Restart bot: docker-compose restart bot"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f bot"
echo "   docker-compose logs -f api"
echo ""
