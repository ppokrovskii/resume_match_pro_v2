@echo off
REM Development Environment Setup Script for Document Service (Windows)

echo 🚀 Setting up Document Service development environment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not available. Please ensure Docker Desktop is running.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Start core services
echo 🐳 Starting core development services...
docker-compose up -d postgres azurite

REM Wait for services
echo ⏳ Waiting for services to be ready...
echo    - PostgreSQL...
timeout /t 10 /nobreak >nul
docker-compose exec postgres pg_isready -U postgres -d resumematch

echo    - Azurite (Azure Storage Emulator)...
timeout /t 5 /nobreak >nul

echo ✅ Core services are ready!

REM Display service information
echo.
echo 🎯 Development services running:
echo    📊 PostgreSQL:     localhost:5432
echo    📦 Azurite Blob:   localhost:10000
echo.
echo 📝 Next steps:
echo    1. Copy env.example to .env and configure
echo    2. Run database migrations: uv run alembic upgrade head
echo    3. Start the API: uv run python main.py
echo.
echo 💡 Note: Database schema is managed by Alembic migrations, not init scripts
echo.
echo 🛑 To stop services: docker-compose down
echo 🗑️  To reset data: docker-compose down -v

pause
