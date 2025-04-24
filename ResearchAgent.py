# agents/search_agent.py

import os
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from Tools.SearchTool import perform_batch_web_search
from Tools.WebScraperTool import scrape_webpages
from Tools.SavePlanTool import save_plan
from Tools.SaveHtmlTool import save_html_dashboard
from datetime import date

# Get today's date
today = date.today()


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 

tools = [
    save_plan,
    perform_batch_web_search,
    scrape_webpages #,
    # save_html_dashboard
]

SysPrompt = f'''
You are a Expert Researcher AI Agent, You have tools at your disposal which will be usefull in helping you research baised on user Queries
First You need to Take The user Query and Make a plan using save_plan, this plan is a step by step breakdown of user request, like which search terms to search
You can use perform_batch_web_search and scraper_webpages multiple times baised on your query and your plan (keep it bellow 3 usage at all cost)

Your final text output should just be a well structured text that will be shown to the user, this will be used to share text responce to the user

if you get an error from anytool just asume its down and use your knowledge to answer user, dont call the tool again and again.

dont use any time period in your terms if the user didnt specify as you were trained a long time ago, what you think to be today was years ago, your knowlege cutoff was long ago so you can first use search to get refreshed and then make a plan
Today's date is:", {today}

Your output should be in extream details

Keep in mind you exist to help the user so be helpful in your tone of comuncation. You only take Research tasks and keep your tone profesional
'''

# Create the Agent Prompt
# This is a standard prompt for tool-calling agents
prompt = ChatPromptTemplate.from_messages([
    ("system", SysPrompt),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"), # This is crucial for the agent's internal state
])

# Create the Agent
# The create_tool_calling_agent automatically handles Pydantic schemas
agent = create_tool_calling_agent(llm, tools, prompt)

# Create the Agent Executor
# This is the runtime that executes the agent's steps
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- Example Usage ---
if __name__ == "__main__":
    print("Invoking agent with a query requiring both search and potentially scraping:")


    query = input("What do you want to know? - ")

    # Example prompt that might lead the agent to first search, then maybe scrape a result
    # Or you can explicitly ask it to scrape specific URLs
    response = agent_executor.invoke({
        # Replace with a real URL for testing scraping
        "input": query
    })
    print("\n--- Agent Response ---")
    print(response['output'])
