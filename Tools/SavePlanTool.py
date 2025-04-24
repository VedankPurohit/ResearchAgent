# Tools/SavePlansTool.py

import os
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Define the Pydantic Model for the Save Plan Tool's Input
class SavePlanInput(BaseModel):
    """Input schema for the save_plan tool."""
    plan_content: str = Field(..., description="The well-formatted plan content as a string to be saved to Plan.md.")


# Define the Save Plan Tool
@tool(args_schema=SavePlanInput)
def save_plan(plan_content: str, file_name: str = "Plan.md") -> str:
    """
    Saves the provided plan content to a Markdown file.
    Use this tool when the agent has formulated a well-formatted plan that needs to be saved.
    Input includes the plan content as a string and an optional file name (defaults to Plan.md).
    Returns the path to the saved file upon success.
    """
    print(f"Tool 'save_plan' called to save to file: {file_name}")

    try:
        # Define the directory where the plan should be saved
        # You might want to make this configurable or relative to the project root
        save_directory = "." # Saves in the current working directory

        # Ensure the directory exists (though '.' usually does)
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        file_path = os.path.join(save_directory, file_name)

        # Write the plan content to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(plan_content)

        print(f"Plan successfully saved to {file_path}")
        return f"Plan successfully saved to {file_path}"

    except Exception as e:
        error_msg = f"An error occurred while saving the plan to {file_name}: {e}"
        print(f"Error saving plan: {error_msg}")
        return f"Failed to save plan: {error_msg}"

# Example of how to test this tool directly using .invoke()
if __name__ == "__main__":
    print("Testing save_plan tool directly using .invoke()")

    sample_plan = """
# Research Plan

1.  Identify key concepts in the user query.
2.  Use `perform_batch_web_search` for initial information gathering on key concepts.
3.  If specific URLs are mentioned, use `scrape_webpages` to get content.
4.  Synthesize gathered information.
5.  Identify any data suitable for visualization.
6.  If data exists, use `generate_plot` to create images.
7.  Format the synthesized text and image paths.
8.  Use `generate_html_output` to create the final report.
9.  Save this plan using `save_plan`.
"""
    result = save_plan.invoke({"plan_content": sample_plan})
    print("\n--- Direct Tool Output ---")
    print(result)

    # Verify file creation (optional)
    # if os.path.exists("TestPlan.md"):
    #     print("\nTestPlan.md file was created.")
    # else:
    #     print("\nTestPlan.md file was NOT created.")

