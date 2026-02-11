"""Trend Analysis Agent - Analyze research trends over time."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .deep_research_agent import (
    DeepResearchAgent,
    ResearchConfig,
    ResearchDepth,
    SearchResultSummary,
)


@dataclass
class YearlyTrend:
    """Research trend for a specific year."""
    year: int
    paper_count: int
    key_topics: List[str]
    representative_papers: List[SearchResultSummary]


@dataclass
class TrendAnalysisResult:
    """Result of trend analysis."""
    topic: str
    start_year: int
    end_year: int
    yearly_trends: List[YearlyTrend]
    emerging_topics: List[str]
    declining_topics: List[str]
    peak_year: int
    growth_rate: float
    forecast: str
    markdown_report: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrendAnalysisAgent:
    """Analyze research trends over time."""
    
    def __init__(self, config: Optional[ResearchConfig] = None):
        self.config = config or ResearchConfig(depth=ResearchDepth.STANDARD)
        self._llm_client = None
    
    def _get_llm_client(self):
        if self._llm_client is None:
            from ..llm import create_client
            self._llm_client = create_client()
        return self._llm_client
    
    def analyze_trends(
        self, 
        topic: str, 
        start_year: int = 2018, 
        end_year: Optional[int] = None
    ) -> TrendAnalysisResult:
        """Analyze research trends for a topic over time.
        
        Args:
            topic: Research topic to analyze
            start_year: Start year for analysis
            end_year: End year (defaults to current year)
        
        Returns:
            TrendAnalysisResult with trend data
        """
        if end_year is None:
            end_year = datetime.now().year
        
        print("=" * 70)
        print(f"TREND ANALYSIS: {topic}")
        print(f"Period: {start_year} - {end_year}")
        print("=" * 70)
        
        # Collect papers by year
        papers_by_year = self._collect_papers_by_year(topic, start_year, end_year)
        
        # Analyze trends
        yearly_trends = []
        for year in range(start_year, end_year + 1):
            papers = papers_by_year.get(year, [])
            trend = YearlyTrend(
                year=year,
                paper_count=len(papers),
                key_topics=self._extract_topics(papers),
                representative_papers=papers[:3],
            )
            yearly_trends.append(trend)
            print(f"   {year}: {len(papers)} papers")
        
        # Find peak year
        peak_year = max(yearly_trends, key=lambda t: t.paper_count).year
        
        # Calculate growth rate
        if yearly_trends[0].paper_count > 0:
            growth_rate = (yearly_trends[-1].paper_count - yearly_trends[0].paper_count) / yearly_trends[0].paper_count
        else:
            growth_rate = float(yearly_trends[-1].paper_count) if yearly_trends[-1].paper_count > 0 else 0
        
        # Identify emerging and declining topics
        emerging, declining = self._identify_topic_changes(yearly_trends)
        
        # Generate forecast
        forecast = self._generate_forecast(topic, yearly_trends, growth_rate)
        
        # Build report
        md_report = self._build_report(
            topic, start_year, end_year, yearly_trends, 
            emerging, declining, peak_year, growth_rate, forecast
        )
        
        total_papers = sum(t.paper_count for t in yearly_trends)
        print(f"\nTotal papers: {total_papers}")
        print(f"Peak year: {peak_year}")
        print(f"Growth rate: {growth_rate:.1%}")
        
        return TrendAnalysisResult(
            topic=topic,
            start_year=start_year,
            end_year=end_year,
            yearly_trends=yearly_trends,
            emerging_topics=emerging,
            declining_topics=declining,
            peak_year=peak_year,
            growth_rate=growth_rate,
            forecast=forecast,
            markdown_report=md_report,
            metadata={
                "total_papers": total_papers,
                "years_analyzed": end_year - start_year + 1,
            },
        )
    
    def _collect_papers_by_year(
        self, 
        topic: str, 
        start_year: int, 
        end_year: int
    ) -> Dict[int, List[SearchResultSummary]]:
        """Collect papers organized by year."""
        from ..literature_review.providers import ArxivProvider, OpenReviewProvider
        
        papers_by_year = defaultdict(list)
        
        print("\n[1/2] Searching arXiv...")
        try:
            provider = ArxivProvider()
            results = provider.search(topic, limit=50)
            for r in results:
                if r.year and start_year <= r.year <= end_year:
                    papers_by_year[r.year].append(SearchResultSummary(
                        title=r.title,
                        url=r.url,
                        source="arXiv",
                        summary=r.abstract[:200] if r.abstract else "",
                        year=r.year,
                        authors=r.authors[:3] if r.authors else [],
                    ))
            print(f"   Found {len(results)} papers")
        except Exception as e:
            print(f"   Error: {e}")
        
        print("[2/2] Searching OpenReview...")
        try:
            provider = OpenReviewProvider()
            results = provider.search(topic, limit=30)
            for r in results:
                if r.year and start_year <= r.year <= end_year:
                    papers_by_year[r.year].append(SearchResultSummary(
                        title=r.title,
                        url=r.url,
                        source="OpenReview",
                        summary=r.abstract[:200] if r.abstract else "",
                        year=r.year,
                        authors=r.authors[:3] if r.authors else [],
                    ))
            print(f"   Found {len(results)} papers")
        except Exception as e:
            print(f"   Error: {e}")
        
        return dict(papers_by_year)
    
    def _extract_topics(self, papers: List[SearchResultSummary]) -> List[str]:
        """Extract key topics from paper titles."""
        import re
        
        # Common research keywords
        all_words = []
        for p in papers:
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', p.title)
            all_words.extend(words)
        
        # Count frequency
        word_counts = defaultdict(int)
        for w in all_words:
            if len(w) > 3:
                word_counts[w] += 1
        
        # Return top topics
        sorted_words = sorted(word_counts.items(), key=lambda x: -x[1])
        return [w[0] for w in sorted_words[:5]]
    
    def _identify_topic_changes(
        self, 
        trends: List[YearlyTrend]
    ) -> tuple[List[str], List[str]]:
        """Identify emerging and declining topics."""
        if len(trends) < 3:
            return [], []
        
        early_topics = set()
        for t in trends[:len(trends)//2]:
            early_topics.update(t.key_topics)
        
        late_topics = set()
        for t in trends[len(trends)//2:]:
            late_topics.update(t.key_topics)
        
        emerging = list(late_topics - early_topics)[:5]
        declining = list(early_topics - late_topics)[:5]
        
        return emerging, declining
    
    def _generate_forecast(
        self, 
        topic: str, 
        trends: List[YearlyTrend], 
        growth_rate: float
    ) -> str:
        """Generate a forecast for the research area."""
        try:
            client = self._get_llm_client()
            from ..llm import Message
            
            trend_summary = "\n".join([
                f"- {t.year}: {t.paper_count} papers"
                for t in trends
            ])
            
            prompt = f"""Based on this publication trend for "{topic}":

{trend_summary}

Growth rate: {growth_rate:.1%}

Provide a 2-3 sentence forecast for this research area over the next 2-3 years.
Consider: Is it growing? Maturing? What might drive future interest?"""

            response, _ = client.chat([
                Message.system("You are a research trend analyst."),
                Message.user(prompt),
            ])
            return response.content
            
        except Exception as e:
            if growth_rate > 0.5:
                return f"The field shows strong growth ({growth_rate:.0%}). Research interest is likely to continue increasing."
            elif growth_rate > 0:
                return f"The field shows steady growth ({growth_rate:.0%}). Research activity is expected to remain stable."
            else:
                return f"The field shows declining interest. New breakthrough applications may be needed to revive interest."
    
    def _build_report(
        self,
        topic: str,
        start_year: int,
        end_year: int,
        trends: List[YearlyTrend],
        emerging: List[str],
        declining: List[str],
        peak_year: int,
        growth_rate: float,
        forecast: str,
    ) -> str:
        """Build markdown trend report."""
        md = f"# Research Trend Analysis: {topic}\n\n"
        md += f"*Period: {start_year} - {end_year}*\n\n"
        
        md += "## Summary Statistics\n\n"
        total = sum(t.paper_count for t in trends)
        md += f"- **Total Papers Analyzed:** {total}\n"
        md += f"- **Peak Year:** {peak_year}\n"
        md += f"- **Growth Rate:** {growth_rate:.1%}\n\n"
        
        md += "## Publications Over Time\n\n"
        md += "| Year | Papers | Key Topics |\n"
        md += "|------|--------|------------|\n"
        for t in trends:
            topics = ", ".join(t.key_topics[:3]) if t.key_topics else "-"
            md += f"| {t.year} | {t.paper_count} | {topics} |\n"
        md += "\n"
        
        if emerging:
            md += "## Emerging Topics\n\n"
            for e in emerging:
                md += f"- {e}\n"
            md += "\n"
        
        if declining:
            md += "## Declining Topics\n\n"
            for d in declining:
                md += f"- {d}\n"
            md += "\n"
        
        md += "## Forecast\n\n"
        md += f"{forecast}\n\n"
        
        md += "## Representative Papers by Year\n\n"
        for t in trends:
            if t.representative_papers:
                md += f"### {t.year}\n"
                for p in t.representative_papers[:2]:
                    md += f"- [{p.title}]({p.url})\n"
                md += "\n"
        
        return md


def analyze_research_trends(
    topic: str, 
    start_year: int = 2018
) -> TrendAnalysisResult:
    """Convenience function to analyze research trends.
    
    Args:
        topic: Research topic
        start_year: Start year for analysis
    
    Returns:
        TrendAnalysisResult
    
    Example:
        result = analyze_research_trends("transformer neural network", 2017)
    """
    agent = TrendAnalysisAgent()
    return agent.analyze_trends(topic, start_year)
