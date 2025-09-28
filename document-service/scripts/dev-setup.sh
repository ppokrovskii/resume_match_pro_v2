#!/bin/bash
# Development Environment Setup Script for Document Service

set -e

echo "🚀 Setting up Document Service development environment..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Start core services (postgres, azurite)
echo "🐳 Starting core development services..."
docker-compose up -d postgres azurite

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
echo "   - PostgreSQL..."
docker-compose exec postgres pg_isready -U postgres -d resumematch || {
    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 10
    docker-compose exec postgres pg_isready -U postgres -d resumematch
}

echo "   - Azurite (Azure Storage Emulator)..."
sleep 5

echo "✅ Core services are ready!"

# Display service information
echo ""
echo "🎯 Development services running:"
echo "   📊 PostgreSQL:     localhost:5432"
echo "   📦 Azurite Blob:   localhost:10000"
echo ""
echo "📝 Next steps:"
echo "   1. Copy env.example to .env and configure"
echo "   2. Run database migrations: uv run alembic upgrade head"
echo "   3. Start the API: uv run python main.py"
echo ""
echo "💡 Note: Database schema is managed by Alembic migrations, not init scripts"
echo ""
echo "🛑 To stop services: docker-compose down"
echo "🗑️  To reset data: docker-compose down -v"
