from __future__ import annotations

import os
from typing import Any, Dict, List

from ..mentor_tools import arxiv_search


def topics_to_search_query(topics: List[str]) -> str:
    import re

    joined = " ".join(topics or [])
    no_paren = re.sub(r"\([^)]*\)", " ", joined)
    norm = no_paren.replace("/", " ")
    raw_tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-]{1,}\b", norm.lower())

    variant_map = {
        "datasets": "dataset",
        "lmms": "lmm",
        "llms": "llm",
        "preprints": "arxiv",
        "pdfs": "pdf",
        "open-source": "open source",
    }
    tokens: List[str] = []
    seen: set[str] = set()
    for t in raw_tokens:
        t = variant_map.get(t, t)
        if t not in seen:
            seen.add(t)
            tokens.append(t)

    stop = {
        "the","and","for","are","but","not","you","all","can","has","have","had",
        "one","two","new","now","old","see","use","using","with","via","from","into",
        "scale","scaling","build","building","project","source","open","large","large-scale",
        "strategy","strategies","resources","models","model","data","collection","sourcing",
        "curation","strategies","best","practices","mix","available","currently",
    }
    filtered = [t for t in tokens if t not in stop and len(t) >= 3]

    priority = [
        "multimodal","dataset","lmm","llm","vision-language","vlm","vision","image","text",
        "arxiv","pdf","html","pretraining","pretrain","benchmark","survey",
    ]

    def sort_key(tok: str) -> tuple[int, int]:
        try:
            idx = priority.index(tok)
        except ValueError:
            idx = len(priority)
        return (idx, -len(tok))

    ordered = sorted(filtered, key=sort_key)
    core = ordered[:5] if ordered else (tokens[:5] if tokens else [])
    return " ".join(core) or " ".join((topics or [])[:3])


def perform_literature_searches(topics: List[str], relax: bool = False) -> Dict[str, Any]:
    """Search ALL 5 FREE providers: arXiv, OpenReview, PubMed, HAL, Zenodo."""
    query = topics_to_search_query(topics)
    limit = 10 if relax else 5

    # Import all FREE providers
    from .providers import (
        ArxivProvider,
        OpenReviewProvider,
        PubMedProvider,
        HALProvider,
        ZenodoProvider,
    )

    search_results = {
        "arxiv": {"papers": []},
        "openreview": {"threads": []},
        "pubmed": {"papers": []},
        "hal": {"papers": []},
        "zenodo": {"papers": []},
        "all_papers": [],
    }

    providers = [
        ("arxiv", ArxivProvider, "papers"),
        ("openreview", OpenReviewProvider, "threads"),
        ("pubmed", PubMedProvider, "papers"),
        ("hal", HALProvider, "papers"),
        ("zenodo", ZenodoProvider, "papers"),
    ]

    for name, ProviderClass, key in providers:
        try:
            provider = ProviderClass()
            results = provider.search(query, limit=limit)
            papers = [
                {
                    "title": r.title,
                    "authors": r.authors,
                    "abstract": r.abstract,
                    "url": r.url,
                    "year": r.year,
                    "source": name,
                    "pdf_url": r.metadata.get("pdf_url"),
                    "arxiv_id": r.metadata.get("arxiv_id"),
                }
                for r in results
            ]
            search_results[name][key] = papers
            search_results["all_papers"].extend(papers)
            print(f"   ✓ {name}: {len(papers)} papers")
        except Exception as e:
            print(f"   ✗ {name}: {e}")
            search_results[name][key] = []

    print(f"📊 Total: {len(search_results['all_papers'])} papers from 5 sources")
    return search_results


def has_meaningful_results(search_results: Dict[str, Any]) -> bool:
    arxiv_papers = search_results.get("arxiv", {}).get("papers", [])
    openreview_threads = search_results.get("openreview", {}).get("threads", [])
    pubmed_papers = search_results.get("pubmed", {}).get("papers", [])
    hal_papers = search_results.get("hal", {}).get("papers", [])
    zenodo_papers = search_results.get("zenodo", {}).get("papers", [])
    return (len(arxiv_papers) > 0 or len(openreview_threads) > 0 or 
            len(pubmed_papers) > 0 or len(hal_papers) > 0 or len(zenodo_papers) > 0)
