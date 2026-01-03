"""Content Writer Agent using Pydantic AI."""

from pydantic_ai import Agent

from src.config.settings import Settings
from src.models.news import NewsArticle
from src.models.post import LinkedInPost


class ContentWriterAgent:
    """Agent for generating LinkedIn posts from news articles."""

    def __init__(self, settings: Settings):
        """Initialize content writer agent."""
        self.settings = settings

        # Create Pydantic AI agent for post generation
        self.writer_agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=(
                "You are the Marketing Manager at intalent. Your mission is 'Powering Human Achievement' "
                "by providing AI-driven agentic solutions for Hiring Managers and Recruiters. "
                "Write LinkedIn posts that position intalent as a sophisticated, human-centric leader in AI-recruitment.\n\n"
                "Voice & Tone:\n"
                "- Sophisticated and professional, mirroring a clean, modern editorial aesthetic.\n"
                "- Visionary yet practical; focus on how AI augments human potential rather than replacing it.\n"
                "- Avoid 'AI-hype'—use clear, authoritative language.\n\n"
                "Structure:\n"
                "1) Hook: A 1–2 line perspective on why this news is a milestone for human achievement in hiring.\n"
                "2) The 'intalent' Lens: 2–3 bullet points on impact to recruitment efficiency and talent experience.\n"
                "3) The Strategic Edge: A specific takeaway for HR leaders and Hiring Managers.\n"
                "4) CTA: A conversational question to spark engagement among the recruitment community.\n\n"
                "Image Prompt Guidance (to return in image_prompt):\n"
                "- Base it strictly on the article's theme; minimal and clean; professional; square (1:1).\n"
                "- 1–2 sentences only; include subject, setting, and style cues; optional 'gradient lighting'.\n"
                "- No text, logos, or screenshots.\n"
            ),
            output_type=LinkedInPost,
        )

    async def generate_post(
        self,
        article: NewsArticle,
    ) -> LinkedInPost:
        """Generate a LinkedIn post from a news article."""
        prompt = (
            f"Create a professional LinkedIn post based on this news article:\n\n"
            f"Title: {article.title}\n"
            f"Summary: {article.summary}\n"
            f"Category: {article.category}\n"
            f"URL: {article.url}\n\n"
            f"Write an engaging LinkedIn post that: "
            f"1. Highlights the key insights from this article "
            f"2. Provides context and value to the reader "
            f"3. Is professional and appropriate for LinkedIn "
            f"4. Includes relevant hashtags "
            f"5. Has an image prompt that would create a compelling visual representation. "
            f"The image prompt should be descriptive and suitable for DALL-E generation."
        )

        result = await self.writer_agent.run(prompt)

        post = result.output
        # Add source article metadata
        post.news_article_title = article.title
        post.news_article_url = str(article.url)
        post.metadata["source_category"] = article.category
        post.metadata["source_relevance"] = str(article.relevance_score)

        return post

    async def generate_posts(
        self,
        articles: list[NewsArticle],
    ) -> list[LinkedInPost]:
        """Generate LinkedIn posts for multiple articles."""
        posts = []
        for article in articles:
            post = await self.generate_post(article)
            posts.append(post)
        return posts

