# Tools/web_scraping_tools.py

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Import necessary libraries for web scraping
import requests
from bs4 import BeautifulSoup
import re # Import regex module
import urllib.robotparser # Import robotparser
from urllib.parse import urlparse # Import urlparse

rp = urllib.robotparser.RobotFileParser()

def is_scraping_allowed(url: str, user_agent: str = '*') -> bool:
    """
    Checks if scraping is allowed for a given URL and user agent based on robots.txt.

    Args:
        url: The URL to check.
        user_agent: The user agent string to use for the check (defaults to '*').

    Returns:
        True if scraping is allowed, False otherwise.
    """
    try:
        # Parse the URL to get the base URL (scheme and netloc)
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_txt_url = f"{base_url}/robots.txt"

        # Set the robots.txt URL for the parser
        rp.set_url(robots_txt_url)

        # Read the robots.txt file from the web
        # This might raise exceptions if robots.txt is not accessible
        try:
            rp.read()
        except Exception as e:
            print(f"[WebScraperTool] Warning: Could not read robots.txt from {robots_txt_url}. Assuming allowed. Error: {e}")
            # If robots.txt cannot be read, it's generally safer to assume crawling is allowed
            # as per the standard; however, for a tool, you might decide to block.
            # Let's assume allowed for now, but print a warning.
            return True

        # Check if the user agent is allowed to fetch the URL path
        path = parsed_url.path if parsed_url.path else '/' # Use '/' if path is empty
        if parsed_url.query: # Include query parameters if they exist
             path += '?' + parsed_url.query

        allowed = rp.can_fetch(user_agent, path)

        if not allowed:
            print(f"[WebScraperTool] Scraping disallowed by robots.txt for {url} (User Agent: {user_agent}).")

        return allowed

    except Exception as e:
        print(f"[WebScraperTool] Error checking robots.txt for {url}: {e}. Assuming allowed.")
        # If any error occurs during the robots.txt check, assume allowed
        return True


def scrape_website_text(url: str, timeout: int = 10) -> Optional[str]:
    """
    Scrapes the main text content from a given URL using requests and BeautifulSoup,
    after checking robots.txt.

    Args:
        url: The URL of the website to scrape.
        timeout: Request timeout in seconds.

    Returns:
        The extracted text content as a single string, or None if scraping fails,
        content is unsuitable, or scraping is disallowed by robots.txt.
    """
    # --- Add robots.txt check ---
    if not is_scraping_allowed(url):
        return f"Scraping of {url} is disallowed by robots.txt." # Return a specific message

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
    Returns the scraped content for each URL, or an error message if scraping fails or is disallowed.
    """
    print(f"Tool 'scrape_webpages' called with URLs: {urls}")
    results = []
    for url in urls:
        # Call the scraping function which now includes the robots.txt check
        content = scrape_website_text(url)
        if content and "disallowed by robots.txt" not in content: # Check if content is not the disallowed message
            results.append(f"--- Content from {url} ---\n{content}\n")
        elif content and "disallowed by robots.txt" in content:
             results.append(f"--- Scraping disallowed for {url} ---\n")
        else:
            results.append(f"--- Failed to scrape content from {url} ---\n")

    if not results:
        return "No URLs were provided to scrape."

    # Join the results for all URLs into a single output string
    return "\n".join(results)

# Example of how to use the tool directly (optional, for testing)
if __name__ == "__main__":
    print("Testing scrape_webpages tool directly using .invoke()")
    # Replace with actual URLs you want to test scraping
    # Call the tool using .invoke() and pass arguments as a dictionary
    # Example URLs: one allowed, one potentially disallowed (replace with real examples)
    test_urls = [
        "https://www.example.com", # Usually allowed
        "https://www.google.com/search?q=test", # Often disallowed for scraping
        "https://medium.com/data-scientists-from-future/agentic-frameworks-what-why-who-when-where-and-how-874272b4812a",
        "https://huggingface.co/blog/gemma3"
    ]
    result = scrape_webpages.invoke({"urls": test_urls})
    print("\n--- Direct Tool Output ---")
    print(result)
