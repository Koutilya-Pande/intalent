"""Service for generating images using DALL-E."""

from pathlib import Path
from typing import Optional

import httpx
from openai import AsyncOpenAI

from src.config.settings import Settings
from src.models.post import GeneratedImage


class ImageService:
    """Service for generating images using DALL-E."""

    def __init__(self, settings: Settings):
        """Initialize image service with settings."""
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.image_size = settings.image_size
        self.image_quality = settings.image_quality
        self.color_theme = settings.get_color_theme()

    def _enhance_prompt_with_theme(
        self,
        base_prompt: str,
    ) -> str:
        """Enhance image prompt with brand color theme."""
        theme_description = (
            f"Use a professional color palette with: "
            f"Primary color: {self.color_theme.primary} (Lilac), "
            f"Secondary color: {self.color_theme.secondary} (White/Light Grey), "
            f"Accent color: {self.color_theme.accent} (Orange/Amber), "
            f"Background color: {self.color_theme.background} (Charcoal), "
            f"Text color: {self.color_theme.text} (for dark backgrounds). "
            f"Professional, modern, clean design style with these specific brand colors."
        )
        return f"{base_prompt}. {theme_description}"

    async def generate_image(
        self,
        prompt: str,
        output_dir: Optional[Path] = None,
    ) -> GeneratedImage:
        """Generate an image using DALL-E."""
        enhanced_prompt = self._enhance_prompt_with_theme(prompt)

        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=self.image_size,
                quality=self.image_quality,
                n=1,
            )

            image_url = response.data[0].url
            image_path = None

            # Download and save image if output directory is provided
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                async with httpx.AsyncClient(timeout=30.0) as client:
                    img_response = await client.get(image_url)
                    img_response.raise_for_status()

                    # Generate filename from prompt hash
                    import hashlib

                    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                    filename = f"post_image_{prompt_hash}.png"
                    image_path = output_dir / filename

                    with open(image_path, "wb") as f:
                        f.write(img_response.content)

            return GeneratedImage(
                image_url=image_url,
                image_path=str(image_path) if image_path else None,
                prompt_used=enhanced_prompt,
                generation_metadata={
                    "model": "dall-e-3",
                    "size": self.image_size,
                    "quality": self.image_quality,
                },
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate image: {str(e)}") from e

