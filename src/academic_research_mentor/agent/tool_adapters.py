"""Adapters to bridge legacy BaseTool implementations to the new ToolRegistry."""

from __future__ import annotations

import json
from typing import Any, Optional

from .tools import Tool


class WebSearchToolAdapter(Tool):
    """Adapter for the WebSearchTool."""
    
    def __init__(self):
        from academic_research_mentor.tools.web_search.tool import WebSearchTool
        self._tool = WebSearchTool()
        self._tool.initialize()
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return (
            "Search the web for recent information, news, articles, and resources. "
            "Use this for current events, recent developments, blog posts, or when you need "
            "up-to-date information that may not be in academic papers."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (1-12)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 5)
        
        if not query:
            return "Error: No search query provided"
        
        result = self._tool.execute({"query": query, "limit": limit})
        
        # Format results for the LLM
        results = result.get("results", [])
        if not results:
            note = result.get("note", "No results found")
            return f"Web search returned no results. {note}"
        
        formatted = []
        for i, r in enumerate(results[:limit], 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = r.get("content", r.get("snippet", ""))[:300]
            formatted.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet}")
        
        return "\n\n".join(formatted)


class ArxivSearchToolAdapter(Tool):
    """Adapter for the ArxivSearchTool."""
    
    def __init__(self):
        from academic_research_mentor.tools.legacy.arxiv.tool import ArxivSearchTool
        self._tool = ArxivSearchTool()
        self._tool.initialize()
    
    @property
    def name(self) -> str:
        return "arxiv_search"
    
    @property
    def description(self) -> str:
        return (
            "Search arXiv for academic papers in computer science, machine learning, AI, "
            "physics, mathematics, and other scientific fields. Use this when looking for "
            "research papers, preprints, or academic literature."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for academic papers"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of papers to return (1-20)",
                    "default": 5
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["relevance", "date"],
                    "description": "Sort order. Use 'date' to find the absolute latest papers.",
                    "default": "relevance"
                }
            },
            "required": ["query"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 5)
        sort_by = kwargs.get("sort_by", "relevance")
        
        if not query:
            return "Error: No search query provided"
        
        result = self._tool.execute({"query": query, "limit": limit, "sort_by": sort_by})
        
        # Format results for the LLM
        papers = result.get("papers", [])
        if not papers:
            note = result.get("note", "No papers found")
            return f"arXiv search returned no results. {note}"
        
        formatted = []
        for i, p in enumerate(papers[:limit], 1):
            title = p.get("title", "Untitled")
            authors = ", ".join(p.get("authors", [])[:3])
            if len(p.get("authors", [])) > 3:
                authors += " et al."
            url = p.get("url", "")
            year = p.get("year", "")
            published = p.get("published", "")
            summary = (p.get("summary", "") or "")[:400]
            
            # Show full published date if available, otherwise year
            date_str = f"Published: {published}" if published else f"Year: {year}"
            
            formatted.append(
                f"{i}. **{title}**\n"
                f"   Authors: {authors}\n"
                f"   {date_str} | URL: {url}\n"
                f"   {summary}"
            )
        
        return "\n\n".join(formatted)


class LiteratureSearchToolAdapter(Tool):
    """Search ALL 5 FREE academic providers: arXiv, OpenReview, PubMed, HAL, Zenodo."""
    
    @property
    def name(self) -> str:
        return "literature_search"
    
    @property
    def description(self) -> str:
        return (
            "Search academic literature across 5 FREE sources: "
            "arXiv (AI/ML/CS), OpenReview (AI conferences), PubMed (medical), "
            "HAL (European research), and Zenodo (datasets). "
            "Use this for comprehensive literature reviews and finding related papers."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for academic papers"
                },
                "limit": {
                    "type": "integer",
                    "description": "Papers per source (1-10)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 5)
        
        if not query:
            return "Error: No search query provided"
        
        from academic_research_mentor.literature_review.providers import (
            ArxivProvider, OpenReviewProvider, PubMedProvider, HALProvider, ZenodoProvider
        )
        
        providers = [
            ("arXiv", ArxivProvider),
            ("OpenReview", OpenReviewProvider),
            ("PubMed", PubMedProvider),
            ("HAL", HALProvider),
            ("Zenodo", ZenodoProvider),
        ]
        
        all_results = []
        for name, ProviderClass in providers:
            try:
                provider = ProviderClass()
                results = provider.search(query, limit=limit)
                for r in results:
                    all_results.append({
                        "source": name,
                        "title": r.title,
                        "authors": r.authors[:3] if r.authors else [],
                        "url": r.url,
                        "year": r.year,
                        "abstract": (r.abstract or "")[:300],
                        "pdf_url": r.metadata.get("pdf_url"),
                    })
            except Exception as e:
                print(f"[{name}] Error: {e}")
        
        if not all_results:
            return "No papers found across any source."
        
        # Format results grouped by source
        formatted = []
        for i, p in enumerate(all_results[:25], 1):
            authors = ", ".join(p["authors"])
            if len(p["authors"]) >= 3:
                authors += " et al."
            pdf = f" | PDF: {p['pdf_url']}" if p.get("pdf_url") else ""
            formatted.append(
                f"{i}. [{p['source']}] **{p['title']}**\n"
                f"   Authors: {authors} | Year: {p['year'] or 'N/A'}\n"
                f"   URL: {p['url']}{pdf}\n"
                f"   {p['abstract']}"
            )
        
        return f"Found {len(all_results)} papers from 5 sources:\n\n" + "\n\n".join(formatted)


class SimilarPapersToolAdapter(Tool):
    """Find similar papers based on a paper ID or title."""
    
    @property
    def name(self) -> str:
        return "find_similar_papers"
    
    @property
    def description(self) -> str:
        return (
            "Find papers similar to a given paper. Provide an arXiv ID (e.g., '2301.12345'), "
            "DOI, or paper title. Returns related papers from multiple sources."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "arXiv ID, DOI, or paper title to find similar papers for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of similar papers to return",
                    "default": 10
                }
            },
            "required": ["paper_id"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        paper_id = kwargs.get("paper_id", "")
        limit = kwargs.get("limit", 10)
        
        if not paper_id:
            return "Error: No paper ID or title provided"
        
        # Use the paper_id as a search query to find related papers
        from academic_research_mentor.literature_review.providers import (
            ArxivProvider, OpenReviewProvider, PubMedProvider
        )
        
        # Extract keywords from paper_id if it's a title
        query = paper_id
        
        all_results = []
        for name, ProviderClass in [
            ("arXiv", ArxivProvider),
            ("OpenReview", OpenReviewProvider),
            ("PubMed", PubMedProvider),
        ]:
            try:
                provider = ProviderClass()
                results = provider.search(query, limit=limit // 3 + 1)
                for r in results:
                    all_results.append({
                        "source": name,
                        "title": r.title,
                        "url": r.url,
                        "year": r.year,
                        "abstract": (r.abstract or "")[:200],
                    })
            except Exception:
                pass
        
        if not all_results:
            return f"No similar papers found for: {paper_id}"
        
        formatted = []
        for i, p in enumerate(all_results[:limit], 1):
            formatted.append(
                f"{i}. [{p['source']}] **{p['title']}**\n"
                f"   Year: {p['year'] or 'N/A'} | URL: {p['url']}\n"
                f"   {p['abstract']}"
            )
        
        return f"Similar papers to '{paper_id}':\n\n" + "\n\n".join(formatted)


class GuidelinesToolAdapter(Tool):
    """Adapter for the GuidelinesTool (research guidelines)."""
    
    def __init__(self):
        from academic_research_mentor.tools.guidelines.tool import GuidelinesTool
        self._tool = GuidelinesTool()
        self._tool.initialize()
    
    @property
    def name(self) -> str:
        return "research_guidelines"
    
    @property
    def description(self) -> str:
        return (
            "Search for research guidelines, methodology advice, and best practices in academic research. "
            "Use this when the user needs advice on research methods, experimental design, writing practices, "
            "or general guidance on how to conduct research effectively."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The research topic or methodology question"
                },
                "topic": {
                    "type": "string",
                    "description": "Specific topic area (optional, defaults to query)"
                }
            },
            "required": ["query"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        topic = kwargs.get("topic", query)
        
        if not query:
            return "Error: No query provided for guidelines search"
        
        result = self._tool.execute({"query": query, "topic": topic})
        
        # Format results for the LLM
        formatted_content = result.get("formatted_content", "")
        if formatted_content:
            return formatted_content
        
        guidelines = result.get("retrieved_guidelines", [])
        if not guidelines:
            note = result.get("note", "No guidelines found")
            return f"No research guidelines found. {note}"
        
        formatted = []
        for i, g in enumerate(guidelines[:5], 1):
            title = g.get("title", "Guideline")
            content = g.get("content", g.get("snippet", ""))[:500]
            source = g.get("source", "")
            formatted.append(f"{i}. **{title}**\n   Source: {source}\n   {content}")
        
        return "\n\n".join(formatted)


class DeepResearchToolAdapter(Tool):
    """Deep research with comprehensive multi-source analysis."""
    
    @property
    def name(self) -> str:
        return "deep_research"
    
    @property
    def description(self) -> str:
        return (
            "Conduct comprehensive deep research on a topic. Searches 5 academic sources "
            "(arXiv, OpenReview, PubMed, HAL, Zenodo), synthesizes findings, identifies "
            "key themes, research gaps, and future directions. Use for thorough literature reviews."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The research topic to investigate"
                },
                "depth": {
                    "type": "string",
                    "enum": ["shallow", "standard", "deep"],
                    "description": "Research depth: shallow (quick), standard (balanced), deep (comprehensive)",
                    "default": "standard"
                }
            },
            "required": ["topic"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        topic = kwargs.get("topic", "")
        depth = kwargs.get("depth", "standard")
        
        if not topic:
            return "Error: No research topic provided"
        
        from academic_research_mentor.deep_research import (
            DeepResearchAgent, ResearchConfig, ResearchDepth
        )
        
        depth_map = {
            "shallow": ResearchDepth.SHALLOW,
            "standard": ResearchDepth.STANDARD,
            "deep": ResearchDepth.DEEP,
        }
        
        config = ResearchConfig(depth=depth_map.get(depth, ResearchDepth.STANDARD))
        agent = DeepResearchAgent(config=config)
        report = agent.research(topic)
        
        # Return markdown report
        return report.markdown_report


class ComparativeResearchToolAdapter(Tool):
    """Compare different research approaches."""
    
    @property
    def name(self) -> str:
        return "compare_approaches"
    
    @property
    def description(self) -> str:
        return (
            "Compare different research approaches or methods for a topic. "
            "Analyzes strengths, weaknesses, and provides recommendations. "
            "Example: compare CNN vs Transformer vs RNN for image classification."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The research problem/topic"
                },
                "approaches": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of approaches to compare (e.g., ['CNN', 'Transformer', 'RNN'])"
                }
            },
            "required": ["topic", "approaches"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        topic = kwargs.get("topic", "")
        approaches = kwargs.get("approaches", [])
        
        if not topic:
            return "Error: No topic provided"
        if not approaches or len(approaches) < 2:
            return "Error: Need at least 2 approaches to compare"
        
        from academic_research_mentor.deep_research import compare_approaches
        
        result = compare_approaches(topic, approaches)
        return result.markdown_report


class TrendAnalysisToolAdapter(Tool):
    """Analyze research trends over time."""
    
    @property
    def name(self) -> str:
        return "analyze_trends"
    
    @property
    def description(self) -> str:
        return (
            "Analyze research trends for a topic over time. Shows publication counts by year, "
            "emerging/declining topics, growth rate, and forecasts. Useful for understanding "
            "how a research area is evolving."
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The research topic to analyze"
                },
                "start_year": {
                    "type": "integer",
                    "description": "Start year for analysis",
                    "default": 2018
                }
            },
            "required": ["topic"]
        }
    
    def execute(self, **kwargs: Any) -> str:
        topic = kwargs.get("topic", "")
        start_year = kwargs.get("start_year", 2018)
        
        if not topic:
            return "Error: No topic provided"
        
        from academic_research_mentor.deep_research import analyze_research_trends
        
        result = analyze_research_trends(topic, start_year)
        return result.markdown_report


def create_default_tools() -> list[Tool]:
    """Create all default tools for the mentor agent."""
    tools = []
    
    # Literature search using ALL 5 FREE providers (primary tool)
    try:
        tools.append(LiteratureSearchToolAdapter())
        print("✓ literature_search tool (5 sources: arXiv, OpenReview, PubMed, HAL, Zenodo)")
    except Exception as e:
        print(f"Warning: Could not initialize literature_search tool: {e}")
    
    # Deep research (comprehensive)
    try:
        tools.append(DeepResearchToolAdapter())
        print("✓ deep_research tool")
    except Exception as e:
        print(f"Warning: Could not initialize deep_research tool: {e}")
    
    # Comparative research
    try:
        tools.append(ComparativeResearchToolAdapter())
        print("✓ compare_approaches tool")
    except Exception as e:
        print(f"Warning: Could not initialize compare_approaches tool: {e}")
    
    # Trend analysis
    try:
        tools.append(TrendAnalysisToolAdapter())
        print("✓ analyze_trends tool")
    except Exception as e:
        print(f"Warning: Could not initialize analyze_trends tool: {e}")
    
    # Similar papers finder
    try:
        tools.append(SimilarPapersToolAdapter())
        print("✓ find_similar_papers tool")
    except Exception as e:
        print(f"Warning: Could not initialize find_similar_papers tool: {e}")
    
    # Keep arXiv as standalone for quick searches
    try:
        tools.append(ArxivSearchToolAdapter())
        print("✓ arxiv_search tool")
    except Exception as e:
        print(f"Warning: Could not initialize arxiv_search tool: {e}")
    
    # Web search (if available)
    try:
        tools.append(WebSearchToolAdapter())
        print("✓ web_search tool")
    except Exception as e:
        print(f"Warning: Could not initialize web_search tool: {e}")
    
    # Research guidelines
    try:
        tools.append(GuidelinesToolAdapter())
        print("✓ research_guidelines tool")
    except Exception as e:
        print(f"Warning: Could not initialize research_guidelines tool: {e}")
    
    return tools
