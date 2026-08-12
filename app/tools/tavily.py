from typing import List, Dict, Any
import requests
import os
import logging
import asyncio

logger = logging.getLogger("startup-stress-test-agent.tavily")

class TavilyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = os.getenv("TAVILY_BASE_URL", "https://api.tavily.com")
        if not api_key:
            logger.warning("TAVILY_API_KEY is not set. Tavily client will not function without it.")

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Simple wrapper. Adjust endpoint/params to match Tavily API.
        """
        if not self.api_key:
            return []
        url = f"{self.base}/search"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"q": query, "limit": max_results}
        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, headers=headers, timeout=10))
            resp.raise_for_status()
            data = resp.json()
            # Expect data to be list of {"text":..., "url":...}
            return data.get("results", data)
        except Exception:
            logger.exception("Tavily search failed")
            return []
