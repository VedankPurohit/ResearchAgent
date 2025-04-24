# Tools/web_scraping_tools.py

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Import necessary libraries for web scraping
import requests
from bs4 import BeautifulSoup
import re # Import regex module

def scrape_website_text(url: str, timeout: int = 10) -> Optional[str]:
    """
    Scrapes the main text content from a given URL using requests and BeautifulSoup.
    Attempts basic cleaning and focuses on potentially relevant content tags.

    Args:
        url: The URL of the website to scrape.
        timeout: Request timeout in seconds.

    Returns:
        The extracted text content as a single string, or None if scraping fails or content is unsuitable.
    """
    print(f"[WebScraperTool] Attempting to scrape: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            print(f"[WebScraperTool] Warning: Content type for {url} is '{content_type}', not text/html. Skipping.")
            return None

        # Use lxml for parsing speed if available, fallback to html.parser
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except ImportError:
             print("[WebScraperTool] lxml not found, falling back to html.parser")
             soup = BeautifulSoup(response.content, 'html.parser')


        # Remove common non-content tags
        for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'button', 'img', 'svg', 'canvas']): # Added img, svg, canvas
            tag.decompose()

        # Attempt to find common main content containers
        main_content = soup.find('article') or \
                       soup.find('main') or \
                       soup.find(id='content') or \
                       soup.find(id='main-content') or \
                       soup.find(class_='post-content') or \
                       soup.find(class_='entry-content') or \
                       soup.find(role='main')

        body = main_content if main_content else soup.find('body')

        if not body:
            print(f"[WebScraperTool] Could not find body tag for {url}. Strange HTML.")
            return None

        # Get all text, separated by space, and strip leading/trailing whitespace from each piece
        all_text = body.get_text(separator=' ', strip=True)

        # Basic cleaning: remove excessive whitespace and newline characters
        cleaned_text = re.sub(r'\s+', ' ', all_text).strip()

        # Add a check for minimal meaningful content length
        if len(cleaned_text) < 150:
            print(f"[WebScraperTool] Warning: Extracted content from {url} is very short ({len(cleaned_text)} chars) from {url}. Might be incomplete or a stub page.")
            # Return short content anyway, let the analyzer decide relevance

        print(f"[WebScraperTool] Successfully scraped ~{len(cleaned_text)} characters from {url}")
        return cleaned_text

    except requests.exceptions.Timeout:
        print(f"[WebScraperTool] Error: Request timed out for {url} after {timeout} seconds.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[WebScraperTool] Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        print(f"[WebScraperTool] Error scraping content from {url}: {e}")
        return None

# Define the Pydantic Model for the Web Scraping Tool's Input
class ScrapeUrlsInput(BaseModel):
    """Input schema for the scrape_webpages tool."""
    urls: List[str] = Field(..., description="A list of URLs to scrape the text content from.")
    # You could add a timeout parameter here if you want the agent to control it
    # timeout: int = Field(10, description="Request timeout in seconds for each URL.")


# Define the Web Scraping Tool
@tool(args_schema=ScrapeUrlsInput)
def scrape_webpages(urls: List[str]) -> str:
    """
    Scrapes the text content from a list of specified URLs.
    Use this tool when you have specific URLs you need to read the content of.
    Input must be a list of strings, where each string is a valid URL.
    Returns the scraped content for each URL, or an error message if scraping fails.
    """
    print(f"Tool 'scrape_webpages' called with URLs: {urls}")
    results = []
    for url in urls:
        # You could pass the timeout here if you added it to the Pydantic model
        content = scrape_website_text(url)
        if content:
            results.append(f"--- Content from {url} ---\n{content}\n")
        else:
            results.append(f"--- Failed to scrape content from {url} ---\n")

    if not results:
        return "No URLs were provided to scrape."

    # Join the results for all URLs into a single output string
    return "\n".join(results)

# Example of how to use the tool directly (optional, for testing)
# if __name__ == "__main__":
#     # Replace with actual URLs you want to test scraping
#     print(scrape_webpages(urls=["https://example.com", "https://www.google.com"]))

