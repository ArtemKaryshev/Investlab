#!/bin/bash

# Development helper commands for InvestLab

case "$1" in
  start)
    echo "🚀 Starting InvestLab..."
    docker-compose up -d
    echo "✅ Services started"
    echo "📍 Bot: check logs with 'docker-compose logs -f bot'"
    echo "📍 API: http://localhost:8000"
    ;;
  
  stop)
    echo "⏸️  Stopping InvestLab..."
    docker-compose down
    echo "✅ Services stopped"
    ;;
  
  restart)
    echo "🔄 Restarting InvestLab..."
    docker-compose restart
    echo "✅ Services restarted"
    ;;
  
  logs)
    service=${2:-bot}
    echo "📋 Showing logs for $service..."
    docker-compose logs -f $service
    ;;
  
  build)
    echo "🔨 Building services..."
    docker-compose build
    echo "✅ Build complete"
    ;;
  
  clean)
    echo "🧹 Cleaning up..."
    docker-compose down -v
    echo "✅ Cleaned up containers and volumes"
    ;;
  
  db)
    echo "🗄️  Connecting to database..."
    docker-compose exec postgres psql -U investlab investlab
    ;;
  
  redis)
    echo "🔴 Connecting to Redis..."
    docker-compose exec redis redis-cli
    ;;
  
  test)
    echo "🧪 Running tests..."
    cd backend && pytest tests/ -v
    ;;
  
  frontend)
    echo "🎨 Starting frontend dev server..."
    cd frontend && npm run dev
    ;;
  
  *)
    echo "InvestLab Development Helper"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start      - Start all services"
    echo "  stop       - Stop all services"
    echo "  restart    - Restart all services"
    echo "  logs [svc] - Show logs (default: bot)"
    echo "  build      - Rebuild containers"
    echo "  clean      - Remove containers and volumes"
    echo "  db         - Connect to PostgreSQL"
    echo "  redis      - Connect to Redis"
    echo "  test       - Run backend tests"
    echo "  frontend   - Start frontend dev server"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh start"
    echo "  ./dev.sh logs api"
    echo "  ./dev.sh frontend"
    ;;
esac
