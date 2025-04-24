# Tools/SaveHtmlTool.py

import os
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Define the Pydantic Model for the Save HTML Tool's Input
class SaveHtmlInput(BaseModel):
    """Input schema for the save_html tool."""
    html_content: str = Field(..., description="The complete HTML content as a string to be saved to Dashboard.html.")


# Define the Save HTML Tool
@tool(args_schema=SaveHtmlInput)
def save_html_dashboard(html_content: str, file_name: str = "Dashboard.html") -> str:
    """
    Saves the provided HTML content to a file named Dashboard.html (or specified filename).
    Use this tool as the final step after generating HTML content to save it as a file.
    Input includes the HTML content as a string and an optional file name (defaults to Dashboard.html).
    Returns the path to the saved file upon success.
    """
    print(f"Tool 'save_html_dashboard' called to save to file: {file_name}")

    try:
        # Define the directory where the HTML dashboard should be saved
        # Saving in the current working directory for simplicity
        save_directory = "."

        # Ensure the directory exists
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        file_path = os.path.join(save_directory, file_name)

        # Write the HTML content to the file
        # Use utf-8 encoding to handle various characters
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML dashboard successfully saved to {file_path}")
        return f"HTML dashboard successfully saved to {file_path}"

    except Exception as e:
        error_msg = f"An error occurred while saving the HTML dashboard to {file_name}: {e}"
        print(f"Error saving HTML: {error_msg}")
        return f"Failed to save HTML dashboard: {error_msg}"

# Example of how to test this tool directly using .invoke()
if __name__ == "__main__":
    print("Testing save_html_dashboard tool directly using .invoke()")

    sample_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Dashboard</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        h1 { color: green; }
    </style>
</head>
<body>
    <h1>Hello from Test Dashboard!</h1>
    <p>This is some sample HTML content.</p>
</body>
</html>
"""
    result = save_html_dashboard.invoke({"html_content": sample_html, "file_name": "TestDashboard.html"})
    print("\n--- Direct Tool Output ---")
    print(result)

    # Verify file creation (optional)
    # if os.path.exists("TestDashboard.html"):
    #     print("\nTestDashboard.html file was created.")
    # else:
    #     print("\nTestDashboard.html file was NOT created.")

