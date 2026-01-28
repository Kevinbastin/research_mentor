"""Report generator for deep research."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class ReportGenerator:
    """Generates formatted research reports."""
    
    def __init__(self):
        pass
    
    def generate_markdown(self, topic: str, summary: str, sources: List[Any], gap_analysis: Optional[str] = None) -> str:
        """Generate a complete markdown report from research findings."""
        markdown = f"# Research Report: {topic}\n\n"
        markdown += f"## Summary\n{summary}\n\n"
        
        if sources:
            markdown += "## Sources\n"
            for s in sources:
                title = getattr(s, "title", str(s))
                markdown += f"- {title}\n"
        
        if gap_analysis:
            markdown += f"\n## Gap Analysis\n{gap_analysis}\n"
        
        return markdown
