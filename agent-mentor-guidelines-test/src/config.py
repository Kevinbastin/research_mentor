import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = "gpt-4"
    TEMPERATURE = 0.1
    
    # Guidelines Sources - Domain mapping for filtering
    GUIDELINE_SOURCES = {
        "gwern.net": "Hamming on research methodology and important problems",
        "lesswrong.com": "Research project selection and evaluation", 
        "colah.github.io": "Research taste and judgment",
        "01.me": "Research taste development",
        "arxiv.org": "Academic papers on research methodology",
        "lifescied.org": "Research process and methodology",
        "trendspider.com": "ML research framing",
        "news.ycombinator.com": "Community discussion on research",
        "cuhk.edu.hk": "Research taste academic perspectives"
    }
    
    # Specific URLs for direct fetching if needed
    GUIDELINE_URLS = [
        "https://gwern.net/doc/science/1986-hamming",
        "https://www.lesswrong.com/posts/kDsywodAKgQAAAxE8/how-not-to-choose-a-research-project",
        "https://news.ycombinator.com/item?id=35776480",
        "https://trendspider.com/learning-center/framing-machine-learning-research/",
        "https://arxiv.org/abs/2412.05683",
        "https://www.lifescied.org/doi/10.1187/cbe.20-12-0276",
        "https://arxiv.org/abs/2304.05585",
        "https://colah.github.io/notes/taste/",
        "https://01.me/en/2024/04/research-taste/",
        "https://home.ie.cuhk.edu.hk/~dmchiu/research_taste.pdf"
    ]