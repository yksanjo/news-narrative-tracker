"""
Reddit Scraper

Scrapes posts and comments from Reddit subreddits.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    """A Reddit post"""
    post_id: str
    subreddit: str
    title: str
    content: str
    author: str
    score: int = 0
    num_comments: int = 0
    url: str
    permalink: str
    created_utc: float
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            "post_id": self.post_id,
            "subreddit": self.subreddit,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "score": self.score,
            "num_comments": self.num_comments,
            "url": self.url,
            "permalink": self.permalink,
            "created_utc": self.created_utc,
            "scraped_at": self.scraped_at.isoformat()
        }


class RedditScraper:
    """Scraper for Reddit (via old.reddit.com for simplicity)"""
    
    BASE_URL = "https://old.reddit.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    def __init__(self, timeout: int = 30):
        self.client = httpx.AsyncClient(
            headers=self.HEADERS,
            timeout=timeout,
            follow_redirects=True
        )
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def get_subreddit_posts(
        self, 
        subreddit: str, 
        limit: int = 25,
        sort: str = "hot"
    ) -> list[RedditPost]:
        """Get posts from a subreddit"""
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
        params = {"limit": min(100, limit)}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_posts(data, subreddit)
    
    async def search_subreddit(
        self, 
        subreddit: str, 
        query: str, 
        limit: int = 25
    ) -> list[RedditPost]:
        """Search within a subreddit"""
        url = f"{self.BASE_URL}/r/{subreddit}/search.json"
        params = {"q": query, "limit": min(100, limit), "sort": "relevance"}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_posts(data, subreddit)
    
    def _parse_posts(self, data: dict, subreddit: str) -> list[RedditPost]:
        """Parse Reddit API response"""
        posts = []
        
        children = data.get("data", {}).get("children", [])
        
        for child in children:
            post_data = child.get("data", {})
            
            posts.append(RedditPost(
                post_id=post_data.get("id", ""),
                subreddit=post_data.get("subreddit", subreddit),
                title=post_data.get("title", ""),
                content=post_data.get("selftext", ""),
                author=post_data.get("author", ""),
                score=post_data.get("score", 0),
                num_comments=post_data.get("num_comments", 0),
                url=post_data.get("url", ""),
                permalink=post_data.get("permalink", ""),
                created_utc=post_data.get("created_utc", 0)
            ))
        
        return posts


# Popular subreddits for tech/news
SUBREDDITS = [
    "technology", "news", "worldnews", "programming",
    "artificial", "MachineLearning", "datascience",
    "startups", "business", "cryptocurrency"
]


async def get_subreddit_posts(subreddit: str) -> list[RedditPost]:
    """Convenience function"""
    async with RedditScraper() as scraper:
        return await scraper.get_subreddit_posts(subreddit)


if __name__ == "__main__":
    import json
    import sys
    
    async def main():
        sub = sys.argv[1] if len(sys.argv) > 1 else "technology"
        
        print(f"Fetching r/{sub}...")
        posts = await get_subreddit_posts(sub)
        
        print(f"Found {len(posts)} posts:")
        for p in posts[:10]:
            print(f"  - {p.title[:60]}... ({p.score} votes)")
        
        with open(f"data/reddit_{sub}.json", "w") as f:
            json.dump([p.to_dict() for p in posts], f, indent=2)
    
    asyncio.run(main())
