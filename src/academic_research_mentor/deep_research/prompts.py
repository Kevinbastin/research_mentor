"""LangGraph state definitions for the Deep Research agent.

Based on Open Deep Research: https://github.com/langchain-ai/open_deep_research
"""

import operator
from typing import Annotated, Optional, List

from langchain_core.messages import MessageLikeRepresentation
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


###################
# Structured Outputs (Tool Schemas)
###################

class ConductResearch(BaseModel):
    """Call this tool to conduct research on a specific topic."""
    research_topic: str = Field(
        description="The topic to research. Should be a single topic, and should be described in high detail (at least a paragraph).",
    )


class ResearchComplete(BaseModel):
    """Call this tool to indicate that the research is complete."""
    pass


class Summary(BaseModel):
    """Research summary with key findings."""
    summary: str
    key_excerpts: str


class ClarifyWithUser(BaseModel):
    """Model for user clarification requests."""
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )
    verification: str = Field(
        description="Verify message that we will start research after the user has provided the necessary information.",
    )


class ResearchQuestion(BaseModel):
    """Research question and brief for guiding research."""
    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )


###################
# State Definitions
###################

def override_reducer(current_value, new_value):
    """Reducer function that allows overriding values in state."""
    if isinstance(new_value, dict) and new_value.get("type") == "override":
        return new_value.get("value", new_value)
    else:
        return operator.add(current_value, new_value)


class AgentInputState(MessagesState):
    """Input state is only 'messages'."""
    pass


class AgentState(MessagesState):
    """Main agent state containing messages and research data."""
    
    supervisor_messages: Annotated[List[MessageLikeRepresentation], override_reducer]
    research_brief: Optional[str] = None
    raw_notes: Annotated[List[str], override_reducer] = []
    notes: Annotated[List[str], override_reducer] = []
    final_report: str = ""


class SupervisorState(MessagesState):
    """State for the supervisor that manages research tasks."""
    
    supervisor_messages: Annotated[List[MessageLikeRepresentation], override_reducer]
    research_brief: str = ""
    notes: Annotated[List[str], override_reducer] = []
    research_iterations: int = 0
    raw_notes: Annotated[List[str], override_reducer] = []


class ResearcherState(MessagesState):
    """State for individual researchers conducting research."""
    
    researcher_messages: Annotated[List[MessageLikeRepresentation], operator.add]
    tool_call_iterations: int = 0
    research_topic: str = ""
    compressed_research: str = ""
    raw_notes: Annotated[List[str], override_reducer] = []


class ResearcherOutputState(BaseModel):
    """Output state from individual researchers."""
    
    compressed_research: str
    raw_notes: List[str] = []

   

state.py

"""Prompts for the Deep Research agent.

Based on Open Deep Research: https://github.com/langchain-ai/open_deep_research
"""

from datetime import datetime


def get_today_str() -> str:
    """Get today's date as a formatted string."""
    return datetime.now().strftime("%B %d, %Y")


# Clarification prompt
CLARIFY_WITH_USER_INSTRUCTIONS = """You are a research assistant helping to clarify a research request.

Analyze the user's request and determine if you need any clarification before starting research.
If the request is clear enough to proceed, set need_clarification to false.
If you need more details, ask a focused question.

User request: {user_request}
"""

# Research brief generation
RESEARCH_BRIEF_PROMPT = """You are a senior research analyst. Based on the user's request, create a clear research brief.

User request: {user_request}

Create a research brief that:
1. Clearly states the research objective
2. Identifies key areas to investigate
3. Specifies the expected deliverables

Be concise but comprehensive.
"""

# Lead researcher (supervisor) prompt
LEAD_RESEARCHER_PROMPT = """You are the lead researcher coordinating a team of research specialists.
Today's date is {date}.

Research Brief:
{research_brief}

Your role:
1. Break down the research into manageable sub-topics
2. Delegate research tasks using the ConductResearch tool
3. Review findings and identify gaps
4. Call ResearchComplete when sufficient research has been gathered

Current findings:
{notes}

Guidelines:
- Delegate 2-5 research tasks at a time for parallel execution
- Each research topic should be specific and focused
- After reviewing results, decide if more research is needed
- Maximum {max_iterations} research iterations allowed
"""

# Individual researcher prompt
RESEARCH_SYSTEM_PROMPT = """You are a specialist researcher focused on gathering comprehensive information.
Today's date is {date}.

Your research topic: {research_topic}

Instructions:
1. Use the search tool to find relevant information
2. Take detailed notes on important findings
3. Include sources and citations where possible
4. Focus on factual, verifiable information
5. Maximum {max_tool_calls} search iterations allowed

Be thorough but efficient in your research.
"""

# Compress research findings
COMPRESS_RESEARCH_SYSTEM_PROMPT = """You are a research analyst specializing in synthesizing information.

Compress the research findings into a clear, organized summary.
Preserve key facts, statistics, and citations.
Remove redundant information.
Organize by theme or relevance.
"""

COMPRESS_RESEARCH_HUMAN_MESSAGE = """Research Topic: {research_topic}

Raw Research Findings:
{raw_findings}

Compress these findings into a concise summary that preserves the most important information.
"""

# Final report generation
FINAL_REPORT_PROMPT = """You are an expert research report writer.
Today's date is {date}.

Research Brief:
{research_brief}

Conversation Context:
{messages}

Research Findings:
{findings}

Write a comprehensive, well-structured research report that:
1. Has a clear executive summary
2. Organizes findings by theme
3. Includes relevant citations and sources
4. Provides actionable insights
5. Identifies gaps or areas for further research

Format the report in clean Markdown with proper headings.
"""

# Summarization prompt for search results
SUMMARIZE_SEARCH_RESULTS_PROMPT = """Summarize the following search results for the research topic.

Research Topic: {topic}

Search Results:
{results}

Provide a concise summary highlighting:
1. Key facts and findings
2. Relevant sources
3. Any conflicting information
"""