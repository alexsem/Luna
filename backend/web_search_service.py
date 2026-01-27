import logging
import asyncio
from typing import List, Dict, Any
from ddgs import DDGS

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self) -> None:
        self.max_results = 3
        logger.info("WebSearchService initialized")

    async def web_search(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo for factual information.
        Returns a list of search results with title, snippet, and URL.
        """
        return await asyncio.to_thread(self._web_search_sync, query, max_results)

    def _web_search_sync(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        try:
            with DDGS() as ddgs:
                results = []
                for result in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", "")
                    })
                
                logger.info(f"Web search for '{query}' returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

# Global instance
web_search_service = WebSearchService()
