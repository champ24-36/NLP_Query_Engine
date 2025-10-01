#!/bin/bash

#Setup Script

set -e  # Exit on error

echo "=========================================="
echo "NLP Query Engine - Setup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check Python version
echo ""
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python version: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Node.js version
echo ""
echo "Checking Node.js version..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js version: $NODE_VERSION"
else
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
print_status "Python dependencies installed"
cd ..

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install
print_status "Frontend dependencies installed"
cd ..

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p sample_data/documents
print_status "Directories created"

# Copy environment file
echo ""
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Environment file created (.env)"
    print_warning "Please update .env with your database credentials"
else
    print_warning ".env file already exists"
fi

# Download embedding model (optional, will download on first use)
echo ""
echo "Preparing embedding model..."
python3 << EOF
try:
    from sentence_transformers import SentenceTransformer
    print("Testing sentence transformers...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("Embedding model ready!")
except Exception as e:
    print(f"Note: Embedding model will be downloaded on first use: {e}")
EOF

# Check Docker
echo ""
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_status "Docker version: $DOCKER_VERSION"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_status "Docker Compose version: $COMPOSE_VERSION"
    fi
else
    print_warning "Docker is not installed. Docker is optional but recommended."
fi

# Check PostgreSQL (optional)
echo ""
echo "Checking PostgreSQL installation..."
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version)
    print_status "PostgreSQL version: $PSQL_VERSION"
else
    print_warning "PostgreSQL client not found. You can use Docker or remote database."
fi

# Run tests
echo ""
read -p "Do you want to run tests now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    cd backend
    pytest tests/ -v --tb=short
    cd ..
fi

# Setup complete
echo ""
echo "=========================================="
print_status "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your database connection"
echo "2. Start the backend: cd backend && uvicorn main:app --reload"
echo "3. Start the frontend: cd frontend && npm run dev"
echo "4. Or use Docker: docker-compose up --build"
echo ""
echo "Access the application:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "For more information, see README.md"
echo ""
