#!/bin/bash

# =============================================================================
# TikTok Viral Signal Detector - Setup Script
# =============================================================================
# This script automates the complete environment setup process
# Usage: bash setup.sh
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
echo "============================================================================="
echo "  TikTok Viral Signal Detector - Environment Setup"
echo "============================================================================="
echo ""

# =============================================================================
# 1. Check Prerequisites
# =============================================================================
log_info "Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    log_error "Python $REQUIRED_VERSION+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

log_success "Python $PYTHON_VERSION detected"

# Check for PostgreSQL
if ! command -v psql &> /dev/null; then
    log_warning "PostgreSQL not found. You'll need to install it manually."
    log_info "Installation instructions:"
    log_info "  - Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    log_info "  - macOS: brew install postgresql"
    log_info "  - Or use Docker: docker run --name tiktok-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres"
else
    log_success "PostgreSQL detected"
fi

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    log_warning "FFmpeg not found. Required for video processing."
    log_info "Installation instructions:"
    log_info "  - Ubuntu/Debian: sudo apt-get install ffmpeg"
    log_info "  - macOS: brew install ffmpeg"
else
    log_success "FFmpeg detected"
fi

# Check for Tesseract (for OCR)
if ! command -v tesseract &> /dev/null; then
    log_warning "Tesseract OCR not found. Required for text detection."
    log_info "Installation instructions:"
    log_info "  - Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    log_info "  - macOS: brew install tesseract"
else
    log_success "Tesseract detected"
fi

echo ""

# =============================================================================
# 2. Create Virtual Environment
# =============================================================================
log_info "Creating Python virtual environment..."

VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    log_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv $VENV_DIR
    log_success "Virtual environment created"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source $VENV_DIR/bin/activate
log_success "Virtual environment activated"

echo ""

# =============================================================================
# 3. Upgrade pip and install build tools
# =============================================================================
log_info "Upgrading pip and installing build tools..."
pip install --upgrade pip setuptools wheel
log_success "Build tools updated"

echo ""

# =============================================================================
# 4. Install Python dependencies
# =============================================================================
log_info "Installing Python dependencies (this may take several minutes)..."
pip install -r requirements.txt
log_success "Python dependencies installed"

echo ""

# =============================================================================
# 5. Install Playwright browsers
# =============================================================================
log_info "Installing Playwright browsers..."
playwright install chromium
log_success "Playwright browsers installed"

echo ""

# =============================================================================
# 6. Download spaCy language model
# =============================================================================
log_info "Downloading spaCy English language model..."
python -m spacy download en_core_web_sm
log_success "spaCy model downloaded"

echo ""

# =============================================================================
# 7. Create project directory structure
# =============================================================================
log_info "Creating project directory structure..."

# Create directories
mkdir -p config
mkdir -p agents
mkdir -p orchestration
mkdir -p models
mkdir -p utils
mkdir -p notebooks
mkdir -p data/raw
mkdir -p data/processed/embeddings
mkdir -p data/processed/transcripts
mkdir -p data/models
mkdir -p scripts
mkdir -p tests
mkdir -p app/pages
mkdir -p docs
mkdir -p logs

# Create __init__.py files for Python packages
touch config/__init__.py
touch agents/__init__.py
touch orchestration/__init__.py
touch models/__init__.py
touch utils/__init__.py
touch tests/__init__.py

log_success "Directory structure created"

echo ""

# =============================================================================
# 8. Setup environment variables
# =============================================================================
log_info "Setting up environment variables..."

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        log_success ".env file created from template"
        log_warning "IMPORTANT: Edit .env file with your actual credentials"
    else
        log_warning ".env.example not found. Skipping .env creation."
    fi
else
    log_warning ".env file already exists. Skipping."
fi

echo ""

# =============================================================================
# 9. Initialize PostgreSQL Database
# =============================================================================
log_info "Initializing PostgreSQL database..."

# Check if PostgreSQL is running
if command -v psql &> /dev/null; then
    # Load database configuration from .env if it exists
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi

    # Default values
    DB_NAME=${DB_NAME:-tiktok_viral_detector}
    DB_USER=${DB_USER:-postgres}
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}

    log_info "Database: $DB_NAME"
    log_info "User: $DB_USER"
    log_info "Host: $DB_HOST:$DB_PORT"

    # Check if we can connect to PostgreSQL
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME 2>/dev/null; then
        log_warning "Database '$DB_NAME' already exists."
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Dropping existing database..."
            dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME 2>/dev/null || true
            log_info "Creating database..."
            createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME

            if [ -f scripts/init_database.sql ]; then
                log_info "Running database schema initialization..."
                psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f scripts/init_database.sql
                log_success "Database schema initialized"
            fi
        else
            log_info "Keeping existing database"
        fi
    else
        log_info "Creating database '$DB_NAME'..."
        createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME 2>/dev/null || {
            log_error "Failed to create database. Make sure PostgreSQL is running and credentials are correct."
            log_info "You can create it manually: createdb -U $DB_USER $DB_NAME"
        }

        if [ -f scripts/init_database.sql ]; then
            log_info "Running database schema initialization..."
            psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f scripts/init_database.sql
            log_success "Database schema initialized"
        fi
    fi
else
    log_warning "PostgreSQL not installed. Skipping database initialization."
    log_info "Install PostgreSQL and run: psql -U postgres -d tiktok_viral_detector -f scripts/init_database.sql"
fi

echo ""

# =============================================================================
# 10. Create ChromaDB directory
# =============================================================================
log_info "Setting up ChromaDB storage..."
mkdir -p data/chromadb
log_success "ChromaDB directory created"

echo ""

# =============================================================================
# 11. Verify Installation
# =============================================================================
log_info "Verifying installation..."

# Test imports
python3 << END
import sys
try:
    # Core dependencies
    import TikTokApi
    import playwright
    import yt_dlp

    # ML/AI
    import sklearn
    import xgboost
    import torch
    import transformers

    # Database
    import sqlalchemy
    import chromadb

    # NLP
    import spacy

    # Utilities
    import dotenv
    import structlog
    import streamlit

    print("✓ All critical packages imported successfully")
    sys.exit(0)
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
END

if [ $? -eq 0 ]; then
    log_success "Package verification complete"
else
    log_error "Some packages failed to import. Check the output above."
fi

echo ""

# =============================================================================
# 12. Display Next Steps
# =============================================================================
echo "============================================================================="
echo "  Setup Complete!"
echo "============================================================================="
echo ""
log_success "Environment setup completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Edit .env file with your API keys and credentials:"
echo "     - TIKTOK_MS_TOKEN (extract from browser cookies)"
echo "     - GEMINI_API_KEY (get from Google AI Studio)"
echo "     - DATABASE_URL (verify PostgreSQL connection)"
echo ""
echo "  3. Test database connection:"
echo "     python scripts/test_database.py"
echo ""
echo "  4. Run a test scrape:"
echo "     python scripts/test_scraper.py"
echo ""
echo "  5. Start the Streamlit app:"
echo "     streamlit run app/streamlit_app.py"
echo ""
echo "Documentation:"
echo "  - README.md - Project overview and usage"
echo "  - docs/setup.md - Detailed setup instructions"
echo "  - docs/api_keys.md - How to get API keys"
echo ""
echo "Troubleshooting:"
echo "  - If PostgreSQL connection fails, check your credentials in .env"
echo "  - If TikTok scraping fails, you may need to update ms_token"
echo "  - For Colab GPU processing, upload notebooks/ to Google Drive"
echo ""
log_info "Happy building! 🚀"
echo "============================================================================="
