"""News Scraper Agent using Pydantic AI."""

from pydantic import BaseModel
from pydantic_ai import Agent
import logging

from src.config.settings import Settings
from src.models.news import NewsArticle, NewsCollection
from src.services.news_service import NewsService


logger = logging.getLogger(__name__)


class FilterNewsRequest(BaseModel):
    """Request model for filtering news."""

    articles: list[NewsArticle]
    target_count: int = 5


class FilterNewsResponse(BaseModel):
    """Response model for filtered news."""

    filtered_articles: list[NewsArticle]
    reasoning: str


class NewsScraperAgent:
    """Agent for scraping and filtering news articles."""

    def __init__(self, settings: Settings):
        """Initialize news scraper agent."""
        self.settings = settings
        self.news_service = NewsService(settings)

        # Create Pydantic AI agent for filtering
        self.filter_agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=(
                "You are an expert analyst filtering news for AI, HR, and talent audiences.\n"
                "Select the most relevant articles with these priorities:\n"
                "1) Recency and substance (clear, credible reporting)\n"
                "2) Relevance to AI advancements, AI in HR, or AI in talent/hiring\n"
                "3) Practical implications for HR leaders and talent teams\n"
                "4) Credible sources; avoid low-signal or duplicate content\n"
                "Return exactly the requested number, ranked by relevance."
            ),
            output_type=FilterNewsResponse,
        )

    async def fetch_and_filter_news(
        self,
        target_count: int = 5,
        days: int | None = None,
    ) -> NewsCollection:
        """Fetch top 10 news articles and filter to target count."""
        logger.info("Filtering flow started | target=%s, days=%s", target_count, days)
        # Fetch top 10 articles
        all_articles = await self.news_service.fetch_news(max_results=10, days=days)
        logger.info("Fetched %s candidate articles from sources", len(all_articles))

        if not all_articles:
            logger.warning("No candidate articles available after fetch. Returning empty collection.")
            return NewsCollection(
                articles=[],
                total_count=0,
                filtered_count=0,
            )

        # Use AI agent to filter and rank articles
        if len(all_articles) <= target_count:
            logger.info("Candidate count <= target (%s). Skipping AI filtering.", target_count)
            filtered_articles = all_articles
        else:
            logger.info("Running AI filter on %s candidates → top %s", len(all_articles), target_count)
            # Prepare article summaries for the agent
            article_summaries = [
                {
                    "title": a.title,
                    "summary": a.summary,
                    "category": a.category,
                    "url": str(a.url),
                }
                for a in all_articles
            ]

            result = await self.filter_agent.run(
                f"Filter these {len(all_articles)} articles to the top {target_count} most relevant ones. "
                f"Focus on AI advancements, AI in HR, and AI in talent/hiring. "
                f"Return the articles in order of relevance. "
                f"Articles: {article_summaries}",
            )

            # Match filtered articles back to originals by URL
            filtered_urls = {str(a.url) for a in result.output.filtered_articles}
            url_to_article = {str(a.url): a for a in all_articles}
            filtered_articles = [
                url_to_article[url] for url in filtered_urls if url in url_to_article
            ][:target_count]

        # Update relevance scores based on filtering
        for i, article in enumerate(filtered_articles):
            article.relevance_score = 1.0 - (i * 0.1)

        filtered_articles = filtered_articles[:target_count]
        logger.info(
            "Filtering completed | total=%s, selected=%s",
            len(all_articles),
            len(filtered_articles),
        )
        return NewsCollection(
            articles=filtered_articles,
            total_count=len(all_articles),
            filtered_count=len(filtered_articles),
            all_articles=all_articles,
            filtered_articles=filtered_articles,
        )

