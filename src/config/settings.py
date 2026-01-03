"""Configuration management for the application."""

from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class ColorTheme(BaseModel):
    """Color theme configuration for branding."""

    primary: str = Field(default="#7367FF", description="Primary brand color (Lilac)")
    secondary: str = Field(default="#F3F3F3", description="Secondary brand color (White/Light Grey)")
    accent: str = Field(default="#FFA050", description="Accent color (Orange/Amber)")
    background: str = Field(default="#0D0919", description="Background color (Charcoal)")
    text: str = Field(default="#F3F3F3", description="Text color (for dark backgrounds)")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    openai_api_key: str = Field(..., description="OpenAI API key for DALL-E")
    newsapi_key: Optional[str] = Field(
        None,
        description="NewsAPI.org API key (optional)",
    )
    serpapi_key: Optional[str] = Field(
        None,
        description="SerpAPI key for web search (optional)",
    )

    # Color Theme
    color_primary: str = Field(
        default="#7367FF",
        description="Primary brand color (Lilac)",
    )
    color_secondary: str = Field(
        default="#F3F3F3",
        description="Secondary brand color (White/Light Grey)",
    )
    color_accent: str = Field(
        default="#FFA050",
        description="Accent color (Orange/Amber)",
    )
    color_background: str = Field(
        default="#0D0919",
        description="Background color (Charcoal)",
    )
    color_text: str = Field(
        default="#F3F3F3",
        description="Text color (for dark backgrounds)",
    )

    # LinkedIn Post Guidelines
    post_tone: str = Field(
        default="professional",
        description="Tone for LinkedIn posts",
    )
    post_max_length: int = Field(
        default=3000,
        description="Maximum length for LinkedIn posts",
    )

    # Image Generation
    image_size: str = Field(
        default="1024x1024",
        description="DALL-E image size",
    )
    image_quality: str = Field(
        default="standard",
        description="DALL-E image quality",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_color_theme(self) -> ColorTheme:
        """Get color theme configuration."""
        return ColorTheme(
            primary=self.color_primary,
            secondary=self.color_secondary,
            accent=self.color_accent,
            background=self.color_background,
            text=self.color_text,
        )


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()

