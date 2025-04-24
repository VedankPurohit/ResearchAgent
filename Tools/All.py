import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS # Direct library for more control
import re
import time

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

# --- Tool 2: Web Scraper ---

def scrape_website_text(url: str, timeout: int = 10):
    """
    Scrapes the main text content from a given URL using requests and BeautifulSoup.
    Attempts basic cleaning and focuses on potentially relevant content tags.

    Args:
        url: The URL of the website to scrape.
        timeout: Request timeout in seconds.

    Returns:
        The extracted text content as a single string, or None if scraping fails.
    """
    print(f"[WebScraperTool] Attempting to scrape: {url}")
    headers = {
        # Standard User-Agent to avoid blocking
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # Check content type - proceed only if it's likely HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            print(f"[WebScraperTool] Warning: Content type for {url} is '{content_type}', not text/html. Skipping.")
            return None

        # Use lxml for parsing speed if available
        soup = BeautifulSoup(response.content, 'lxml') # 'html.parser' is a fallback

        # Remove common non-content tags (scripts, styles, nav, footers, etc.)
        for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'button']):
            tag.decompose()

        # Attempt to find common main content containers
        main_content = soup.find('article') or \
                       soup.find('main') or \
                       soup.find(id='content') or \
                       soup.find(id='main-content') or \
                       soup.find(class_='post-content') or \
                       soup.find(class_='entry-content') or \
                       soup.find(role='main') # Add role='main'

        body = main_content if main_content else soup.find('body') # Fallback to body if no main container found

        if not body:
             print(f"[WebScraperTool] Could not find body tag for {url}. Strange HTML.")
             return None # Should not happen often

        # Get all text, separated by space, and strip leading/trailing whitespace from each piece
        all_text = body.get_text(separator=' ', strip=True)

        # Basic cleaning: remove excessive whitespace and newline characters
        cleaned_text = re.sub(r'\s+', ' ', all_text).strip()

        # Add a check for minimal meaningful content length
        if len(cleaned_text) < 150: # Increased threshold slightly
             print(f"[WebScraperTool] Warning: Extracted content from {url} is very short ({len(cleaned_text)} chars). Might be incomplete or a stub page.")
             # Return short content anyway, let the analyzer decide relevance

        print(f"[WebScraperTool] Successfully scraped ~{len(cleaned_text)} characters from {url}")
        return cleaned_text

    except requests.exceptions.Timeout:
        print(f"[WebScraperTool] Error: Request timed out for {url} after {timeout} seconds.")
        return None
    except requests.exceptions.RequestException as e:
        # Handles connection errors, invalid URLs, HTTP errors etc.
        print(f"[WebScraperTool] Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        # Catch other potential errors during parsing etc.
        print(f"[WebScraperTool] Error scraping content from {url}: {e}")
        return None

# --- Tool 3: News Tool ---

def get_latest_news_text(topic: str, num_articles: int = 3, max_chars_per_article: int = 4000):
    """
    Searches for the latest news on a topic using the search tool, scrapes the top
    articles using the scraper tool, combines the text, and returns it.

    Args:
        topic: The news topic to search for (e.g., "latest AI developments").
        num_articles: The maximum number of articles to scrape and combine.
        max_chars_per_article: Approximate maximum characters to include per article to manage context length.

    Returns:
        A single string containing the combined text from the scraped articles,
        separated by source URL markers, or None if no suitable articles could be processed.
    """
    print(f"[NewsTool] Getting latest news for: '{topic}' (target: {num_articles} articles)")
    # Make the search query more specific for news
    search_query = f"latest news {topic}"
    # Fetch slightly more results than needed to allow for scraping failures
    search_results = search_web_ddg(search_query, num_results=num_articles + 2)

    if not search_results:
        print(f"[NewsTool] No search results found for '{search_query}'.")
        return None

    combined_text = ""
    articles_processed_count = 0
    urls_processed = set() # Keep track of processed URLs to avoid duplicates if search returns similar links

    print(f"[NewsTool] Found {len(search_results)} potential articles. Attempting to scrape top {num_articles}.")

    for result in search_results:
        if articles_processed_count >= num_articles:
            break # Stop once we have enough articles

        url = result.get("link")
        title = result.get("title", "Untitled Article")

        if url and url not in urls_processed:
            urls_processed.add(url) # Mark URL as attempted
            print(f"[NewsTool] -> Scraping '{title}': {url}")
            # Add a small delay between requests to be polite to servers
            time.sleep(0.5)
            scraped_content = scrape_website_text(url)

            if scraped_content:
                # Truncate content if it exceeds the character limit
                truncated_content = scraped_content[:max_chars_per_article]
                if len(scraped_content) > max_chars_per_article:
                     truncated_content += "..." # Indicate truncation
                     print(f"[NewsTool]   - Truncated content to {max_chars_per_article} chars.")

                # Add separator, source URL, and content
                combined_text += f"--- News Article Source: {url} ---\n\n"
                combined_text += truncated_content
                combined_text += "\n\n---\n\n" # Clearer separator between articles
                articles_processed_count += 1
                print(f"[NewsTool]   + Successfully scraped and added content from {url}")
            else:
                print(f"[NewsTool]   - Failed to scrape content from {url}")
        elif not url:
             print(f"[NewsTool]   - Skipping result with no URL: {title}")
        # Implicit else: URL already processed, skip.

    if articles_processed_count == 0:
        print(f"[NewsTool] Failed to scrape usable content from any of the top articles found for '{topic}'.")
        return None

    print(f"[NewsTool] Successfully combined text from {articles_processed_count} articles for topic '{topic}'. Total length: ~{len(combined_text)} chars.")
    return combined_text.strip()


# --- Example Usage (for testing) ---


if __name__ == "__main__":
    print(scrape_website_text("https://huggingface.co/blog/gemma3"))


if __name__ == "1__main__":
    print("--- Testing Web Search Tool ---")
    search_test_query = "What is LangGraph?"
    search_results = search_web_ddg(search_test_query, num_results=3)
    if search_results:
        for res in search_results:
            print(f"  Title: {res['title']}")
            print(f"  Link: {res['link']}")
            print(f"  Snippet: {res['snippet'][:100]}...") # Print short snippet
            print("-" * 10)
    else:
        print(f"No results for '{search_test_query}'")

    print("\n--- Testing Web Scraper Tool ---")
    # Use a known, generally scrape-friendly page if possible for testing
    # Or use one of the links found above if the search worked
    scrape_test_url = None
    if search_results and search_results[0]['link']:
       scrape_test_url = search_results[0]['link']
       # Example fallback URL if search failed or returned unusable links:
       # scrape_test_url = "https://lilianweng.github.io/posts/2023-06-23-agent/" # Known good blog post
    else:
       scrape_test_url = "https://www.example.com" # Very basic fallback

    if scrape_test_url:
        scraped_text = scrape_website_text(scrape_test_url)
        if scraped_text:
            print(f"Scraped text from {scrape_test_url} (first 500 chars):\n{scraped_text[:500]}...")
        else:
            print(f"Failed to scrape {scrape_test_url}")
    else:
        print("Cannot test scraper without a valid URL.")


    print("\n--- Testing News Tool ---")
    news_test_topic = "AI safety research"
    news_text = get_latest_news_text(news_test_topic, num_articles=2) # Request fewer for testing
    if news_text:
        print(f"\nCombined News Text for '{news_test_topic}' (first 1000 chars):\n{news_text[:1000]}...")
    else:
        print(f"Could not retrieve news for '{news_test_topic}'")

    print("\n--- Testing News Tool - Edge Case (Difficult Topic) ---")
    news_test_topic_fail = "asdfqwerlkjhzxcv" # Unlikely to have news
    news_text_fail = get_latest_news_text(news_test_topic_fail, num_articles=2)
    if news_text_fail:
        print(f"\nCombined News Text for '{news_test_topic_fail}' (first 1000 chars):\n{news_text_fail[:1000]}...")
    else:
        print(f"Correctly handled non-existent news topic '{news_test_topic_fail}'")