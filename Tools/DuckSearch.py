import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS # Direct library for more control
import re
import time
# from langchain_community.tools import DuckDuckGoSearchRun

# search = DuckDuckGoSearchRun()

# search.invoke("Obama's first name?")
# --- Tool 1: Web Search (DuckDuckGo) ---

def search_web_ddg(query: str, num_results: int = 7):
    """
    Performs a web search using DuckDuckGo and returns structured results.

    Args:
        query: The search query string.
        num_results: The maximum number of results to return.

    Returns:
        A list of dictionaries, each containing 'title', 'link', and 'snippet',
        or an empty list if the search fails or no results are found.
    """
    print(f"[WebSearchTool] Searching for: '{query}' (max {num_results} results)")
    results = []
    try:
        # Use the DDGS context manager for searching
        with DDGS() as ddgs:
            # ddgs.text returns a generator of results
            search_iterator = ddgs.text(query, max_results=num_results)
            for i, r in enumerate(search_iterator):
                # The library returns results with keys 'title', 'href', 'body'.
                # Map 'href' to 'link' and 'body' to 'snippet'.
                results.append({
                    "title": r.get("title", ""),
                    "link": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
                # Safety break, though max_results should handle this
                if i >= num_results - 1:
                    break
        print(f"[WebSearchTool] Found {len(results)} results.")
        return results
    except Exception as e:
        print(f"[WebSearchTool] Error during DuckDuckGo search for '{query}': {e}")
        return [] # Return empty list on error
    
if __name__ == "__main__":
    query = input("Enter your search query: ")
    num_results = int(input("Enter the maximum number of results: "))
    results = search_web_ddg(query, num_results)
    for result in results:
        print(f"Title: {result['title']}")
        print(f"Link: {result['link']}")
        print(f"Snippet: {result['snippet']}")
        print()