"""Data models for LinkedIn posts and generated content."""

from typing import Optional

from pydantic import BaseModel, Field


class LinkedInPost(BaseModel):
    """Represents a LinkedIn post with content and metadata."""

    content: str = Field(..., description="Post content text")
    hashtags: list[str] = Field(
        default_factory=list,
        description="List of hashtags for the post",
    )
    image_prompt: str = Field(..., description="Prompt for image generation")
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    news_article_title: Optional[str] = Field(
        None,
        description="Title of the source news article",
    )
    news_article_url: Optional[str] = Field(
        None,
        description="URL of the source news article",
    )


class GeneratedImage(BaseModel):
    """Represents a generated image for a post."""

    image_url: Optional[str] = Field(None, description="URL of the generated image")
    image_path: Optional[str] = Field(None, description="Local file path of the image")
    prompt_used: str = Field(..., description="Prompt used for image generation")
    generation_metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Metadata about image generation",
    )


class GeneratedContent(BaseModel):
    """Complete generated content pairing post with image."""

    post: LinkedInPost = Field(..., description="LinkedIn post content")
    image: GeneratedImage = Field(..., description="Generated image for the post")
    post_index: int = Field(..., description="Index of this post (1-5)")

