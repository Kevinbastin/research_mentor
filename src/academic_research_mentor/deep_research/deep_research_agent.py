"""Deep Research Agent - Uses 100% FREE providers."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ResearchDepth(Enum):
    SHALLOW = "shallow"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class ResearchConfig:
    depth: ResearchDepth = ResearchDepth.STANDARD
    max_papers_per_provider: int = 10
    top_k: int = 10  # Return top 10 papers overall
    from_year: Optional[int] = None
    include_gap_analysis: bool = True
    provider: str = ""

    def __post_init__(self):
        self.provider = "ollama"  # Always use local Ollama qwen model
        if self.depth == ResearchDepth.SHALLOW:
            self.max_papers_per_provider = 5
            self.top_k = 10
        elif self.depth == ResearchDepth.STANDARD:
            self.max_papers_per_provider = 10
            self.top_k = 10
        elif self.depth == ResearchDepth.DEEP:
            self.max_papers_per_provider = 15
            self.top_k = 10


@dataclass
class SearchResultSummary:
    title: str
    url: str
    source: str
    summary: str
    year: Optional[int] = None
    citations: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    venue: Optional[str] = None


@dataclass
class ResearchReport:
    topic: str
    summary: str
    key_themes: List[str]
    sources: List[SearchResultSummary]
    gap_analysis: Optional[str] = None
    markdown_report: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeepResearchAgent:
    """Deep research using 100% FREE providers:
    - arXiv (AI/ML/CS)
    - OpenReview (AI conferences)
    - PubMed (Medical)
    - HAL (European)
    - Zenodo (Datasets)
    """

    def __init__(self, config: Optional[ResearchConfig] = None):
        self.config = config or ResearchConfig()
        self._llm_client = None

    def _get_llm_client(self):
        if self._llm_client is None:
            from ..llm import create_client
            self._llm_client = create_client(provider=self.config.provider)
        return self._llm_client

    def _search_arxiv(self, topic: str, limit: int) -> List[SearchResultSummary]:
        """ArXiv - FREE, great for AI/ML/CS/Physics."""
        sources = []
        try:
            from ..mentor_tools import arxiv_search
            result = arxiv_search(query=topic, limit=limit)
            for paper in result.get("papers", []):
                sources.append(SearchResultSummary(
                    title=paper.get("title", "Unknown"),
                    url=paper.get("url", ""),
                    source="arXiv",
                    summary=paper.get("summary", "")[:400],
                    year=paper.get("year"),
                    authors=paper.get("authors", [])[:3],
                    venue="arXiv",
                ))
        except Exception as e:
            print(f"[arXiv] Error: {e}")
        return sources

    def _search_provider(self, provider_name: str, topic: str, limit: int) -> List[SearchResultSummary]:
        """Generic search using registry provider."""
        sources = []
        try:
            from ..literature_review.providers import get_registry
            registry = get_registry()
            provider = registry.get(provider_name)
            if provider and provider.is_available():
                results = provider.search(query=topic, limit=limit)
                for r in results:
                    sources.append(SearchResultSummary(
                        title=r.title,
                        url=r.url,
                        source=provider_name,
                        summary=r.abstract[:400] if r.abstract else "",
                        year=r.year,
                        authors=r.authors[:3] if r.authors else [],
                        venue=r.venue,
                    ))
        except Exception as e:
            print(f"[{provider_name}] Error: {e}")
        return sources

    def _score_relevance(self, topic: str, paper: SearchResultSummary) -> float:
        """Score a paper's relevance to the topic using keyword matching."""
        topic_words = set(topic.lower().split())
        # Remove common stop words
        stop_words = {"the", "a", "an", "of", "in", "on", "for", "and", "or", "to", "is", "with", "by", "from", "at", "as"}
        topic_words -= stop_words

        text = f"{paper.title} {paper.summary}".lower()
        if not topic_words:
            return 0.0

        # Count how many topic keywords appear in the paper text
        matches = sum(1 for w in topic_words if w in text)
        score = matches / len(topic_words)

        # No year bias — papers from any year are treated equally

        return score

    def _rank_top_papers(self, topic: str, sources: List[SearchResultSummary], top_k: int = 10) -> List[SearchResultSummary]:
        """Pick the top 10 most relevant papers across ALL providers.
        
        Scores every paper by keyword relevance, sorts globally, returns the best 10.
        No per-provider quota — purely the best papers regardless of source.
        """
        if len(sources) <= top_k:
            return sources

        # Score every paper
        scored = [(self._score_relevance(topic, s), s) for s in sources]

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        top = [paper for _, paper in scored[:top_k]]

        # Log which providers made it
        prov_counts: dict[str, int] = {}
        for p in top:
            key = p.source.lower().strip()
            prov_counts[key] = prov_counts.get(key, 0) + 1
        for prov, cnt in sorted(prov_counts.items()):
            print(f"[Ranking] {prov}: {cnt} paper(s) in top {top_k}")
        print(f"[Ranking] Total selected: {len(top)} from {len(prov_counts)} providers")

        return top

    def research(self, topic: str) -> ResearchReport:
        """Conduct research using ALL free providers, return top 10 papers."""
        all_sources = []
        counts = {}
        
        # 1. ArXiv - Core AI/ML/CS
        print(f"[1/5] Searching arXiv...")
        arxiv = self._search_arxiv(topic, self.config.max_papers_per_provider)
        all_sources.extend(arxiv)
        counts["arXiv"] = len(arxiv)
        print(f"      Found {len(arxiv)} papers")
        
        # 2. OpenReview - AI Conferences
        print(f"[2/5] Searching OpenReview...")
        openreview = self._search_provider("openreview", topic, self.config.max_papers_per_provider)
        all_sources.extend(openreview)
        counts["OpenReview"] = len(openreview)
        print(f"      Found {len(openreview)} papers")
        
        # 3. PubMed - Medical/Clinical
        print(f"[3/5] Searching PubMed...")
        pubmed = self._search_provider("pubmed", topic, self.config.max_papers_per_provider)
        all_sources.extend(pubmed)
        counts["PubMed"] = len(pubmed)
        print(f"      Found {len(pubmed)} papers")
        
        # 4. HAL - European Research
        print(f"[4/5] Searching HAL...")
        hal = self._search_provider("hal", topic, self.config.max_papers_per_provider)
        all_sources.extend(hal)
        counts["HAL"] = len(hal)
        print(f"      Found {len(hal)} papers")
        
        # 5. Zenodo - Datasets
        print(f"[5/5] Searching Zenodo...")
        zenodo = self._search_provider("zenodo", topic, self.config.max_papers_per_provider)
        all_sources.extend(zenodo)
        counts["Zenodo"] = len(zenodo)
        print(f"      Found {len(zenodo)} papers")
        
        total_fetched = len(all_sources)
        print(f"\nTotal fetched: {total_fetched} from {len([c for c in counts.values() if c > 0])} providers")
        
        # Rank and select top 10 papers using LLM
        top_sources = self._rank_top_papers(topic, all_sources, self.config.top_k)
        total = len(top_sources)
        print(f"Top {total} papers selected")
        
        # Generate analysis using LLM
        summary = ""
        key_themes = []
        
        try:
            client = self._get_llm_client()
            from ..llm import Message
            
            if top_sources:
                # Show all top 10 papers to LLM for analysis
                src_text = ""
                for i, s in enumerate(top_sources, 1):
                    src_text += f"\n{i}. [{s.source}] {s.title} ({s.year})\n"
                    src_text += f"   Authors: {', '.join(s.authors)}\n"
                    src_text += f"   {s.summary[:200]}\n"
                
                prompt = f"""Analyze these top {total} research papers on "{topic}" from multiple academic sources:
{src_text}

Provide:
1. **Executive Summary** (3 paragraphs synthesizing findings across sources)
2. **Key Research Themes** (7 bullet points)
3. **Methodological Approaches** (common techniques)
4. **Cross-Source Insights** (compare findings from different sources)
5. **Research Gaps** (what needs more investigation)
6. **Future Directions** (emerging trends)

Reference specific papers and sources."""

                response, _ = client.chat([
                    Message.system("You are a research expert synthesizing multi-source academic literature."),
                    Message.user(prompt),
                ])
                summary = response.content
                
                # Extract themes
                bullets = re.findall(r"[-*•]\s*\*?\*?([^*\n]{15,})", summary)
                key_themes = [b.strip()[:100] for b in bullets[:10] if len(b.strip()) > 15]
            else:
                prompt = f"Provide research overview on: {topic}"
                response, _ = client.chat([Message.system("Research expert"), Message.user(prompt)])
                summary = response.content
                
        except Exception as e:
            print(f"[LLM] Error: {e}")
            summary = f"Found {total} papers. Error: {e}"
        
        if not key_themes:
            key_themes = [s.title[:80] for s in top_sources[:7]] if top_sources else ["No papers found"]

        # Build markdown report with top 10 papers
        md = f"# Research Report: {topic}\n\n"
        md += f"*Top {total} papers selected from {total_fetched} results across: "
        md += ", ".join([f"{k} ({v})" for k, v in counts.items() if v > 0])
        md += "*\n\n"
        md += f"## Analysis\n{summary}\n\n"
        md += f"## Top {total} Papers\n\n"
        for i, s in enumerate(top_sources, 1):
            authors = ", ".join(s.authors) if s.authors else "Unknown"
            md += f"{i}. **[{s.title}]({s.url})** ({s.year})\n"
            md += f"   - Source: {s.source} | Authors: {authors}\n"
            md += f"   - {s.summary[:200]}\n\n"

        return ResearchReport(
            topic=topic,
            summary=summary,
            key_themes=key_themes,
            sources=top_sources,
            markdown_report=md,
            metadata={
                "total_fetched": total_fetched,
                "top_k": total,
                "provider": self.config.provider,
                **counts,
            },
        )
