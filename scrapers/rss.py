"""
RSS News Scraper

Fetches articles from RSS feeds of major news sources.
"""

import asyncio
import feedparser
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, FieldArticle(BaseModel):
    """A news


class News article from RSS"""
    title: str
    summary: str
    link: str
    published: str
    source: str
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "published": self.published,
            "source": self.source,
            "scraped_at": self.scraped_at.isoformat()
        }


class RSSScraper:
    """Scraper for RSS feeds"""
    
    # Major news RSS feeds
    FEEDS = {
        "bbc": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "reuters": "https://feeds.reuters.com/reuters/topNews",
        "npr": "https://feeds.npr.org/1001/rss.xml",
        "techcrunch": "https://techcrunch.com/feed/",
        "hackernews": "https://hnrss.org/frontpage",
        "wired": "https://www.wired.com/feed/rss",
        "theverge": "https://www.theverge.com/rss/index.xml",
    }
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def fetch_feed(self, source: str) -> list[NewsArticle]:
        """Fetch articles from a specific source"""
        if source not in self.FEEDS:
            raise ValueError(f"Unknown source: {source}")
        
        feed_url = self.FEEDS[source]
        
        # Parse synchronously (feedparser is blocking)
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
        
        articles = []
        for entry in feed.entries[:25]:  # Limit to 25
            articles.append(NewsArticle(
                title=entry.get("title", ""),
                summary=entry.get("summary", ""),
                link=entry.get("link", ""),
                published=entry.get("published", ""),
                source=source
            ))
        
        return articles
    
    async def fetch_all(self) -> list[NewsArticle]:
        """Fetch from all sources"""
        tasks = [self.fetch_feed(source) for source in self.FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
        
        return articles
    
    async def search(self, query: str) -> list[NewsArticle]:
        """Search all feeds for query"""
        all_articles = await self.fetch_all()
        
        query_lower = query.lower()
        return [
            a for a in all_articles 
            if query_lower in a.title.lower() or query_lower in a.summary.lower()
        ]


async def fetch_news(source: str = "all") -> list[NewsArticle]:
    """Convenience function"""
    scraper = RSSScraper()
    
    if source == "all":
        return await scraper.fetch_all()
    else:
        return await scraper.fetch_feed(source)


if __name__ == "__main__":
    import json
    
    async def main():
        print("Fetching news...")
        articles = await fetch_news()
        
        print(f"Found {len(articles)} articles:")
        for a in articles[:10]:
            print(f"  - {a.title[:60]}... ({a.source})")
        
        with open("data/news.json", "w") as f:
            json.dump([a.to_dict() for a in articles], f, indent=2)
    
    asyncio.run(main())
