from typing import List, Dict, Any
from app.tools.tavily import TavilyClient
from app.tools.firecrawl import FirecrawlClient
import os
import logging
from fastapi import Depends

logger = logging.getLogger("startup-stress-test-agent.search")

class SearchService:
    def __init__(self, tavily_client: TavilyClient, firecrawl_client: FirecrawlClient):
        self.tavily = tavily_client
        self.firecrawl = firecrawl_client

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        1) Query Tavily
        2) If results insufficient, crawl top result(s) with Firecrawl
        3) Clean text, dedupe, and return concise snippets with URLs
        """
        results = await self.tavily.search(query, max_results=max_results)
        if not results or len(results) < 3:
            # try crawling top domains to enrich
            top_urls = [r["url"] for r in results[:3]] if results else []
            crawled = []
            for url in top_urls:
                try:
                    c = await self.firecrawl.crawl(url)
                    crawled.extend(c)
                except Exception:
                    logger.exception("Firecrawl failed for %s", url)
            # merge
            results.extend(crawled)
        # simple dedupe by url
        seen = set()
        cleaned = []
        for r in results:
            url = r.get("url")
            if url in seen:
                continue
            seen.add(url)
            cleaned.append({"text": self._clean_text(r.get("text", "")), "url": url})
        return cleaned[:max_results]

    def _clean_text(self, text: str) -> str:
        # naive cleaning
        return " ".join(text.strip().split())

# Dependency provider
def get_search_service() -> SearchService:
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
    firecrawl_client = FirecrawlClient(api_key=os.getenv("FIRECRAWL_API_KEY", ""))
    return SearchService(tavily_client=tavily_client, firecrawl_client=firecrawl_client)
