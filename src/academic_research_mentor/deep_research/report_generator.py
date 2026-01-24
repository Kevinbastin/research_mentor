"""Research report generator for producing publication-quality markdown reports."""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
 from .deep_research_agent import ResearchReport, SearchResultSummary


class ReportGenerator:
 """Generate publication-quality markdown research reports."""

 @staticmethod
 def generate(report: "ResearchReport") -> str:
 """Generate a complete markdown report from research findings.
 
 Args:
 report: ResearchReport object with all findings
 
 Returns:
 Complete markdown report as string
 """
 sections = []
 
 # Header
 sections.append(f"# Research Report: {report.topic}")
 sections.append(f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
 sections.append(f"*Sources reviewed: {len(report.sources)}*\n")
 
 # Executive Summary
 sections.append("## Executive Summary\n")
 sections.append(report.summary)
 sections.append("")
 
 # Key Themes
 if report.key_themes:
 sections.append("## Key Themes\n")
 for i, theme in enumerate(report.key_themes, 1):
 sections.append(f"{i}. **{theme}**")
 sections.append("")
 
 # Literature Review
 sections.append("## Literature Review\n")
 
 # Group by source
 sources_by_type: dict[str, list] = {}
 for source in report.sources:
 if source.source not in sources_by_type:
 sources_by_type[source.source] = []
 sources_by_type[source.source].append(source)
 
 for source_type, sources in sources_by_type.items():
 sections.append(f"### {source_type.title()} Sources\n")
 
 for source in sources:
 year_str = f" ({source.year})" if source.year else ""
 citation_str = f" - {source.citations} citations" if source.citations else ""
 
 sections.append(f"#### [{source.title}]({source.url}){year_str}")
 sections.append(f"\n{source.summary}")
 
 if source.key_findings:
 sections.append("\n**Key Findings:**")
 for finding in source.key_findings:
 sections.append(f"- {finding}")
 
 sections.append(f"\n*Source: {source.source}{citation_str}*\n")
 
 # Gap Analysis
 if report.gap_analysis:
 sections.append("## Research Gap Analysis\n")
 sections.append(report.gap_analysis)
 sections.append("")
 
 # Future Directions
 if report.future_directions:
 sections.append("## Future Research Directions\n")
 for i, direction in enumerate(report.future_directions, 1):
 sections.append(f"{i}. {direction}")
 sections.append("")
 
 # Methodology Recommendations
 if report.methodology_recommendations:
 sections.append("## Methodology Recommendations\n")
 sections.append(report.methodology_recommendations)
 sections.append("")
 
 # Bibliography
 sections.append("## References\n")
 for i, source in enumerate(report.sources, 1):
 authors = source.title # Use title as fallback
 year = source.year or "n.d."
 sections.append(f"{i}. {authors} ({year}). [{source.title}]({source.url})")
 
 sections.append("")
 
 # Metadata footer
 if report.metadata:
 sections.append("---")
 sections.append("\n*Report metadata:*")
 for key, value in report.metadata.items():
 sections.append(f"- {key}: {value}")
 
 return "\n".join(sections)

 @staticmethod
 def generate_brief(report: "ResearchReport") -> str:
 """Generate a brief summary suitable for chat responses.
 
 Args:
 report: ResearchReport object
 
 Returns:
 Brief markdown summary
 """
 lines = [
 f"## Research Summary: {report.topic}\n",
 report.summary,
 "",
 ]
 
 if report.key_themes:
 lines.append("**Key Themes:**")
 for theme in report.key_themes[:3]:
 lines.append(f"- {theme}")
 lines.append("")
 
 lines.append(f"*Reviewed {len(report.sources)} sources across multiple databases.*")
 
 if report.gap_analysis:
 lines.append("\n**Notable Gap:** " + report.gap_analysis[:200])
 if len(report.gap_analysis) > 200:
 lines.append("...")
 
 return "\n".join(lines)

 @staticmethod
 def generate_citations(report: "ResearchReport", style: str = "apa") -> str:
 """Generate formatted citations in specified style.
 
 Args:
 report: ResearchReport object
 style: Citation style ("apa", "mla", "chicago")
 
 Returns:
 Formatted citations string
 """
 if style == "apa":
 citations = []
 for source in report.sources:
 year = source.year or "n.d."
 # Simplified APA format
 citations.append(
 f"{source.title}. ({year}). Retrieved from {source.url}"
 )
 return "\n".join(citations)
 
 # Default to simple format
 return "\n".join([
 f"- {s.title} ({s.year or 'n.d.'}): {s.url}"
 for s in report.sources
 ])