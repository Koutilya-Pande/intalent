"""Service for fetching news articles from various sources."""

from typing import Optional

import httpx
from bs4 import BeautifulSoup

from src.config.settings import Settings
from src.models.news import NewsArticle, NewsCategory


class NewsService:
    """Service for fetching and processing news articles."""

    def __init__(self, settings: Settings):
        """Initialize news service with settings."""
        self.settings = settings
        self.newsapi_key = settings.newsapi_key
        self.serpapi_key = settings.serpapi_key

    async def fetch_from_newsapi(
        self,
        query: str,
        max_results: int = 10,
        days: int | None = None,
    ) -> list[NewsArticle]:
        """Fetch news from NewsAPI.org."""
        if not self.newsapi_key:
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": self.newsapi_key,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": max_results,
            }
            if days is not None and days > 0:
                # NewsAPI supports ISO8601 'from' parameter
                import datetime as _dt
                from_date = (_dt.datetime.utcnow() - _dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
                params["from"] = from_date

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                articles = []
                for item in data.get("articles", [])[:max_results]:
                    if item.get("title") and item.get("url"):
                        article = NewsArticle(
                            title=item["title"],
                            url=item["url"],
                            summary=item.get("description", "") or item.get("content", "")[:200],
                            relevance_score=0.5,
                            category=self._categorize_article(item["title"], item.get("description", "")),
                            source=item.get("source", {}).get("name"),
                            published_date=item.get("publishedAt"),
                        )
                        articles.append(article)

                return articles
        except Exception as e:
            print(f"Warning: NewsAPI failed for query '{query}': {str(e)}")
            return []

    async def fetch_from_serpapi(
        self,
        query: str,
        max_results: int = 10,
        days: int | None = None,
    ) -> list[NewsArticle]:
        """Fetch news using SerpAPI."""
        if not self.serpapi_key:
            return []

        try:
            url = "https://serpapi.com/search"
            params = {
                "q": f"{query} news",
                "api_key": self.serpapi_key,
                "engine": "google",
                "tbm": "nws",  # News search
                "num": max_results,
            }
            # Recency filter: qdr:d (day), qdr:w (week), qdr:m (month)
            if days is not None and days > 0:
                if days <= 1:
                    params["tbs"] = "qdr:d"
                elif days <= 7:
                    params["tbs"] = "qdr:w"
                else:
                    params["tbs"] = "qdr:m"
            params["hl"] = "en"
            params["gl"] = "us"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                articles = []
                news_results = data.get("news_results", [])
                for item in news_results[:max_results]:
                    if item.get("title") and item.get("link"):
                        article = NewsArticle(
                            title=item["title"],
                            url=item["link"],
                            summary=item.get("snippet", ""),
                            relevance_score=0.5,
                            category=self._categorize_article(item["title"], item.get("snippet", "")),
                            source=item.get("source"),
                            published_date=item.get("date"),
                        )
                        articles.append(article)

                return articles
        except Exception as e:
            print(f"Warning: SerpAPI failed for query '{query}': {str(e)}")
            return []

    async def fetch_from_web_search(
        self,
        query: str,
        max_results: int = 10,
        days: int | None = None,
    ) -> list[NewsArticle]:
        """Fetch news using web search (fallback when APIs are not available)."""
        try:
            # Use DuckDuckGo HTML search as a free alternative
            url = "https://html.duckduckgo.com/html/"
            params = {"q": f"{query} news"}

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                # Try multiple selectors for DuckDuckGo results
                results = soup.find_all("a", class_="result__a", limit=max_results)
                if not results:
                    # Alternative selector
                    results = soup.find_all("a", {"class": "web-result"}, limit=max_results)
                if not results:
                    # Another alternative
                    results = soup.select("a.result__a", limit=max_results)

                articles = []
                for result in results:
                    title = result.get_text(strip=True)
                    url_str = result.get("href", "")
                    if not url_str and result.get("data-result"):
                        url_str = result.get("data-result")
                    
                    if title and url_str:
                        # Clean up URL if needed
                        if url_str.startswith("//"):
                            url_str = "https:" + url_str
                        elif url_str.startswith("/"):
                            continue  # Skip relative URLs
                        
                        article = NewsArticle(
                            title=title,
                            url=url_str,
                            summary="",
                            relevance_score=0.5,
                            category=self._categorize_article(title, ""),
                            source=None,
                            published_date=None,
                        )
                        articles.append(article)

                return articles
        except Exception as e:
            print(f"Warning: Web search failed for query '{query}': {str(e)}")
            return []

    async def fetch_news(
        self,
        max_results: int = 10,
        days: int | None = None,
    ) -> list[NewsArticle]:
        """Fetch news articles from multiple sources."""
        queries = [
            '(AI OR "artificial intelligence") (hiring OR recruitment OR "talent acquisition")',
            '(AI OR "artificial intelligence") (HR OR "human resources")',
            '"AI advancement" OR "AI breakthrough" OR "generative AI"',
        ]

        all_articles = []

        # Try NewsAPI first
        if self.newsapi_key:
            print("   Using NewsAPI...")
            for query in queries:
                articles = await self.fetch_from_newsapi(query, max_results=5, days=days)
                all_articles.extend(articles)
                if articles:
                    print(f"   Found {len(articles)} articles for: {query}")

        # Try SerpAPI if NewsAPI didn't work
        if not all_articles and self.serpapi_key:
            print("   NewsAPI not available or returned no results. Trying SerpAPI...")
            for query in queries:
                articles = await self.fetch_from_serpapi(query, max_results=5, days=days)
                all_articles.extend(articles)
                if articles:
                    print(f"   Found {len(articles)} articles for: {query}")

        # Fallback to web search if APIs didn't work
        if not all_articles:
            print("   APIs not available or returned no results. Trying web search...")
            for query in queries:
                articles = await self.fetch_from_web_search(query, max_results=5, days=days)
                all_articles.extend(articles)
                if articles:
                    print(f"   Found {len(articles)} articles for: {query}")

        # If still no articles, provide some mock data for testing
        if not all_articles:
            print("   Warning: No articles found from any source. Using mock data for testing...")
            all_articles = self._get_mock_articles()

        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url_str = str(article.url)
            if url_str not in seen_urls:
                seen_urls.add(url_str)
                unique_articles.append(article)

        return unique_articles[:max_results]

    def _get_mock_articles(self) -> list[NewsArticle]:
        """Return mock articles for testing when no real articles are found."""
        return [
            NewsArticle(
                title="AI Revolutionizes Talent Acquisition: New Tools Transform Hiring",
                url="https://example.com/ai-talent-acquisition",
                summary="Artificial intelligence is transforming how companies find and hire talent, with new AI-powered tools making recruitment more efficient and effective.",
                relevance_score=0.9,
                category=NewsCategory.AI_IN_TALENT,
                source="Tech News",
                published_date=None,
            ),
            NewsArticle(
                title="HR Departments Embrace AI for Employee Management",
                url="https://example.com/ai-hr-management",
                summary="Human resources departments are increasingly adopting AI technologies to streamline employee management, improve engagement, and optimize workforce planning.",
                relevance_score=0.85,
                category=NewsCategory.AI_IN_HR,
                source="HR Today",
                published_date=None,
            ),
            NewsArticle(
                title="Latest AI Breakthroughs in Machine Learning and Automation",
                url="https://example.com/ai-breakthroughs",
                summary="Recent advances in artificial intelligence and machine learning are opening new possibilities for automation and intelligent systems across industries.",
                relevance_score=0.8,
                category=NewsCategory.AI_ADVANCEMENT,
                source="AI Weekly",
                published_date=None,
            ),
            NewsArticle(
                title="AI-Powered Recruitment Platforms Gain Traction",
                url="https://example.com/ai-recruitment-platforms",
                summary="Companies are turning to AI-powered recruitment platforms that use machine learning to match candidates with job opportunities more accurately.",
                relevance_score=0.75,
                category=NewsCategory.AI_IN_TALENT,
                source="Recruitment Tech",
                published_date=None,
            ),
            NewsArticle(
                title="How AI is Reshaping the Future of Work and Hiring",
                url="https://example.com/ai-future-work",
                summary="Artificial intelligence is fundamentally changing the landscape of work, from how jobs are posted to how candidates are evaluated and selected.",
                relevance_score=0.7,
                category=NewsCategory.AI_IN_HR,
                source="Future of Work",
                published_date=None,
            ),
        ]

    def _categorize_article(
        self,
        title: str,
        description: str,
    ) -> NewsCategory:
        """Categorize article based on title and description."""
        text = (title + " " + description).lower()

        if any(term in text for term in ["hr", "human resources", "recruitment", "hiring", "talent acquisition"]):
            if "talent" in text:
                return NewsCategory.AI_IN_TALENT
            return NewsCategory.AI_IN_HR

        return NewsCategory.AI_ADVANCEMENT

    async def fetch_article_from_url(self, url: str) -> NewsArticle | None:
        """Fetch a single article by URL and extract basic metadata."""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")
            # Extract title
            title = (
                (soup.find("meta", property="og:title") or {}).get("content")
                or soup.title.string if soup.title else None
            )
            # Extract description
            description = (
                (soup.find("meta", attrs={"name": "description"}) or {}).get("content")
                or (soup.find("meta", property="og:description") or {}).get("content")
                or ""
            )
            if not title:
                return None

            category = self._categorize_article(title, description or "")
            return NewsArticle(
                title=title.strip(),
                url=url,
                summary=description.strip() if description else "",
                relevance_score=0.6,
                category=category,
                source=None,
                published_date=None,
            )
        except Exception:
            return None

