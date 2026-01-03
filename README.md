# AI News Agent System for LinkedIn Content Generation

An intelligent multi-agent system that automatically scans the internet for the latest AI and talent/hiring news, generates professional LinkedIn posts, and creates branded images for each post.

## Features

- **News Scraper Agent**: Fetches top 10 news articles from multiple sources and filters to the 5 most relevant articles about AI advancements, AI in HR, and AI in talent/hiring
- **Content Writer Agent**: Generates engaging, professional LinkedIn posts from news articles
- **Image Generator Agent**: Creates branded images using DALL-E with your firm's color theme

## Architecture

The system uses the Pydantic AI framework to create three specialized agents:

1. **News Scraper Agent**: Uses web search and NewsAPI to find relevant news articles
2. **Content Writer Agent**: Transforms news articles into LinkedIn-ready posts
3. **Image Generator Agent**: Generates branded images for each post

## Setup

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (required for DALL-E image generation)
- NewsAPI key (optional, for structured news)
- SerpAPI key (optional, for enhanced web search)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd intalent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
NEWSAPI_KEY=your_newsapi_key_here  # Optional
SERPAPI_KEY=your_serpapi_key_here  # Optional
```

5. Configure your color theme in `.env`:
```env
COLOR_PRIMARY=#000000
COLOR_SECONDARY=#FFFFFF
COLOR_ACCENT=#0066CC
COLOR_BACKGROUND=#F5F5F5
COLOR_TEXT=#333333
```

## Usage

### Option 1: Command Line (CLI)

Run the main script:
```bash
python -m src.main
```

The system will:
1. Fetch and filter news articles
2. Generate LinkedIn posts (currently set to 1 for testing)
3. Create branded images for each post
4. Save all outputs to the `output/` directory

### Option 2: API Server (Recommended)

Start the FastAPI server:
```bash
uvicorn src.api.server:app --reload --port 8000
```

The API will be available at:
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

#### API Endpoints

**1. Health Check**
```bash
GET /health
```

**2. Collect News Articles**
```bash
POST /api/news/collect?count=5
```
Returns: List of filtered news articles

**3. Generate Posts with Images**
```bash
POST /api/generate?count=1&save_to_disk=true
```
Returns: Generated LinkedIn posts with images

### Option 3: Streamlit UI (Easiest)

Start the Streamlit web interface:
```bash
streamlit run streamlit_app.py
```

The UI will open in your browser at http://localhost:8501

Features:
- Collect and preview news articles
- Generate posts with images
- View generated content in real-time
- Download posts and images

### Output Structure

```
output/
├── generated_content_YYYYMMDD_HHMMSS.json  # Complete JSON with all data
├── posts/
│   ├── post_1.txt
│   ├── post_2.txt
│   └── ...
└── images/
    ├── post_image_*.png
    └── ...
```

## Configuration

All configuration is managed through environment variables in the `.env` file:

- **API Keys**: OpenAI (required), NewsAPI (optional), SerpAPI (optional)
- **Color Theme**: Primary, secondary, accent, background, and text colors
- **Post Settings**: Tone, maximum length
- **Image Settings**: Size, quality

## Project Structure

```
intalent/
├── src/
│   ├── agents/          # Pydantic AI agents
│   │   ├── news_scraper.py
│   │   ├── content_writer.py
│   │   └── image_generator.py
│   ├── models/          # Pydantic data models
│   │   ├── news.py
│   │   └── post.py
│   ├── services/        # External API integrations
│   │   ├── news_service.py
│   │   └── image_service.py
│   ├── api/             # FastAPI server
│   │   ├── server.py
│   │   └── models.py
│   ├── config/          # Configuration management
│   │   └── settings.py
│   └── main.py          # CLI orchestrator
├── streamlit_app.py     # Streamlit web UI
├── requirements.txt
├── .env.example
└── README.md
```

## Dependencies

### Core
- `pydantic-ai`: Core agent framework
- `openai`: DALL-E image generation
- `pydantic`: Data validation
- `pydantic-settings`: Settings management
- `python-dotenv`: Environment variable management

### Data Collection
- `httpx`: HTTP requests for news scraping
- `beautifulsoup4`: HTML parsing

### API & UI
- `fastapi`: REST API framework
- `uvicorn`: ASGI server
- `streamlit`: Web UI framework

## API Examples

### Using curl

**Collect news:**
```bash
curl -X POST "http://localhost:8000/api/news/collect?count=5"
```

**Generate posts:**
```bash
curl -X POST "http://localhost:8000/api/generate?count=1&save_to_disk=true"
```

### Using Python

```python
import requests

# Collect news
response = requests.post("http://localhost:8000/api/news/collect", params={"count": 5})
news = response.json()

# Generate posts
response = requests.post("http://localhost:8000/api/generate", params={"count": 1})
posts = response.json()
```

## Notes

- The system requires an OpenAI API key for image generation
- NewsAPI and SerpAPI keys are optional but recommended for better news quality
- Color theme can be customized to match your brand
- LinkedIn post guidelines can be refined in the Content Writer Agent's system prompt
- API server includes built-in error handling and logging
- All endpoints are fully typed with Pydantic models

## License

[Add your license here]

