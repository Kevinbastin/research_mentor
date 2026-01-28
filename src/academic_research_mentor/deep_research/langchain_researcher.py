"""LangGraph Deep Researcher - Full implementation with supervisor/researcher pattern.

Based on Open Deep Research: https://github.com/langchain-ai/open_deep_research
Adapted for METIS with local Ollama support for RTX 5090.
Uses FREE providers only (ArXiv, Semantic Scholar, Ollama).
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, List

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    get_buffer_string,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from .state import (
    AgentInputState,
    AgentState,
    ConductResearch,
    ResearchComplete,
    ResearcherState,
    SupervisorState,
)
from .prompts import (
    CLARIFY_WITH_USER_INSTRUCTIONS,
    RESEARCH_BRIEF_PROMPT,
    LEAD_RESEARCHER_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    COMPRESS_RESEARCH_SYSTEM_PROMPT,
    COMPRESS_RESEARCH_HUMAN_MESSAGE,
    FINAL_REPORT_PROMPT,
    SUMMARIZE_SEARCH_RESULTS_PROMPT,
    get_today_str,
)


@dataclass
class DeepResearchConfig:
    """Configuration for deep research workflow."""
    
    # General settings
    max_structured_output_retries: int = 3
    allow_clarification: bool = True
    max_concurrent_research_units: int = 5
    
    # Research settings
    max_researcher_iterations: int = 6
    max_react_tool_calls: int = 10
    search_api: str = "arxiv"  # arxiv (FREE), semantic_scholar (FREE), none
    
    # Model settings - defaults for local Ollama (FREE)
    summarization_model: str = field(default_factory=lambda: os.getenv(
        "RESEARCH_SUMMARIZATION_MODEL", 
        "ollama/qwen2.5:14b" if os.getenv("LLM_PROVIDER") == "ollama" else "openai/gpt-4o-mini"
    ))
    research_model: str = field(default_factory=lambda: os.getenv(
        "RESEARCH_DEEP_MODEL",
        "ollama/qwen2.5:14b" if os.getenv("LLM_PROVIDER") == "ollama" else "openai/gpt-4o"
    ))
    compression_model: str = field(default_factory=lambda: os.getenv(
        "RESEARCH_COMPRESSION_MODEL",
        "ollama/qwen2.5:14b" if os.getenv("LLM_PROVIDER") == "ollama" else "openai/gpt-4o-mini"
    ))
    final_report_model: str = field(default_factory=lambda: os.getenv(
        "RESEARCH_REPORT_MODEL",
        "ollama/qwen2.5:14b" if os.getenv("LLM_PROVIDER") == "ollama" else "openai/gpt-4o"
    ))
    
    # Token limits
    summarization_max_tokens: int = 8192
    research_max_tokens: int = 10000
    compression_max_tokens: int = 8192
    final_report_max_tokens: int = 10000
    max_content_length: int = 50000
    
    @classmethod
    def from_env(cls) -> "DeepResearchConfig":
        """Create configuration from environment variables."""
        return cls()


def get_configurable_model():
    """Initialize a configurable model that supports both cloud and local providers."""
    def _init_model(model_str: str, **kwargs):
        """Initialize model from 'provider/model' string format."""
        if "/" in model_str:
            provider, model = model_str.split("/", 1)
        else:
            provider, model = "openai", model_str
        
        # Handle Ollama specially (FREE, local)
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model,
                base_url=base_url,
                **kwargs
            )
        else:
            # Use LangChain's universal init
            return init_chat_model(
                model=model,
                model_provider=provider,
                **kwargs
            )
    return _init_model


# Global configurable model factory
configurable_model = get_configurable_model()


def get_search_tool(search_api: str = "arxiv"):
    """Get the appropriate search tool based on configuration.
    
    Uses FREE providers by default:
    - arxiv: Free academic paper search (no API key needed)
    - semantic_scholar: Free academic paper search (rate limited but free)
    - none: Disable search
    """
    if search_api == "arxiv":
        # Use our free ArXiv provider
        try:
            from ..literature_review.providers import get_registry
            registry = get_registry()
            arxiv = registry.get("arxiv")
            if arxiv and arxiv.is_available():
                return arxiv
        except Exception as e:
            print(f"ArXiv provider error: {e}")
        return None
    elif search_api == "semantic_scholar":
        # Use free Semantic Scholar provider
        try:
            from ..literature_review.providers import get_registry
            registry = get_registry()
            ss = registry.get("semantic_scholar")
            if ss and ss.is_available():
                return ss
        except Exception as e:
            print(f"Semantic Scholar provider error: {e}")
        return None
    elif search_api == "tavily":
        # Tavily requires paid API key - skip if not configured
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("TAVILY_API_KEY not set, falling back to ArXiv (FREE)")
            return get_search_tool("arxiv")
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            return TavilySearchResults(
                max_results=10,
                include_raw_content=True,
            )
        except ImportError:
            return get_search_tool("arxiv")
    elif search_api == "none":
        return None
    else:
        # Unknown API, fall back to ArXiv (FREE)
        return get_search_tool("arxiv")


###################
# Researcher Subgraph
###################

async def researcher(state: ResearcherState, config: RunnableConfig) -> Command:
    """Individual researcher that conducts focused research on a topic."""
    cfg = DeepResearchConfig.from_env()
    
    # Get research model
    model = configurable_model(
        cfg.research_model,
        max_tokens=cfg.research_max_tokens,
    )
    
    # Get search tool
    search_tool = get_search_tool(cfg.search_api)
    if search_tool:
        model = model.bind_tools([search_tool])
    
    # Build messages
    messages = state.get("researcher_messages", [])
    if not messages:
        messages = [
            SystemMessage(content=RESEARCH_SYSTEM_PROMPT.format(
                date=get_today_str(),
                research_topic=state.get("research_topic", ""),
                max_tool_calls=cfg.max_react_tool_calls,
            )),
            HumanMessage(content=f"Research topic: {state.get('research_topic', '')}")
        ]
    
    # Check iteration limit
    iterations = state.get("tool_call_iterations", 0)
    if iterations >= cfg.max_react_tool_calls:
        return Command(
            goto=END,
            update={"researcher_messages": messages}
        )
    
    # Get model response
    response = await model.ainvoke(messages)
    messages.append(response)
    
    # Handle tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            try:
                if search_tool:
                    result = await search_tool.ainvoke(tool_call["args"])
                    messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"],
                    ))
            except Exception as e:
                messages.append(ToolMessage(
                    content=f"Error: {e}",
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"],
                ))
        
        return Command(
            goto="researcher",
            update={
                "researcher_messages": messages,
                "tool_call_iterations": iterations + 1,
            }
        )
    
    # Research complete - extract notes
    raw_notes = [response.content] if response.content else []
    
    return Command(
        goto="compress",
        update={
            "researcher_messages": messages,
            "raw_notes": raw_notes,
        }
    )


async def compress_research(state: ResearcherState, config: RunnableConfig) -> dict:
    """Compress research findings into a concise summary."""
    cfg = DeepResearchConfig.from_env()
    
    model = configurable_model(
        cfg.compression_model,
        max_tokens=cfg.compression_max_tokens,
    )
    
    raw_notes = state.get("raw_notes", [])
    research_topic = state.get("research_topic", "")
    
    if not raw_notes:
        return {"compressed_research": "No research findings to compress."}
    
    messages = [
        SystemMessage(content=COMPRESS_RESEARCH_SYSTEM_PROMPT),
        HumanMessage(content=COMPRESS_RESEARCH_HUMAN_MESSAGE.format(
            research_topic=research_topic,
            raw_findings="\n\n".join(raw_notes),
        ))
    ]
    
    response = await model.ainvoke(messages)
    
    return {
        "compressed_research": response.content,
        "raw_notes": raw_notes,
    }


# Build researcher subgraph
researcher_builder = StateGraph(ResearcherState)
researcher_builder.add_node("researcher", researcher)
researcher_builder.add_node("compress", compress_research)
researcher_builder.add_edge(START, "researcher")
researcher_builder.add_edge("compress", END)
researcher_subgraph = researcher_builder.compile()


###################
# Supervisor Subgraph
###################

async def supervisor(state: SupervisorState, config: RunnableConfig) -> Command:
    """Supervisor that delegates research tasks and coordinates findings."""
    cfg = DeepResearchConfig.from_env()
    
    model = configurable_model(
        cfg.research_model,
        max_tokens=cfg.research_max_tokens,
    )
    
    # Bind research tools
    model = model.bind_tools([ConductResearch, ResearchComplete])
    
    # Build prompt
    notes = state.get("notes", [])
    notes_str = "\n".join(notes) if notes else "No research conducted yet."
    
    messages = state.get("supervisor_messages", [])
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages.insert(0, SystemMessage(content=LEAD_RESEARCHER_PROMPT.format(
            date=get_today_str(),
            research_brief=state.get("research_brief", ""),
            notes=notes_str,
            max_iterations=cfg.max_researcher_iterations,
        )))
    
    # Check iteration limit
    iterations = state.get("research_iterations", 0)
    if iterations >= cfg.max_researcher_iterations:
        return Command(
            goto=END,
            update={"notes": notes}
        )
    
    response = await model.ainvoke(messages)
    messages.append(response)
    
    # Handle tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        return Command(
            goto="supervisor_tools",
            update={
                "supervisor_messages": messages,
                "research_iterations": iterations + 1,
            }
        )
    
    # No tool calls - end supervision
    return Command(
        goto=END,
        update={
            "supervisor_messages": messages,
            "notes": notes,
        }
    )


async def supervisor_tools(state: SupervisorState, config: RunnableConfig) -> Command:
    """Execute supervisor tool calls (delegate to researchers)."""
    cfg = DeepResearchConfig.from_env()
    
    messages = state.get("supervisor_messages", [])
    if not messages:
        return Command(goto=END)
    
    last_message = messages[-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return Command(goto=END)
    
    tool_messages = []
    new_notes = []
    
    # Separate tool calls by type
    research_calls = []
    complete_calls = []
    
    for tc in last_message.tool_calls:
        if tc["name"] == "ConductResearch":
            research_calls.append(tc)
        elif tc["name"] == "ResearchComplete":
            complete_calls.append(tc)
    
    # Handle ResearchComplete
    if complete_calls:
        for tc in complete_calls:
            tool_messages.append(ToolMessage(
                content="Research marked as complete.",
                tool_call_id=tc["id"],
                name=tc["name"],
            ))
        return Command(
            goto=END,
            update={
                "supervisor_messages": messages + tool_messages,
                "notes": state.get("notes", []),
            }
        )
    
    # Handle research delegation (parallel execution)
    if research_calls:
        # Limit concurrent research
        allowed_calls = research_calls[:cfg.max_concurrent_research_units]
        overflow_calls = research_calls[cfg.max_concurrent_research_units:]
        
        # Execute research in parallel
        tasks = [
            researcher_subgraph.ainvoke({
                "researcher_messages": [],
                "research_topic": tc["args"]["research_topic"],
                "tool_call_iterations": 0,
            }, config)
            for tc in allowed_calls
        ]
        
        try:
            results = await asyncio.gather(*tasks)
            
            for result, tc in zip(results, allowed_calls):
                compressed = result.get("compressed_research", "No findings.")
                tool_messages.append(ToolMessage(
                    content=compressed,
                    tool_call_id=tc["id"],
                    name=tc["name"],
                ))
                new_notes.append(f"## {tc['args']['research_topic']}\n\n{compressed}")
        except Exception as e:
            for tc in allowed_calls:
                tool_messages.append(ToolMessage(
                    content=f"Research failed: {e}",
                    tool_call_id=tc["id"],
                    name=tc["name"],
                ))
        
        # Handle overflow
        for tc in overflow_calls:
            tool_messages.append(ToolMessage(
                content=f"Research skipped: exceeded max concurrent limit ({cfg.max_concurrent_research_units}).",
                tool_call_id=tc["id"],
                name=tc["name"],
            ))
    
    return Command(
        goto="supervisor",
        update={
            "supervisor_messages": messages + tool_messages,
            "notes": state.get("notes", []) + new_notes,
        }
    )


# Build supervisor subgraph
supervisor_builder = StateGraph(SupervisorState)
supervisor_builder.add_node("supervisor", supervisor)
supervisor_builder.add_node("supervisor_tools", supervisor_tools)
supervisor_builder.add_edge(START, "supervisor")
supervisor_subgraph = supervisor_builder.compile()


###################
# Main Workflow
###################

async def generate_research_brief(state: AgentState, config: RunnableConfig) -> dict:
    """Generate a research brief from user input."""
    cfg = DeepResearchConfig.from_env()
    
    model = configurable_model(
        cfg.research_model,
        max_tokens=2048,
    )
    
    messages = state.get("messages", [])
    user_request = get_buffer_string(messages)
    
    prompt = RESEARCH_BRIEF_PROMPT.format(user_request=user_request)
    response = await model.ainvoke([HumanMessage(content=prompt)])
    
    return {
        "research_brief": response.content,
        "supervisor_messages": [HumanMessage(content=response.content)],
    }


async def run_supervisor(state: AgentState, config: RunnableConfig) -> dict:
    """Run the supervisor to coordinate research."""
    result = await supervisor_subgraph.ainvoke({
        "supervisor_messages": state.get("supervisor_messages", []),
        "research_brief": state.get("research_brief", ""),
        "notes": state.get("notes", []),
        "research_iterations": 0,
    }, config)
    
    return {
        "notes": result.get("notes", []),
        "raw_notes": result.get("raw_notes", []),
    }


async def generate_final_report(state: AgentState, config: RunnableConfig) -> dict:
    """Generate the final research report."""
    cfg = DeepResearchConfig.from_env()
    
    model = configurable_model(
        cfg.final_report_model,
        max_tokens=cfg.final_report_max_tokens,
    )
    
    notes = state.get("notes", [])
    findings = "\n\n".join(notes) if notes else "No research findings available."
    
    # Truncate if too long
    if len(findings) > cfg.max_content_length:
        findings = findings[:cfg.max_content_length] + "\n\n[Content truncated due to length...]"
    
    prompt = FINAL_REPORT_PROMPT.format(
        date=get_today_str(),
        research_brief=state.get("research_brief", ""),
        messages=get_buffer_string(state.get("messages", [])),
        findings=findings,
    )
    
    response = await model.ainvoke([HumanMessage(content=prompt)])
    
    return {
        "final_report": response.content,
        "messages": state.get("messages", []) + [AIMessage(content=response.content)],
    }


# Build main workflow
deep_researcher_builder = StateGraph(AgentState, input=AgentInputState)
deep_researcher_builder.add_node("generate_brief", generate_research_brief)
deep_researcher_builder.add_node("run_supervisor", run_supervisor)
deep_researcher_builder.add_node("generate_report", generate_final_report)

# Define edges
deep_researcher_builder.add_edge(START, "generate_brief")
deep_researcher_builder.add_edge("generate_brief", "run_supervisor")
deep_researcher_builder.add_edge("run_supervisor", "generate_report")
deep_researcher_builder.add_edge("generate_report", END)

# Compile the workflow
deep_researcher = deep_researcher_builder.compile()


###################
# Public API
###################

async def run_deep_research(
    topic: str,
    config: Optional[DeepResearchConfig] = None,
) -> str:
    """Run deep research on a topic and return the final report.
    
    Args:
        topic: The research topic/question
        config: Optional configuration overrides
    
    Returns:
        The final research report as markdown
    """
    result = await deep_researcher.ainvoke({
        "messages": [HumanMessage(content=topic)],
    })
    
    return result.get("final_report", "Error: No report generated.")


def run_deep_research_sync(
    topic: str,
    config: Optional[DeepResearchConfig] = None,
) -> str:
    """Synchronous wrapper for run_deep_research."""
    return asyncio.run(run_deep_research(topic, config))
