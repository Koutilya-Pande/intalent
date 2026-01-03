"""API request and response models."""

from typing import Optional

from pydantic import BaseModel, Field
from src.models.post import GeneratedContent


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(default="1.0.0", description="API version")


class NewsRequest(BaseModel):
    """Request to collect news articles."""

    count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of articles to collect",
    )
    days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Recency window in days for news search (1-30)",
    )


class GenerateRequest(BaseModel):
    """Request to generate posts and images."""

    count: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Number of posts to generate",
    )
    days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Recency window in days for news search (1-30)",
    )
    save_to_disk: bool = Field(
        default=True,
        description="Whether to save outputs to disk",
    )
    selected_urls: list[str] = Field(
        default_factory=list,
        description="List of selected article URLs to use for generation",
    )
    extra_urls: list[str] = Field(
        default_factory=list,
        description="Additional user-provided article URLs to include",
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class GenerateJobStarted(BaseModel):
    """Response when an async generation job is started."""

    job_id: str = Field(..., description="Job identifier")
    total_expected: int = Field(..., description="Total posts expected to be generated")


class GenerateJobStatus(BaseModel):
    """Status for an async generation job."""

    job_id: str = Field(..., description="Job identifier")
    total_expected: int = Field(..., description="Total posts expected")
    completed: int = Field(..., description="Number of completed items")
    items: list[GeneratedContent] = Field(default_factory=list, description="Completed generated items so far")
