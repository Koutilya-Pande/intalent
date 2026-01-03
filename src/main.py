"""Main orchestrator for the AI News Agent System."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.agents.content_writer import ContentWriterAgent
from src.agents.image_generator import ImageGeneratorAgent
from src.agents.news_scraper import NewsScraperAgent
from src.config.settings import get_settings
from src.models.post import GeneratedContent


async def main() -> None:
    """Main entry point for the AI News Agent System."""
    try:
        settings = get_settings()
    except Exception as e:
        print("❌ Error loading configuration:")
        print(f"   {str(e)}")
        print("\n💡 Please create a .env file with your API keys.")
        print("   See SETUP.md for instructions.")
        print("   Required: OPENAI_API_KEY")
        return

    # Initialize agents
    news_agent = NewsScraperAgent(settings)
    writer_agent = ContentWriterAgent(settings)
    image_agent = ImageGeneratorAgent(settings)

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    print("Starting AI News Agent System...")
    print("=" * 50)

    try:
        # Step 1: Fetch and filter news
        print("\n[Step 1/3] Fetching and filtering news articles...")
        news_collection = await news_agent.fetch_and_filter_news(target_count=5)

        if not news_collection.articles:
            print("ERROR: No news articles found. Exiting.")
            return

        print(f"Found {news_collection.total_count} articles, filtered to {news_collection.filtered_count}")
        print("\n📰 Articles found:")
        for i, article in enumerate(news_collection.articles, start=1):
            print(f"   {i}. {article.title}")
            # Category is already a string due to use_enum_values=True
            category_str = article.category if isinstance(article.category, str) else article.category.value
            print(f"      Category: {category_str}")
            print(f"      Relevance: {article.relevance_score:.2f}")
            if article.source:
                print(f"      Source: {article.source}")
            print()

        # Step 2: Generate LinkedIn posts (TEST MODE: only 1 post)
        print("\n[Step 2/3] Generating LinkedIn posts (TEST MODE: 1 post only)...")
        # Only generate post for the first article
        first_article = news_collection.articles[0]
        post = await writer_agent.generate_post(first_article)
        posts = [post]
        print(f"Generated {len(posts)} LinkedIn post")

        # Step 3: Generate images (TEST MODE: only 1 image)
        print("\n[Step 3/3] Generating image for post (TEST MODE: 1 image only)...")
        image = await image_agent.generate_image(posts[0], output_dir=images_dir)
        images = [image]
        print(f"Generated {len(images)} image")

        # Combine posts and images
        generated_content = []
        for i, (post, image) in enumerate(zip(posts, images), start=1):
            content = GeneratedContent(
                post=post,
                image=image,
                post_index=i,
            )
            generated_content.append(content)

        # Save outputs
        print("\n[Saving] Writing outputs to files...")

        # Save JSON with all content
        output_file = output_dir / f"generated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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

        for i, content in enumerate(generated_content, start=1):
            post_file = posts_dir / f"post_{i}.txt"
            with open(post_file, "w", encoding="utf-8") as f:
                f.write(f"Post #{i}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content.post.content + "\n\n")
                f.write("Hashtags: " + ", ".join(content.post.hashtags) + "\n\n")
                f.write(f"Source: {content.post.news_article_title}\n")
                f.write(f"URL: {content.post.news_article_url}\n")
                if content.image.image_path:
                    f.write(f"Image: {content.image.image_path}\n")
                elif content.image.image_url:
                    f.write(f"Image URL: {content.image.image_url}\n")

        print(f"\n✅ Success! Generated {len(generated_content)} posts with images")
        print(f"📁 Output directory: {output_dir.absolute()}")
        print(f"📄 JSON file: {output_file}")
        print(f"📝 Post files: {posts_dir}")
        print(f"🖼️  Images: {images_dir}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

