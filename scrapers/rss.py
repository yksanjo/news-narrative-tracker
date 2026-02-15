"""
RSS Feed Aggregator

Aggregates news from RSS feeds.
"""

import asyncio
import feedparser
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Article(BaseModel):
    """News article"""
    title: str
    link: str
    published: str = ""
    summary: str = ""
    source: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    sentiment: Optional[float] = None


class RSSAggregator:
    """RSS feed aggregator"""
    
    FEEDS = {
        "techcrunch": "https://techcrunch.com/feed/",
        "ycombinator": "https://news.ycombinator.com/rss",
        "verge": "https://www.theverge.com/rss/index.xml",
        "wired": "https://www.wired.com/feed/rss",
        "ars": "https://feeds.arstechnica.com/arstechnica/index",
        "reuters": "https://www.reutersagency.com/feed/?best-topics=tech",
        "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
        "wsj": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    }
    
    def __init__(self):
        self.articles = []
    
    async def fetch_feed(self, name: str, url: str) -> list[Article]:
        """Fetch single feed"""
        print(f"Fetching {name}...")
        
        try:
            feed = feedparser.parse(url)
            
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 per feed
                article = Article(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    published=entry.get("published", ""),
                    summary=entry.get("summary", ""),
                    source=name,
                    author=entry.get("author", "")
                )
                articles.append(article)
            
            print(f"  Got {len(articles)} articles")
            return articles
        except Exception as e:
            print(f"  Error: {e}")
            return []
    
    async def fetch_all(self) -> list[Article]:
        """Fetch all feeds"""
        tasks = [
            self.fetch_feed(name, url) 
            for name, url in self.FEEDS.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        all_articles = []
        for articles in results:
            all_articles.extend(articles)
        
        # Sort by published date
        all_articles.sort(
            key=lambda a: a.published, 
            reverse=True
        )
        
        self.articles = all_articles
        return all_articles
    
    def get_by_source(self, source: str) -> list[Article]:
        """Get articles by source"""
        return [a for a in self.articles if a.source == source]
    
    def search(self, query: str) -> list[Article]:
        """Search articles"""
        query = query.lower()
        return [
            a for a in self.articles 
            if query in a.title.lower() or query in a.summary.lower()
        ]


async def main():
    """Main function"""
    aggregator = RSSAggregator()
    articles = await aggregator.fetch_all()
    
    print(f"\nTotal: {len(articles)} articles")
    
    # Search examples
    print("\nSearching for 'AI':")
    for article in aggregator.search("AI")[:5]:
        print(f"  - {article.title}")
    
    print("\nSearching for 'startup':")
    for article in aggregator.search("startup")[:5]:
        print(f"  - {article.title}")


if __name__ == "__main__":
    asyncio.run(main())
