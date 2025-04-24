
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import DuckDuckGoSearchResults
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Instantiate DuckDuckGo tools
# DuckDuckGoSearchRun is typically for a single, concise answer (used by search.run)
# DuckDuckGoSearchResults is for getting a list of search results (used by searchWider.run or batch)
search = DuckDuckGoSearchRun()
searchWider = DuckDuckGoSearchResults()

def searchTopics(queryList: list, num_results: int = 5):
    """
    Performs a web search using DuckDuckGo and returns structured results.
    input should be a list of search queries, even if its only one search string, you need to put it in as a list

    Args:
        queryList: List of search queries strings.
        num_results: The maximum number of results to return for each query (used by searchWider.batch).

    Returns:
        A formatted string containing search results from the batch.
    """
    print(f"Executing searchTopics for queries: {queryList} with num_results={num_results}")
    output = ""
    try:
        # Use search.batch for headline results for each query in the list
        Headline = search.batch(queryList)
        # Use searchWider.batch for more detailed results for each query
        # Pass num_results to control how many results searchWider returns per query
        AdvSearch = searchWider.batch(queryList, num_results=num_results)

        # Ensure both lists have the same length as queryList for safe iteration
        # This handles cases where a search might fail for one query
        min_len = min(len(queryList), len(Headline), len(AdvSearch))

        for i in range(min_len):
            headline_result_str = str(Headline[i]) if i < len(Headline) else "No headline result found."
            advsearch_result_str = str(AdvSearch[i]) if i < len(AdvSearch) else "No wider result found."

            output += f"--- Results for Query: '{queryList[i]}' ---\n"
            output += f"Top Answer - {headline_result_str}"
            output += "\n"
            output += f"Other Sources - {advsearch_result_str}"
            if i < min_len - 1:
                output += "\n\n" # Add a separator between results for different queries

        if not output and queryList: # Handle case where no results were found for any query
             output = f"No search results found for the queries: {', '.join(queryList)}"


    except Exception as e:
        # Catch any exceptions during the search process
        output = f"An error occurred during batch search: {e}"
        print(f"Error during searchTopics execution: {e}")

    return output

# Define the Pydantic Model for the Search Tool's Input
class SearchTopicsInput(BaseModel):
    """Input schema for the perform_batch_web_search tool."""
    queryList: List[str] = Field(..., description="A list of search queries to perform simultaneously.")


# Define the Search Tool
@tool(args_schema=SearchTopicsInput)
def perform_batch_web_search(queryList: List[str]) -> str:
    """
    Searches the web for multiple topics simultaneously using a list of queries.
    Use this tool when you need to find information on several related or distinct subjects
    in one go. Input must be a list of strings, where each string is a search query.
    """
    print(f"Tool 'perform_batch_web_search' called with queryList: {queryList}")
    # Call the core search logic with the queryList received as a keyword argument
    # Pass num_results if it was added to the Pydantic model and received here
    return searchTopics(queryList=queryList)

# Example of how to use the tool directly (optional, for testing)
# if __name__ == "__main__":
#     print(perform_batch_web_search(queryList=["latest AI news", "Langchain updates"]))
