"""Deep Research Agent - Comprehensive research workflow inspired by Open Deep Research.

This module implements a multi-stage research workflow:
1. Query Planning: Break topic into focused sub-queries
2. Parallel Search: Execute searches across multiple providers
3. Result Summarization: Compress findings per source
4. Gap Analysis: Identify missing coverage areas
5. Final Synthesis: Produce structured research report
"""

from __future__ import annotations

import os
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ResearchDepth(Enum):
 """Research depth levels controlling thoroughness vs speed."""
 SHALLOW = "shallow" # Quick overview: 5 papers, no gap analysis
 STANDARD = "standard" # Balanced: 15 papers, basic gap analysis
 DEEP = "deep" # Comprehensive: 30+ papers, detailed synthesis


@dataclass
class ResearchConfig:
 """Configuration for deep research workflow."""
 depth: ResearchDepth = ResearchDepth.STANDARD
 max_papers_per_provider: int = 10
 from_year: Optional[int] = 2020
 include_web_search: bool = True
 include_gap_analysis: bool = True
 
 # Model preferences - supports local Ollama models on GPU
 # Use environment variables for easy configuration:
 # RESEARCH_SUMMARIZATION_MODEL - for summarizing papers (fast, smaller model)
 # RESEARCH_DEEP_MODEL - for deep analysis (larger reasoning model)
 # RESEARCH_REPORT_MODEL - for report generation
 # USE_LOCAL_LLM=true - to force local Ollama models
 summarization_model: str = "" # Set in __post_init__
 research_model: str = "" # Set in __post_init__
 report_model: str = "" # Set in __post_init__
 
 # Provider selection (openrouter, openai, ollama)
 provider: str = "" # Set in __post_init__

 def __post_init__(self):
 """Configure models based on environment and depth."""
 import os
 
 # Determine provider
 use_local = os.getenv("USE_LOCAL_LLM", "false").lower() in ("true", "1", "yes")
 self.provider = os.getenv("LLM_PROVIDER", "ollama" if use_local else "openrouter")
 
 # Set model defaults based on provider
 if self.provider == "ollama":
 # Local Ollama models optimized for RTX 5090 (32GB VRAM)
 # DeepSeek R1 14B for reasoning, Qwen 2.5 Coder 14B for coding
 self.summarization_model = os.getenv("RESEARCH_SUMMARIZATION_MODEL", "qwen2.5:14b")
 self.research_model = os.getenv("RESEARCH_DEEP_MODEL", "deepseek-r1:14b")
 self.report_model = os.getenv("RESEARCH_REPORT_MODEL", "qwen2.5:14b")
 else:
 # Cloud API models
 self.summarization_model = os.getenv("RESEARCH_SUMMARIZATION_MODEL", "openai:gpt-4o-mini")
 self.research_model = os.getenv("RESEARCH_DEEP_MODEL", "openai:gpt-4.1")
 self.report_model = os.getenv("RESEARCH_REPORT_MODEL", "openai:gpt-4.1")
 
 # Adjust settings based on depth
 if self.depth == ResearchDepth.SHALLOW:
 self.max_papers_per_provider = 5
 self.include_gap_analysis = False
 elif self.depth == ResearchDepth.DEEP:
 self.max_papers_per_provider = 15
 self.from_year = 2018


@dataclass
class SearchResultSummary:
 """Summarized search result."""
 title: str
 url: str
 source: str
 summary: str
 key_findings: List[str]
 relevance_score: float
 year: Optional[int] = None
 citations: Optional[int] = None


@dataclass
class ResearchReport:
 """Final research report structure."""
 topic: str
 summary: str
 key_themes: List[str]
 sources: List[SearchResultSummary]
 gap_analysis: Optional[str] = None
 methodology_recommendations: Optional[str] = None
 future_directions: List[str] = field(default_factory=list)
 markdown_report: str = ""
 metadata: Dict[str, Any] = field(default_factory=dict)


class DeepResearchAgent:
 """Agent for conducting comprehensive deep research.
 
 Inspired by LangChain's Open Deep Research, this agent orchestrates
 multi-source search, summarization, and synthesis to produce
 publication-quality research reports.
 """

 def __init__(self, config: Optional[ResearchConfig] = None):
 """Initialize the deep research agent.
 
 Args:
 config: Research configuration (uses defaults if not provided)
 """
 self.config = config or ResearchConfig()
 self._llm_client = None
 self._registry = None

 def _get_registry(self):
 """Lazy load the provider registry."""
 if self._registry is None:
 from ..literature_review.providers import get_registry
 self._registry = get_registry()
 return self._registry

 def _get_llm_client(self):
 """Lazy load the LLM client."""
 if self._llm_client is None:
 from ..llm import create_client
 self._llm_client = create_client()
 return self._llm_client

 def _plan_queries(self, topic: str) -> List[str]:
 """Break a research topic into focused sub-queries.
 
 Args:
 topic: Main research topic
 
 Returns:
 List of focused sub-queries
 """
 # Generate sub-queries using LLM
 client = self._get_llm_client()
 
 prompt = f"""Break down this research topic into 3-5 focused search queries.
Each query should target a different aspect of the topic.

Topic: {topic}

Return ONLY a JSON array of query strings, no explanation.
Example: ["query1", "query2", "query3"]
"""
 
 try:
 from ..llm import Message
 response, _ = client.chat([
 Message.system("You are a research query planner. Output only valid JSON."),
 Message.user(prompt),
 ])
 
 import json
 import re
 
 # Extract JSON from response
 content = response.content
 match = re.search(r'\[.*\]', content, re.DOTALL)
 if match:
 queries = json.loads(match.group())
 return queries[:5] # Limit to 5 queries
 except Exception as e:
 print(f"Query planning failed: {e}")
 
 # Fallback: use the topic directly
 return [topic]

 def _search_all_providers(self, queries: List[str]) -> Dict[str, List[Any]]:
 """Execute search across all available providers.
 
 Args:
 queries: List of search queries
 
 Returns:
 Dict mapping provider name to list of results
 """
 registry = self._get_registry()
 all_results: Dict[str, List[Any]] = {}
 
 for query in queries:
 results = registry.search_all(
 query=query,
 limit_per_provider=self.config.max_papers_per_provider,
 from_year=self.config.from_year,
 )
 
 # Merge results
 for provider, provider_results in results.items():
 if provider not in all_results:
 all_results[provider] = []
 all_results[provider].extend(provider_results)
 
 # Deduplicate by URL
 for provider in all_results:
 seen_urls = set()
 unique_results = []
 for result in all_results[provider]:
 if result.url not in seen_urls:
 seen_urls.add(result.url)
 unique_results.append(result)
 all_results[provider] = unique_results
 
 return all_results

 def _summarize_result(self, result: Any) -> SearchResultSummary:
 """Summarize a single search result.
 
 Args:
 result: SearchResult object
 
 Returns:
 SearchResultSummary with key findings extracted
 """
 client = self._get_llm_client()
 
 prompt = f"""Summarize this paper/article for a research overview.

Title: {result.title}
Abstract: {result.abstract[:1000] if result.abstract else 'No abstract available'}

Provide:
1. A 2-sentence summary
2. 2-3 key findings/contributions

Format as JSON:
{{"summary": "...", "key_findings": ["finding1", "finding2"]}}
"""
 
 try:
 from ..llm import Message
 response, _ = client.chat([
 Message.system("You are a research summarizer. Output only valid JSON."),
 Message.user(prompt),
 ])
 
 import json
 import re
 
 content = response.content
 match = re.search(r'\{.*\}', content, re.DOTALL)
 if match:
 data = json.loads(match.group())
 return SearchResultSummary(
 title=result.title,
 url=result.url,
 source=result.source,
 summary=data.get("summary", ""),
 key_findings=data.get("key_findings", []),
 relevance_score=result.relevance_score or 0.5,
 year=result.year,
 citations=result.citations,
 )
 except Exception as e:
 print(f"Summarization failed for {result.title}: {e}")
 
 # Fallback: basic summary
 return SearchResultSummary(
 title=result.title,
 url=result.url,
 source=result.source,
 summary=result.abstract[:200] if result.abstract else "No summary available",
 key_findings=[],
 relevance_score=result.relevance_score or 0.5,
 year=result.year,
 citations=result.citations,
 )

 def _analyze_gaps(self, topic: str, summaries: List[SearchResultSummary]) -> str:
 """Identify research gaps from the collected literature.
 
 Args:
 topic: Original research topic
 summaries: List of summarized results
 
 Returns:
 Gap analysis text
 """
 if not self.config.include_gap_analysis:
 return ""
 
 client = self._get_llm_client()
 
 # Compile findings
 findings_text = "\n".join([
 f"- {s.title} ({s.source}, {s.year}): {s.summary}"
 for s in summaries[:15] # Limit for context
 ])
 
 prompt = f"""Based on these papers about "{topic}", identify research gaps.

Papers reviewed:
{findings_text}

Identify:
1. Under-explored areas in this topic
2. Methodological gaps
3. Potential novel contributions

Be specific and actionable. Keep response under 300 words.
"""
 
 try:
 from ..llm import Message
 response, _ = client.chat([
 Message.system("You are a research advisor identifying gaps in literature."),
 Message.user(prompt),
 ])
 return response.content
 except Exception as e:
 print(f"Gap analysis failed: {e}")
 return ""

 def _synthesize_report(
 self,
 topic: str,
 summaries: List[SearchResultSummary],
 gap_analysis: str,
 ) -> ResearchReport:
 """Synthesize all findings into a final report.
 
 Args:
 topic: Original research topic
 summaries: List of summarized results
 gap_analysis: Gap analysis text
 
 Returns:
 Complete ResearchReport
 """
 client = self._get_llm_client()
 
 # Generate report synthesis
 findings_text = "\n".join([
 f"- {s.title}: {s.summary}"
 for s in summaries[:20]
 ])
 
 prompt = f"""Synthesize a research report on "{topic}" based on these papers.

Papers:
{findings_text}

Gap Analysis:
{gap_analysis if gap_analysis else "Not conducted"}

Provide:
1. Executive summary (2-3 sentences)
2. 3-5 key themes in the literature
3. 2-3 future research directions

Format as JSON:
{{"summary": "...", "themes": ["theme1", "theme2"], "future_directions": ["dir1", "dir2"]}}
"""
 
 try:
 from ..llm import Message
 response, _ = client.chat([
 Message.system("You are a research synthesizer. Output only valid JSON."),
 Message.user(prompt),
 ])
 
 import json
 import re
 
 content = response.content
 match = re.search(r'\{.*\}', content, re.DOTALL)
 if match:
 data = json.loads(match.group())
 
 report = ResearchReport(
 topic=topic,
 summary=data.get("summary", ""),
 key_themes=data.get("themes", []),
 sources=summaries,
 gap_analysis=gap_analysis,
 future_directions=data.get("future_directions", []),
 metadata={
 "total_papers": len(summaries),
 "depth": self.config.depth.value,
 },
 )
 
 # Generate markdown report
 from .report_generator import ReportGenerator
 report.markdown_report = ReportGenerator.generate(report)
 
 return report
 except Exception as e:
 print(f"Synthesis failed: {e}")
 
 # Fallback report
 return ResearchReport(
 topic=topic,
 summary="Research synthesis could not be completed.",
 key_themes=[],
 sources=summaries,
 gap_analysis=gap_analysis,
 metadata={"error": "synthesis_failed"},
 )

 def research(self, topic: str) -> ResearchReport:
 """Execute the full deep research workflow.
 
 Args:
 topic: Research topic to investigate
 
 Returns:
 Complete ResearchReport with findings and synthesis
 """
 print(f"[DeepResearch] Starting research on: {topic}")
 print(f"[DeepResearch] Depth: {self.config.depth.value}")
 
 # Step 1: Plan queries
 print("[DeepResearch] Planning queries...")
 queries = self._plan_queries(topic)
 print(f"[DeepResearch] Generated {len(queries)} sub-queries")
 
 # Step 2: Search all providers
 print("[DeepResearch] Searching across providers...")
 all_results = self._search_all_providers(queries)
 total_results = sum(len(r) for r in all_results.values())
 print(f"[DeepResearch] Found {total_results} results from {len(all_results)} providers")
 
 # Step 3: Summarize results
 print("[DeepResearch] Summarizing results...")
 summaries: List[SearchResultSummary] = []
 
 # Flatten and limit results
 flat_results = []
 for results in all_results.values():
 flat_results.extend(results)
 
 # Take top N based on depth
 max_to_summarize = {
 ResearchDepth.SHALLOW: 5,
 ResearchDepth.STANDARD: 15,
 ResearchDepth.DEEP: 30,
 }[self.config.depth]
 
 for result in flat_results[:max_to_summarize]:
 summary = self._summarize_result(result)
 summaries.append(summary)
 
 print(f"[DeepResearch] Summarized {len(summaries)} papers")
 
 # Step 4: Analyze gaps
 gap_analysis = ""
 if self.config.include_gap_analysis:
 print("[DeepResearch] Analyzing research gaps...")
 gap_analysis = self._analyze_gaps(topic, summaries)
 
 # Step 5: Synthesize report
 print("[DeepResearch] Synthesizing final report...")
 report = self._synthesize_report(topic, summaries, gap_analysis)
 
 print("[DeepResearch] Research complete!")
 return report

