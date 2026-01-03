# Setup Guide

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI API Key (Required for DALL-E image generation)
OPENAI_API_KEY=your_openai_api_key_here

# NewsAPI.org API Key (Optional - for structured news)
NEWSAPI_KEY=your_newsapi_key_here

# SerpAPI Key (Optional - for web search)
SERPAPI_KEY=your_serpapi_key_here

# Color Theme Configuration (defaults shown, customize as needed)
COLOR_PRIMARY=#7367FF
COLOR_SECONDARY=#F3F3F3
COLOR_ACCENT=#FFA050
COLOR_BACKGROUND=#0D0919
COLOR_TEXT=#F3F3F3

# LinkedIn Post Configuration
POST_TONE=professional
POST_MAX_LENGTH=3000

# Image Generation Configuration
IMAGE_SIZE=1024x1024
IMAGE_QUALITY=standard
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your API keys (see above)

3. Run the system:
```bash
python -m src.main
```

## API Keys

- **OpenAI API Key** (Required): Get from https://platform.openai.com/api-keys
- **NewsAPI Key** (Optional): Get from https://newsapi.org/register
- **SerpAPI Key** (Optional): Get from https://serpapi.com/

