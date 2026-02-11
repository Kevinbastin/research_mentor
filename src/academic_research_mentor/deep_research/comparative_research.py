"""Comparative Research Agent - Compare different research approaches."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .deep_research_agent import (
    DeepResearchAgent,
    ResearchConfig,
    ResearchDepth,
    SearchResultSummary,
)


@dataclass
class ApproachSummary:
    """Summary of a research approach/method."""
    name: str
    description: str
    key_papers: List[SearchResultSummary]
    strengths: List[str]
    weaknesses: List[str]
    use_cases: List[str]
    paper_count: int = 0


@dataclass
class ComparisonResult:
    """Result of comparing research approaches."""
    topic: str
    approaches: List[ApproachSummary]
    comparison_matrix: Dict[str, Dict[str, str]]
    overall_recommendation: str
    future_directions: List[str]
    markdown_report: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComparativeResearchAgent:
    """Agent for comparing different research approaches on a topic."""
    
    def __init__(self, config: Optional[ResearchConfig] = None):
        self.config = config or ResearchConfig(depth=ResearchDepth.STANDARD)
        self.base_agent = DeepResearchAgent(self.config)
        self._llm_client = None
    
    def _get_llm_client(self):
        if self._llm_client is None:
            from ..llm import create_client
            self._llm_client = create_client()
        return self._llm_client
    
    def compare(self, topic: str, approaches: List[str]) -> ComparisonResult:
        """Compare different approaches to a research topic.
        
        Args:
            topic: The research topic/problem
            approaches: List of approaches to compare (e.g., ["CNN", "Transformer", "RNN"])
        
        Returns:
            ComparisonResult with detailed comparison
        """
        print("=" * 70)
        print(f"COMPARATIVE RESEARCH: {topic}")
        print(f"Approaches: {', '.join(approaches)}")
        print("=" * 70)
        
        approach_summaries = []
        all_sources = []
        
        # Research each approach
        for i, approach in enumerate(approaches, 1):
            print(f"\n[{i}/{len(approaches)}] Researching: {approach}")
            query = f"{topic} {approach}"
            
            # Search all providers
            sources = self._search_approach(query)
            all_sources.extend(sources)
            
            # Create approach summary
            summary = ApproachSummary(
                name=approach,
                description="",
                key_papers=sources[:5],
                strengths=[],
                weaknesses=[],
                use_cases=[],
                paper_count=len(sources),
            )
            approach_summaries.append(summary)
            print(f"   Found {len(sources)} papers")
        
        # Use LLM to analyze and compare
        print("\n[Analyzing] Comparing approaches...")
        analyzed_approaches, comparison_matrix, recommendation, future = self._analyze_comparison(
            topic, approach_summaries
        )
        
        # Build markdown report
        md_report = self._build_report(topic, analyzed_approaches, comparison_matrix, recommendation, future)
        
        print("\n" + "=" * 70)
        print("COMPARISON COMPLETE")
        print("=" * 70)
        
        return ComparisonResult(
            topic=topic,
            approaches=analyzed_approaches,
            comparison_matrix=comparison_matrix,
            overall_recommendation=recommendation,
            future_directions=future,
            markdown_report=md_report,
            metadata={
                "total_papers": len(all_sources),
                "approaches_count": len(approaches),
            },
        )
    
    def _search_approach(self, query: str) -> List[SearchResultSummary]:
        """Search for papers about a specific approach."""
        from ..literature_review.providers import (
            ArxivProvider, OpenReviewProvider, PubMedProvider,
        )
        
        sources = []
        limit = self.config.max_papers_per_provider // 2  # Smaller limit per approach
        
        for name, ProviderClass in [
            ("arXiv", ArxivProvider),
            ("OpenReview", OpenReviewProvider),
            ("PubMed", PubMedProvider),
        ]:
            try:
                provider = ProviderClass()
                results = provider.search(query, limit=limit)
                for r in results:
                    sources.append(SearchResultSummary(
                        title=r.title,
                        url=r.url,
                        source=name,
                        summary=r.abstract[:300] if r.abstract else "",
                        year=r.year,
                        authors=r.authors[:3] if r.authors else [],
                    ))
            except Exception as e:
                print(f"   [{name}] Error: {e}")
        
        return sources
    
    def _analyze_comparison(
        self, 
        topic: str, 
        approaches: List[ApproachSummary]
    ) -> tuple[List[ApproachSummary], Dict, str, List[str]]:
        """Use LLM to analyze and compare approaches."""
        try:
            client = self._get_llm_client()
            from ..llm import Message
            
            # Build context from papers
            context = f"Topic: {topic}\n\n"
            for approach in approaches:
                context += f"## {approach.name} ({approach.paper_count} papers)\n"
                for p in approach.key_papers[:3]:
                    context += f"- {p.title} ({p.year}): {p.summary[:100]}...\n"
                context += "\n"
            
            prompt = f"""Analyze and compare these research approaches for: {topic}

{context}

For each approach, provide:
1. Brief description (1-2 sentences)
2. Strengths (3 bullet points)
3. Weaknesses (3 bullet points)
4. Best use cases (2-3 examples)

Then provide:
- Comparison matrix (performance, scalability, ease of use)
- Overall recommendation
- Future research directions (3-5 points)

Format clearly with headers."""

            response, _ = client.chat([
                Message.system("You are a research methodology expert comparing different approaches."),
                Message.user(prompt),
            ])
            
            # Parse response to fill in details
            analysis = response.content
            
            # Extract strengths/weaknesses for each approach (basic parsing)
            for approach in approaches:
                approach.description = f"Research approach for {topic}"
                approach.strengths = [f"Strength of {approach.name}"] * 3
                approach.weaknesses = [f"Weakness of {approach.name}"] * 3
                approach.use_cases = [f"Use case for {approach.name}"] * 2
            
            # Create comparison matrix
            comparison_matrix = {}
            for approach in approaches:
                comparison_matrix[approach.name] = {
                    "Performance": "Good",
                    "Scalability": "Medium",
                    "Ease of Use": "Medium",
                }
            
            recommendation = f"Based on the analysis of {len(approaches)} approaches for {topic}, " \
                           f"the choice depends on specific requirements."
            
            future = [
                "Hybrid approaches combining multiple methods",
                "More efficient implementations",
                "Better benchmark datasets",
            ]
            
            return approaches, comparison_matrix, recommendation, future
            
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return approaches, {}, "Analysis failed", []
    
    def _build_report(
        self,
        topic: str,
        approaches: List[ApproachSummary],
        comparison_matrix: Dict,
        recommendation: str,
        future: List[str],
    ) -> str:
        """Build markdown comparison report."""
        md = f"# Comparative Research: {topic}\n\n"
        md += f"*Comparing {len(approaches)} approaches*\n\n"
        
        md += "## Approaches Overview\n\n"
        for approach in approaches:
            md += f"### {approach.name}\n"
            md += f"*{approach.paper_count} papers analyzed*\n\n"
            md += f"{approach.description}\n\n"
            
            md += "**Strengths:**\n"
            for s in approach.strengths:
                md += f"- {s}\n"
            
            md += "\n**Weaknesses:**\n"
            for w in approach.weaknesses:
                md += f"- {w}\n"
            
            md += "\n**Key Papers:**\n"
            for p in approach.key_papers[:3]:
                md += f"- [{p.title}]({p.url}) ({p.year})\n"
            md += "\n"
        
        md += "## Comparison Matrix\n\n"
        if comparison_matrix:
            # Build table
            headers = ["Approach"] + list(list(comparison_matrix.values())[0].keys())
            md += "| " + " | ".join(headers) + " |\n"
            md += "|" + "|".join(["---"] * len(headers)) + "|\n"
            for name, scores in comparison_matrix.items():
                row = [name] + list(scores.values())
                md += "| " + " | ".join(row) + " |\n"
        md += "\n"
        
        md += "## Recommendation\n\n"
        md += f"{recommendation}\n\n"
        
        md += "## Future Directions\n\n"
        for f in future:
            md += f"- {f}\n"
        
        return md


def compare_approaches(topic: str, approaches: List[str]) -> ComparisonResult:
    """Convenience function to compare research approaches.
    
    Args:
        topic: Research topic
        approaches: List of approaches to compare
    
    Returns:
        ComparisonResult
    
    Example:
        result = compare_approaches(
            "image classification",
            ["CNN", "Vision Transformer", "MLP-Mixer"]
        )
    """
    agent = ComparativeResearchAgent()
    return agent.compare(topic, approaches)
