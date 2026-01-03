# API Quick Start Guide

## Starting the API Server

```bash
# Install dependencies first
pip install -r requirements.txt

# Start the FastAPI server
uvicorn src.api.server:app --reload --port 8000
```

The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Collect News Articles
```bash
POST /api/news/collect?count=5&days=7
```

**Parameters:**
- `count` (optional): Number of articles to collect (1-10, default: 5)
- `days` (optional): Recency window in days (1–30, default: 7)

**Response:**
```json
{
  "articles": [                        // AI-filtered list (top-N)
    {
      "title": "AI Revolutionizes Talent Acquisition...",
      "url": "https://example.com/article",
      "summary": "Article summary...",
      "relevance_score": 0.9,
      "category": "ai_in_talent",
      "source": "Tech News",
      "published_date": null
    }
  ],
  "total_count": 10,                   // raw total collected
  "filtered_count": 5,                 // number after filtering
  "all_articles": [ ... ],             // NEW: raw top results (pre-filter)
  "filtered_articles": [ ... ]         // NEW: explicit filtered list (same as articles)
}
```

### 3. Generate Posts with Images
```bash
POST /api/generate
```

**JSON Body (GenerateRequest):**
```json
{
  "count": 1,
  "days": 7,
  "save_to_disk": true,
  "selected_urls": ["https://example.com/article-1"],
  "extra_urls": ["https://example.com/another-article"]
}
```

Notes:
- If `selected_urls` / `extra_urls` provided, they are used (deduped). Otherwise top filtered articles are used.
- One post is created per URL (1:1), then one image per post.

**Response:**
```json
[
  {
    "post": {
      "content": "LinkedIn post content...",
      "hashtags": ["AI", "TalentAcquisition", "HR"],
      "image_prompt": "Image prompt...",
      "metadata": {...},
      "news_article_title": "Article title",
      "news_article_url": "https://..."
    },
    "image": {
      "image_url": "https://...",
      "image_path": "output/images/post_image_xxx.png",
      "prompt_used": "Enhanced prompt...",
      "generation_metadata": {...}
    },
    "post_index": 1
  }
]
```

### 4. Progressive Generation (Async Job)
Start a job:
```bash
POST /api/generate/async
Body: GenerateRequest (same as above)
```

**Response:**
```json
{
  "job_id": "c7b7d3d4b4c54c7a9fb3c7a0b7a1e3f2",
  "total_expected": 3
}
```

Poll job status (progressive results returned as they complete):
```bash
GET /api/generate/status/{job_id}
```

**Response:**
```json
{
  "job_id": "c7b7d3d4b4c54c7a9fb3c7a0b7a1e3f2",
  "total_expected": 3,
  "completed": 2,
  "items": [ { /* GeneratedContent #1 */ }, { /* GeneratedContent #2 */ } ]
}
```

## Using the API

### With curl

```bash
# Health check
curl http://localhost:8000/health

# Collect 5 news articles from the past 7 days
curl -X POST "http://localhost:8000/api/news/collect?count=5&days=7"

# Generate 1 post with image (synchronous)
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"count":1,"days":7,"save_to_disk":true,"selected_urls":[],"extra_urls":[]}'

# Start async job (progressive)
curl -X POST "http://localhost:8000/api/generate/async" \
  -H "Content-Type: application/json" \
  -d '{"count":3,"days":7,"save_to_disk":true,"selected_urls":[],"extra_urls":[]}'

# Poll job status
curl "http://localhost:8000/api/generate/status/JOB_ID_HERE"
```

### With Python

```python
import requests

API_BASE = "http://localhost:8000"

# Health check
response = requests.get(f"{API_BASE}/health")
print(response.json())

# Collect news (past 7 days)
response = requests.post(
    f"{API_BASE}/api/news/collect",
    params={"count": 5, "days": 7}
)
news = response.json()
print(f"Found {len(news['articles'])} articles")

# Generate posts (sync)
payload = {"count": 1, "days": 7, "save_to_disk": True, "selected_urls": [], "extra_urls": []}
response = requests.post(f"{API_BASE}/api/generate", json=payload)
posts = response.json()
print(f"Generated {len(posts)} posts")

# Progressive: start job then poll
payload = {"count": 3, "days": 7, "save_to_disk": True, "selected_urls": [], "extra_urls": []}
job = requests.post(f"{API_BASE}/api/generate/async", json=payload).json()
job_id = job["job_id"]
status = requests.get(f"{API_BASE}/api/generate/status/{job_id}").json()
print(status["completed"], "done out of", status["total_expected"])
```

### With JavaScript/TypeScript

```javascript
const API_BASE = "http://localhost:8000";

// Collect news (past 7 days)
const response = await fetch(`${API_BASE}/api/news/collect?count=5&days=7`, {
  method: "POST",
});
const news = await response.json();

// Generate posts (sync)
const postsResp = await fetch(`${API_BASE}/api/generate`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    count: 1,
    days: 7,
    save_to_disk: true,
    selected_urls: [],
    extra_urls: [],
  }),
});
const posts = await postsResp.json();

// Progressive
const jobResp = await fetch(`${API_BASE}/api/generate/async`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ count: 3, days: 7, save_to_disk: true, selected_urls: [], extra_urls: [] }),
});
const { job_id, total_expected } = await jobResp.json();
const statusResp = await fetch(`${API_BASE}/api/generate/status/${job_id}`);
const status = await statusResp.json();
```

## Error Handling

All endpoints return standard HTTP status codes:
- `200`: Success
- `404`: Resource not found (e.g., no news articles found)
- `422`: Validation error (invalid parameters)
- `500`: Internal server error

Error response format:
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## Best Practices

1. **Always check the health endpoint** before making requests
2. **Handle timeouts**: Image generation can take 30-60 seconds
3. **Save to disk**: Set `save_to_disk=true` to persist outputs
4. **Start small**: Test with `count=1` first
5. **Monitor logs**: The server logs all operations

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify `.env` file exists with valid `OPENAI_API_KEY`

### No news articles found
- Check your NewsAPI/SerpAPI keys in `.env`
- The system will use mock data if APIs fail (for testing)

### Image generation fails
- Verify your OpenAI API key is valid
- Check you have credits in your OpenAI account
- Image generation requires DALL-E 3 access

### Slow response times
- Image generation takes 20-40 seconds per image
- Consider using `count=1` for testing
- Use background tasks for production (future enhancement)

