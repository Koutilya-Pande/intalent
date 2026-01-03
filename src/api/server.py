"""FastAPI server for AI News Agent System."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.agents.content_writer import ContentWriterAgent
from src.agents.image_generator import ImageGeneratorAgent
from src.agents.news_scraper import NewsScraperAgent
from src.api.models import (
    ErrorResponse,
    GenerateJobStarted,
    GenerateJobStatus,
    GenerateRequest,
    HealthResponse,
    NewsRequest,
)
from src.config.settings import get_settings
from src.models.news import NewsCollection
from src.models.post import GeneratedContent
import asyncio
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI News Agent API",
    description="API for generating LinkedIn posts from AI/talent/hiring news",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup."""
    try:
        logger.info("Initializing AI News Agent System...")
        settings = get_settings()
        
        # Store agents in app state
        app.state.settings = settings
        app.state.news_agent = NewsScraperAgent(settings)
        app.state.writer_agent = ContentWriterAgent(settings)
        app.state.image_agent = ImageGeneratorAgent(settings)
        app.state.jobs = {}
        app.state.job_lock = asyncio.Lock()
        
        # Create output directories
        Path("output/images").mkdir(parents=True, exist_ok=True)
        Path("output/posts").mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ AI News Agent System initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {str(e)}")
        raise


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic info."""
    return HealthResponse(
        status="running",
        version="1.0.0",
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
    )


@app.post("/api/news/collect", response_model=NewsCollection)
async def collect_news(
    count: int = Query(5, ge=1, le=10, description="Number of articles to collect"),
    days: int = Query(7, ge=1, le=30, description="Recency window in days (1-30)"),
):
    """
    Collect and filter news articles.
    
    - Fetches top 10 news articles from various sources
    - Filters to the most relevant articles about AI in talent/hiring/HR
    - Returns structured news data
    """
    try:
        logger.info(f"Collecting {count} news articles...")
        news_agent = app.state.news_agent
        news_collection = await news_agent.fetch_and_filter_news(target_count=count, days=days)
        
        if not news_collection.articles:
            raise HTTPException(
                status_code=404,
                detail="No news articles found. Check API keys or try again later.",
            )
        
        logger.info(f"✅ Collected {len(news_collection.articles)} articles")
        return news_collection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error collecting news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate", response_model=list[GeneratedContent])
async def generate_content(payload: GenerateRequest):
    """
    Generate LinkedIn posts with images from news articles.
    
    - Collects news articles
    - Generates professional LinkedIn posts
    - Creates branded images for each post
    - Optionally saves outputs to disk
    - Returns complete generated content
    """
    try:
        logger.info(f"Generating {payload.count} post(s) with images...")
        
        # Get agents from app state
        news_agent = app.state.news_agent
        writer_agent = app.state.writer_agent
        image_agent = app.state.image_agent
        
        # Step 1: Collect news
        logger.info("Step 1/3: Collecting news articles...")
        news_collection = await news_agent.fetch_and_filter_news(target_count=max(5, payload.count), days=payload.days)
        
        if not news_collection.articles and not (payload.selected_urls or payload.extra_urls):
            raise HTTPException(
                status_code=404,
                detail="No news articles found. Cannot generate posts.",
            )
        
        # Build article set: selected URLs + extra URLs, else fall back to filtered
        articles_to_use = []
        if payload.selected_urls or payload.extra_urls:
            from src.services.news_service import NewsService
            service = NewsService(app.state.settings)
            urls = list(dict.fromkeys([*payload.selected_urls, *payload.extra_urls]))  # dedupe keep order
            for url in urls:
                art = await service.fetch_article_from_url(url)
                if art:
                    articles_to_use.append(art)
            if not articles_to_use:
                # fallback to filtered
                articles_to_use = news_collection.articles[:payload.count]
        else:
            articles_to_use = news_collection.articles[:payload.count]
        logger.info(f"Using {len(articles_to_use)} articles")
        
        # Step 2: Generate posts
        logger.info("Step 2/3: Generating LinkedIn posts...")
        posts = await writer_agent.generate_posts(articles_to_use)
        logger.info(f"Generated {len(posts)} posts")
        
        # Step 3: Generate images
        logger.info("Step 3/3: Generating images...")
        output_dir = Path("output/images") if payload.save_to_disk else None
        images = await image_agent.generate_images(posts, output_dir=output_dir)
        logger.info(f"Generated {len(images)} images")
        
        # Combine posts and images
        generated_content = []
        for i, (post, image) in enumerate(zip(posts, images), start=1):
            content = GeneratedContent(
                post=post,
                image=image,
                post_index=i,
            )
            generated_content.append(content)
        
        # Save to disk if requested
        if payload.save_to_disk:
            _save_outputs(generated_content)
        
        logger.info(f"✅ Successfully generated {len(generated_content)} posts with images")
        return generated_content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/async", response_model=GenerateJobStarted)
async def start_generate_job(payload: GenerateRequest):
    """Start an async generation job and return job_id for progressive polling."""
    try:
        job_id = uuid.uuid4().hex
        async with app.state.job_lock:
            app.state.jobs[job_id] = {
                "total_expected": payload.count,
                "items": [],
                "completed": 0,
            }

        # Spawn background task
        asyncio.create_task(_run_generation_job(job_id, payload))
        return GenerateJobStarted(job_id=job_id, total_expected=payload.count)
    except Exception as e:
        logger.error(f"❌ Error starting job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/generate/status/{job_id}", response_model=GenerateJobStatus)
async def get_generate_status(job_id: str):
    """Get current status of an async generation job."""
    async with app.state.job_lock:
        job = app.state.jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return GenerateJobStatus(
            job_id=job_id,
            total_expected=job["total_expected"],
            completed=job["completed"],
            items=job["items"],
        )


async def _run_generation_job(job_id: str, payload: GenerateRequest):
    """Background task to run generation per article and append results as they complete."""
    try:
        news_agent = app.state.news_agent
        writer_agent = app.state.writer_agent
        image_agent = app.state.image_agent

        # Collect news and build article list (reuse synchronous logic)
        news_collection = await news_agent.fetch_and_filter_news(
            target_count=max(5, payload.count),
            days=payload.days,
        )
        articles_to_use = []
        if payload.selected_urls or payload.extra_urls:
            from src.services.news_service import NewsService
            service = NewsService(app.state.settings)
            urls = list(dict.fromkeys([*payload.selected_urls, *payload.extra_urls]))
            for url in urls:
                art = await service.fetch_article_from_url(url)
                if art:
                    articles_to_use.append(art)
            if not articles_to_use:
                articles_to_use = news_collection.articles[:payload.count]
        else:
            articles_to_use = news_collection.articles[:payload.count]

        # Define per-article task: generate post then image
        async def process_article(idx: int, article):
            post = await writer_agent.generate_post(article)
            image = await image_agent.generate_image(post, output_dir=Path("output/images") if payload.save_to_disk else None)
            return GeneratedContent(post=post, image=image, post_index=idx + 1)

        tasks = [asyncio.create_task(process_article(i, a)) for i, a in enumerate(articles_to_use)]

        # As tasks complete, append to job store
        for coro in asyncio.as_completed(tasks):
            try:
                item = await coro
                async with app.state.job_lock:
                    job = app.state.jobs.get(job_id)
                    if job is None:
                        continue
                    job["items"].append(item)
                    job["completed"] = len(job["items"])
            except Exception as e:
                logger.warning(f"Item failed: {str(e)}")

        # Optionally, save all outputs at the end
        if payload.save_to_disk:
            async with app.state.job_lock:
                job = app.state.jobs.get(job_id)
                if job and job["items"]:
                    _save_outputs(job["items"])
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")

def _save_outputs(generated_content: list[GeneratedContent]) -> None:
    """Save generated content to disk."""
    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON with all content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"generated_content_{timestamp}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                [content.model_dump() for content in generated_content],
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        # Save individual post files
        posts_dir = output_dir / "posts"
        posts_dir.mkdir(exist_ok=True)
        
        for content in generated_content:
            post_file = posts_dir / f"post_{content.post_index}.txt"
            with open(post_file, "w", encoding="utf-8") as f:
                f.write(f"Post #{content.post_index}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content.post.content + "\n\n")
                f.write("Hashtags: " + ", ".join(content.post.hashtags) + "\n\n")
                f.write(f"Source: {content.post.news_article_title}\n")
                f.write(f"URL: {content.post.news_article_url}\n")
                if content.image.image_path:
                    f.write(f"Image: {content.image.image_path}\n")
                elif content.image.image_url:
                    f.write(f"Image URL: {content.image.image_url}\n")
        
        logger.info(f"Saved outputs to {output_dir.absolute()}")
    except Exception as e:
        logger.warning(f"Failed to save outputs to disk: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
        ).model_dump(),
    )

