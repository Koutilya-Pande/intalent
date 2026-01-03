"""Data models for news articles."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class NewsCategory(str, Enum):
    """Categories for news articles."""

    AI_ADVANCEMENT = "ai_advancement"
    AI_IN_HR = "ai_in_hr"
    AI_IN_TALENT = "ai_in_talent"


class NewsArticle(BaseModel):
    """Represents a news article with metadata."""

    title: str = Field(..., description="Article title")
    url: HttpUrl = Field(..., description="Article URL")
    summary: str = Field(..., description="Brief summary of the article")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score between 0 and 1",
    )
    category: NewsCategory = Field(..., description="Article category")
    source: Optional[str] = Field(None, description="News source name")
    published_date: Optional[str] = Field(None, description="Publication date")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class NewsCollection(BaseModel):
    """Collection of news articles."""

    # Backward-compat: filtered list returned in `articles`
    articles: list[NewsArticle] = Field(
        ...,
        description="AI-filtered list of news articles",
    )
    total_count: int = Field(..., description="Total number of raw articles collected")
    filtered_count: int = Field(..., description="Number of articles after filtering")

    # New fields for UX: raw and filtered explicit lists
    all_articles: list[NewsArticle] = Field(
        default_factory=list,
        description="Raw top articles collected before AI filtering",
    )
    filtered_articles: list[NewsArticle] = Field(
        default_factory=list,
        description="AI-filtered list (same as `articles`)",
    )

