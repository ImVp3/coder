from langgraph.prebuilt import create_react_agent
from .utils.agent_prompt_template import RESEARCH_TEMPLATE

def create_research_agent(search_tool, model):
    """
    Creates a research agent that can perform web searches and respond to a supervisor.
    """
    return create_react_agent(
        model = model,
        tools = [search_tool],
        prompt= RESEARCH_TEMPLATE,
        name  = "research_agent",
    )
