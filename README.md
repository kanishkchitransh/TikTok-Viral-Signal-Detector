# TikTok Viral Signal Detector

> A multi-agent AI system that predicts which micro-creators will go viral in the next 30 days using multimodal analysis (video, audio, text) and machine learning.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development Roadmap](#development-roadmap)
- [Technical Stack](#technical-stack)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project demonstrates a production-grade multi-agent AI system for predicting TikTok creator virality. Unlike traditional tools that only analyze metadata, this system will use:

- **Multimodal AI**: Analyzes what creators SAY (Whisper), SHOW (CLIP), and their audience engagement patterns
- **Agentic Architecture**: 5 specialized agents orchestrated with LangGraph
- **Predictive ML**: Ensemble of XGBoost and Neural Networks (target: 75%+ Precision-Recall AUC)
- **Intelligence Reports**: AI-generated actionable insights using Gemini 2.5 Flash

**Perfect for**: Brands seeking early partnerships with micro-creators before they become expensive.

**Current Status**: Week 1 complete - environment setup and data collection agent (scraper) fully functional.

---

## Key Features

### 🤖 Multi-Agent System
- **Agent 1**: TikTok scraper with production-grade rate limiting
- **Agent 2**: Multimodal video analysis (Whisper + CLIP + NLP)
- **Agent 3**: Engagement pattern detection with statistical analysis
- **Agent 4**: ML prediction using ensemble models
- **Agent 5**: Intelligence report generation with LLM

### 🎥 Multimodal Analysis
- **Speech-to-Text**: Whisper transcription of video audio
- **Visual Understanding**: CLIP embeddings for semantic video search
- **Hook Analysis**: First 3-second quality scoring
- **Sentiment Analysis**: NLP on captions and transcripts
- **Entity Recognition**: Brand/product mentions

### 📊 Advanced Features
- Growth velocity with Z-score anomaly detection
- Bot detection and authenticity scoring
- Content diversity analysis
- Posting consistency metrics
- Feature importance explanations

### 🎯 100% Free Tier
Built entirely on free resources:
- Local: CPU-based processing
- Colab: GPU for Whisper/CLIP
- PostgreSQL + ChromaDB for storage
- Gemini 2.5 Flash API (1500 req/day free)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (LangGraph)                  │
│              Coordinates all agents, manages state           │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌───────▼──────────┐
│ Agent 1:       │       │ Agent 2:         │
│ Scraper        │       │ Video Analysis   │
│ - TikTok-Api   │       │ - Whisper (GPU)  │
│ - Rate Limited │       │ - CLIP (GPU)     │
└────────┬───────┘       └────────┬─────────┘
         │                        │
         │    ┌───────────────────┘
         │    │
┌────────▼────▼──────┐
│ Agent 3:           │
│ Engagement Pattern │
│ - Growth Z-scores  │
└────────┬───────────┘
         │
┌────────▼───────────┐       ┌────────────────┐
│ Agent 4:           │       │ Agent 5:       │
│ ML Prediction      │──────▶│ Report Gen     │
│ - XGBoost+NN       │       │ - Gemini 2.5   │
└────────────────────┘       └────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- FFmpeg
- Tesseract OCR

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/TikTok-Viral-Signal-Detector.git
cd TikTok-Viral-Signal-Detector

# Run the setup script
bash setup.sh
```

The setup script will:
1. Create a virtual environment
2. Install all Python dependencies
3. Setup Playwright browsers
4. Download spaCy language models
5. Initialize PostgreSQL database
6. Create project directory structure

### Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required credentials**:
- `TIKTOK_MS_TOKEN`: Extract from browser cookies (see [How to Get API Keys](docs/api_keys.md))
- `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `DATABASE_URL`: PostgreSQL connection string

### Verify Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Test database connection
python scripts/test_database.py

# Run test scrape
python scripts/test_scraper.py
```

---

## Detailed Setup

### System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib ffmpeg tesseract-ocr
```

#### macOS
```bash
brew install postgresql ffmpeg tesseract
```

#### Docker Alternative (PostgreSQL)
```bash
docker run --name tiktok-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:14
```

### Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Database Setup

```bash
# Create database
createdb -U postgres tiktok_viral_detector

# Initialize schema
psql -U postgres -d tiktok_viral_detector -f scripts/init_database.sql

# Verify tables created
psql -U postgres -d tiktok_viral_detector -c "\dt"
```

### Getting API Keys

#### TikTok ms_token
1. Open TikTok in your browser (logged in)
2. Press F12 to open Developer Tools
3. Go to: Application → Cookies → https://www.tiktok.com
4. Find cookie named `ms_token`
5. Copy the value to `.env`

**Note**: Token expires periodically; you'll need to refresh it.

#### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy key to `.env`
4. Free tier: 15 requests/min, 1500/day

---

## Usage

### Single Creator Analysis (Week 1 - Available Now)

```python
from agents.scraper import ScraperAgent

# Create scraper agent
agent = ScraperAgent()

# Scrape a creator (uses safe mode if no TikTok API token)
result = agent.run(creator_handle="@fitnessguru123", max_videos=15)

if result['status'] == 'success':
    print(f"Creator ID: {result['data']['creator_id']}")
    print(f"Videos scraped: {result['data']['videos_scraped']}")
    print(f"Followers: {result['data']['metadata']['follower_count']:,}")
```

### Full Pipeline Analysis (Coming in Week 5)

```python
# This will be available after Agents 2-5 are implemented
from orchestration.workflow import analyze_creator

# Analyze a creator end-to-end
result = analyze_creator("@fitnessguru123")

print(f"Viral Probability: {result['viral_probability']:.1%}")
print(f"Report:\n{result['intelligence_report']}")
```

### Streamlit Web Interface (Coming in Week 6)

```bash
# Start the app
streamlit run app/streamlit_app.py
```

Then open http://localhost:8501 in your browser.

### Batch Processing

```bash
# Scrape multiple creators
python scripts/scrape_creators.py --handles-file creators.txt

# Run batch analysis
python scripts/batch_analyze.py --input data/creators.csv --output results.csv
```

### Colab GPU Processing

For heavy video processing (Whisper + CLIP):

1. Upload `notebooks/02_video_processing.ipynb` to Google Colab
2. Upload videos to Google Drive
3. Run notebook on GPU runtime
4. Download processed embeddings and transcripts
5. Place in `data/processed/`

---

## Project Structure

```
tiktok-viral-detector/
├── agents/                    # Agent implementations
│   ├── scraper.py            # Agent 1: Data collection
│   ├── video_analyzer.py     # Agent 2: Video analysis
│   ├── engagement_analyzer.py# Agent 3: Engagement patterns
│   ├── predictor.py          # Agent 4: ML prediction
│   └── report_generator.py   # Agent 5: Report generation
│
├── orchestration/            # LangGraph workflow
│   ├── workflow.py           # Agent orchestration
│   └── state.py              # State management
│
├── models/                   # Data models
│   ├── database_models.py    # SQLAlchemy ORM
│   └── ml_models.py          # ML model definitions
│
├── utils/                    # Utilities
│   ├── video_processing.py   # Video/audio handling
│   ├── feature_engineering.py# Feature calculations
│   ├── embeddings.py         # ChromaDB interface
│   └── logging_config.py     # Structured logging
│
├── scripts/                  # Utility scripts
│   ├── init_database.sql     # Database schema
│   ├── setup_database.py     # Database initialization
│   ├── scrape_creators.py    # Batch scraping
│   └── test_scraper.py       # Testing utilities
│
├── notebooks/                # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_video_processing.ipynb  # Colab GPU
│   └── 03_model_training.ipynb    # Colab GPU
│
├── app/                      # Streamlit web interface
│   ├── streamlit_app.py
│   └── pages/
│       ├── 01_single_creator.py
│       └── 02_batch_analysis.py
│
├── docs/                     # Documentation
│   ├── architecture.md
│   ├── api_keys.md
│   └── deployment.md
│
├── requirements.txt          # Python dependencies
├── setup.sh                  # Automated setup
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## Development Roadmap

### ✅ Week 1: Foundation (COMPLETE)
- [x] Environment setup
- [x] Database schema
- [x] Agent 1: Scraper implementation
- [x] Infrastructure (config, logging, rate limiting)
- [ ] Data collection (200 creators) - ready to run

### 📋 Week 2: Video Processing
- [ ] Colab: Whisper transcription
- [ ] Colab: CLIP embeddings
- [ ] Hook analysis
- [ ] NLP processing

### 📋 Week 3: Engagement Analysis
- [ ] Agent 3: Feature engineering
- [ ] Ground truth labeling
- [ ] Training dataset creation

### 📋 Week 4: Machine Learning
- [ ] Model training (XGBoost + NN)
- [ ] Ensemble creation
- [ ] Agent 4: Inference pipeline

### 📋 Week 5: Integration
- [ ] LangGraph orchestration
- [ ] Agent 5: Report generation
- [ ] End-to-end testing

### 📋 Week 6: Deployment
- [ ] Streamlit app
- [ ] Documentation
- [ ] Demo video
- [ ] Production deployment

---

## Technical Stack

### Core Technologies
- **Language**: Python 3.9+
- **Orchestration**: LangGraph
- **Database**: PostgreSQL 14+
- **Vector Store**: ChromaDB
- **Web Framework**: Streamlit

### AI/ML Stack
- **Video Understanding**: OpenAI CLIP (ViT-B/32)
- **Speech-to-Text**: OpenAI Whisper (base)
- **NLP**: spaCy, sentence-transformers
- **ML Models**: XGBoost, PyTorch
- **LLM**: Google Gemini 2.5 Flash

### Data Processing
- **Video**: FFmpeg, OpenCV, yt-dlp
- **Text**: transformers, NLTK
- **Features**: scikit-learn, pandas, numpy

### Development Tools
- **Testing**: pytest
- **Code Quality**: black, flake8, mypy
- **Notebooks**: JupyterLab
- **Logging**: structlog

---

## Performance Metrics

**Target Benchmarks**:
- Scraping success rate: >90%
- Video processing: 30+ videos/hour (Colab GPU)
- ML Precision-Recall AUC: >0.75
- End-to-end latency: <5 min per creator
- Error rate: <5%

**Current Status** (Week 1 - COMPLETE):
- Environment setup: ✅ Complete
- Database schema: ✅ Complete
- Agent 1 (Scraper): ✅ Complete and tested
- Infrastructure: ✅ Complete (config, logging, rate limiting)
- Agent 2-5: ⏳ Not started
- ML Model training: ⏳ Not started (target: 75%+ PR-AUC)
- Full pipeline: ⏳ Pending

---

## Troubleshooting

### Common Issues

**PostgreSQL Connection Failed**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Verify credentials in .env
psql -U postgres -d tiktok_viral_detector
```

**TikTok Scraping Blocked**
- Update `ms_token` in `.env` (tokens expire)
- Add delays between requests (already configured)
- Consider using proxies (see `.env.example`)

**FFmpeg Not Found**
```bash
# Install FFmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

**Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

For more help, see [docs/troubleshooting.md](docs/troubleshooting.md) or open an issue.

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development Setup**:
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black .

# Type checking
mypy .
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **TikTok-Api** by davidteather for TikTok data access
- **OpenAI** for Whisper and CLIP models
- **Google** for Gemini 2.5 Flash API
- **LangChain** team for LangGraph framework

---

## Contact

**Project Creator**: [Your Name]
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

**Purpose**: Built as a portfolio project demonstrating AI engineering capabilities for Reacher (YC company).

---

## Roadmap & Future Features

- [ ] Real-time creator monitoring
- [ ] Multi-platform support (Instagram, YouTube Shorts)
- [ ] Competitive intelligence dashboard
- [ ] A/B testing for outreach messages
- [ ] Creator recommendation engine
- [ ] API for programmatic access

---

**Built with ❤️ using 100% free tier resources**

*Last updated: November 2024*
