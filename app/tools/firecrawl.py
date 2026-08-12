from typing import List, Dict, Any
import requests
import os
import logging
import asyncio

logger = logging.getLogger("startup-stress-test-agent.firecrawl")

class FirecrawlClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.com")
        if not api_key:
            logger.warning("FIRECRAWL_API_KEY is not set. Firecrawl client may not function without it.")

    async def crawl(self, url: str) -> List[Dict[str, Any]]:
        """
        Crawl a URL and return snippets. Adjust to match Firecrawl API.
        """
        if not self.api_key:
            return []
        api_url = f"{self.base}/crawl"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"url": url}
        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(None, lambda: requests.post(api_url, json=payload, headers=headers, timeout=15))
            resp.raise_for_status()
            data = resp.json()
            return data.get("snippets", [])
        except Exception:
            logger.exception("Firecrawl crawl failed for %s", url)
            return []
