"""Image Generator Agent using Pydantic AI."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from pydantic_ai import Agent

from src.config.settings import Settings
from src.models.post import GeneratedImage, LinkedInPost
from src.services.image_service import ImageService


class ImagePromptEnhancement(BaseModel):
    """Enhanced image prompt with branding considerations."""

    enhanced_prompt: str
    reasoning: str


class ImageGeneratorAgent:
    """Agent for generating images for LinkedIn posts."""

    def __init__(self, settings: Settings):
        """Initialize image generator agent."""
        self.settings = settings
        self.image_service = ImageService(settings)

        # Create Pydantic AI agent for prompt enhancement
        # Note: DALL-E is for image generation only, not text processing.
        # This agent uses GPT-4o-mini to enhance text prompts before sending to DALL-E.
        self.prompt_agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=(
                "You are a Senior Art Director for 'intalent,' an AI-human collaboration firm. "
                "Your goal is to enhance image prompts for LinkedIn to look like high-end editorial photography, "
                "not generic AI art.\n\n"
                "Style Guidelines:\n"
                "- Aesthetic: Sleek, minimal, and sophisticated; premium tech lifestyle or conceptual architecture.\n"
                "- Composition: Clean, modern, and open; ample negative space; 1:1 square framing.\n"
                "- Lighting: Soft, professional studio lighting with subtle gradients.\n\n"
                "Anti-AI Tropes (Avoid at all costs):\n"
                "- No glowing brains, digital networks, floating matrices, or literal robots.\n"
                "- No dark hacker rooms or matrix-style code backgrounds.\n\n"
                "Preferred Visual Concepts:\n"
                "- Human-Centric: Close-ups of professionals in thoughtful poses, minimalist glass offices, "
                "or abstract representations of growth and achievement.\n"
                "- Abstract Tech: Frosted glass textures, clean lines, geometric shapes, and high-quality material finishes "
                "(brushed metal, matte plastics, high-end fabrics).\n\n"
                "Instructions:\n"
                "- Output 1–2 sentences max. Focus on concrete subjects and specific material textures.\n"
                "- Do not include text, logos, or labels."
            ),
            output_type=ImagePromptEnhancement,
        )

    async def enhance_prompt(
        self,
        base_prompt: str,
    ) -> str:
        """Enhance image prompt using AI agent."""
        result = await self.prompt_agent.run(
            f"Enhance this image prompt for a professional LinkedIn post: {base_prompt}",
        )
        return result.output.enhanced_prompt

    async def generate_image(
        self,
        post: LinkedInPost,
        output_dir: Optional[Path] = None,
    ) -> GeneratedImage:
        """Generate an image for a LinkedIn post."""
        # Enhance the prompt from the post
        enhanced_prompt = await self.enhance_prompt(post.image_prompt)

        # Generate image using the service
        image = await self.image_service.generate_image(
            enhanced_prompt,
            output_dir=output_dir,
        )

        return image

    async def generate_images(
        self,
        posts: list[LinkedInPost],
        output_dir: Optional[Path] = None,
    ) -> list[GeneratedImage]:
        """Generate images for multiple posts."""
        images = []
        for post in posts:
            image = await self.generate_image(post, output_dir=output_dir)
            images.append(image)
        return images

