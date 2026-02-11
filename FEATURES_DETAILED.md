# METIS AI Research Mentor - Detailed Feature Documentation

## 📋 Table of Contents
1. [Stage-Aware Mentoring System](#1-stage-aware-mentoring-system)
2. [8 Research Tools](#2-research-tools-suite)
3. [Citation Framework](#3-citation-framework)
4. [Guidelines Engine](#4-guidelines-engine)
5. [Paper Recommendation System](#5-paper-recommendation-system)
6. [Session Memory & Logging](#6-session-memory--logging)
7. [FastAPI + Next.js Web Interface](#7-fastapi--nextjs-web-interface)

---

## 1. Stage-Aware Mentoring System

### Overview
METIS automatically detects which stage of the research writing process the student is in and adapts its responses accordingly.

### The 6 Research Stages

#### **Stage A: Pre-Idea** (Topic Selection)
- **Purpose**: Help students explore and select research topics
- **Keywords detected**: "what should i work on", "brainstorm", "explore ideas", "scope", "clarify"
- **Mentor behavior**: 
  - Asks clarifying questions
  - Helps scope the problem
  - Suggests multiple directions
  - No literature search yet - focus on idea exploration

#### **Stage B: Idea** (Hypothesis Formation)
- **Purpose**: Develop and refine the research hypothesis
- **Keywords detected**: "idea", "hypothesis", "novel", "proposal", "intuition", "approach"
- **Mentor behavior**:
  - Literature search to check novelty
  - Validates if idea is novel/feasible
  - Identifies related work
  - Suggests positioning/angle

#### **Stage C: Research Plan** (Methodology)
- **Purpose**: Design experimental methodology and evaluation plan
- **Keywords detected**: "plan", "methodology", "experiment", "dataset", "metrics", "baseline", "ablation"
- **Mentor behavior**:
  - Deep research on methodology
  - Suggests evaluation metrics
  - Validates experimental design
  - Checks feasibility and risks

#### **Stage D: First Draft** (Initial Results)
- **Purpose**: Write initial paper draft with baseline results
- **Keywords detected**: "draft", "baseline", "preliminary results", "writeup", "figure"
- **Mentor behavior**:
  - Document-grounded responses (uses uploaded PDFs)
  - Structural feedback on sections
  - Validates claims with citations
  - Checks figure quality

#### **Stage E: Second Draft** (Revision)
- **Purpose**: Polish paper based on feedback
- **Keywords detected**: "revision", "revise", "reviewer", "checklist", "polish", "proof check"
- **Mentor behavior**:
  - Detailed proofreading
  - Mathematical notation checks
  - Citation completeness
  - Addresses reviewer comments

#### **Stage F: Final** (Submission Ready)
- **Purpose**: Final checks before submission
- **Keywords detected**: "venue", "submission", "camera ready", "final", "simulate review"
- **Mentor behavior**:
  - Venue-specific requirements check
  - Formatting validation
  - Simulates peer review
  - Final quality assessment

### Implementation Details
```python
# File: src/academic_research_mentor/core/stage_detector.py

def detect_stage(user_text: str) -> Dict[str, object]:
    """
    Returns: {"code": "A-F", "name": "Stage name", "confidence": 0.0-0.9}
    
    Confidence calculation:
    - 0 matches: 0.30-0.35 (fallback to Stage A)
    - 1 match: 0.55
    - 2+ matches: 0.65-0.90
    """
```

### Stage Routing Impact
- **Stages A-C**: More exploratory, uses web search + literature tools
- **Stages D-F**: Document-grounded (requires PDF upload), citation-heavy
- Confidence threshold: 0.45 for stage-specific routing

---

## 2. Research Tools Suite

METIS provides **8 specialized tools** that the agent can invoke automatically:

### Tool 1: **literature_search** 
**Purpose**: Multi-provider academic paper search

**How it works**:
```python
# Uses all 5 FREE providers simultaneously
providers = ["arXiv", "openreview", "pubmed", "hal", "zenodo"]
# Fetches 5 papers from each = 25 total
# Returns top 10 most relevant
```

**Parameters**:
- `query` (required): Search query
- `limit` (optional, default=5): Papers per source
- `from_year` (optional): Filter by year

**Returns**:
```json
{
  "sources": [
    {
      "title": "Paper title",
      "authors": ["Author 1", "Author 2"],
      "year": 2023,
      "url": "https://arxiv.org/abs/...",
      "source": "arXiv",
      "summary": "Paper abstract..."
    }
  ],
  "total": 10,
  "providers_used": ["arXiv", "openreview", "pubmed"]
}
```

**Use cases**:
- Stage B: Check novelty
- Stage C: Find methodology papers
- Stage D-F: Find citations

---

### Tool 2: **deep_research**
**Purpose**: Comprehensive research synthesis across all sources

**How it works**:
1. Fetches 10 papers per provider (50 total)
2. Scores every paper by keyword relevance
3. Selects top 10 globally
4. Uses qwen2.5:14b LLM to synthesize:
   - Executive summary (3 paragraphs)
   - 7 key research themes
   - Methodological approaches
   - Cross-source insights
   - Research gaps
   - Future directions

**Parameters**:
- `topic` (required): Research topic
- `depth` (optional): "shallow", "standard" (default), "deep"

**Returns**:
```json
{
  "topic": "Research topic",
  "summary": "LLM-generated synthesis...",
  "key_themes": ["Theme 1", "Theme 2", ...],
  "sources": [/* top 10 papers */],
  "markdown_report": "# Research Report: ...",
  "metadata": {
    "total_fetched": 49,
    "top_k": 10,
    "arXiv": 6,
    "pubmed": 3,
    "openreview": 1
  }
}
```

**Use cases**:
- Stage B: Understand research landscape
- Stage C: Identify methodology trends
- Literature review sections

---

### Tool 3: **compare_approaches**
**Purpose**: Side-by-side comparison of 2-4 research approaches

**How it works**:
1. Searches literature for each approach
2. Synthesizes pros/cons
3. Generates comparison matrix
4. Recommends best use cases

**Parameters**:
- `approaches` (required): List of 2-4 approaches
- `context` (optional): Specific application context

**Example**:
```python
compare_approaches(
    approaches=["CNN", "Transformer", "RNN"],
    context="image classification"
)
```

**Returns**:
- Comparison table (strengths/weaknesses)
- Performance metrics
- Use-case recommendations
- Trade-offs

**Use cases**:
- Stage C: Choose methodology
- Related work sections
- Baseline selection

---

### Tool 4: **analyze_trends**
**Purpose**: Identify emerging research trends over time

**How it works**:
1. Searches papers from last 5 years
2. Groups by publication year
3. LLM identifies patterns:
   - Rising topics
   - Declining approaches
   - Emerging methods
   - Research gaps

**Parameters**:
- `domain` (required): Research domain
- `time_span` (optional, default=5): Years to analyze

**Returns**:
- Trend timeline
- Hot topics
- Cold topics
- Predicted future directions

**Use cases**:
- Stage A: Identify promising areas
- Stage B: Position novelty
- Introduction sections

---

### Tool 5: **find_similar_papers**
**Purpose**: Paper recommendation based on DOI/arXiv ID/title

**How it works**:
1. Uses **OpenAlex API** (FREE, unlimited)
2. Finds papers via:
   - Related works graph
   - Citation network
   - Keyword similarity
3. Ranks by citation count + similarity score

**Parameters**:
- `paper_id` (required): DOI, arXiv ID, or title
- `limit` (optional, default=10): Max recommendations

**Returns**:
```json
{
  "papers": [
    {
      "title": "Similar paper",
      "similarity_score": 0.85,
      "citation_count": 42,
      "recommendation_reason": "cites this paper",
      "pdf_url": "https://...",
      "year": 2023
    }
  ]
}
```

**Use cases**:
- Discover related work
- Expand literature review
- Find recent follow-ups

---

### Tool 6: **arxiv_search**
**Purpose**: Dedicated arXiv search (faster than multi-provider)

**How it works**:
- Direct arXiv API query
- Supports advanced search:
  - By category (cs.LG, cs.CV, etc.)
  - By date range
  - By author
- Returns up to 25 results

**Parameters**:
- `query` (required)
- `from_year` (optional)
- `limit` (optional, default=10)
- `sort_by` (optional): "relevance" or "date"

**Use cases**:
- Quick arXiv-only search
- Category-specific queries
- Recent papers (last 6 months)

---

### Tool 7: **web_search**
**Purpose**: General web search (news, blogs, documentation)

**How it works**:
- Uses Tavily API (if key available) or fallback
- Searches:
  - News articles
  - Blog posts
  - GitHub repos
  - Documentation

**Parameters**:
- `query` (required)
- `limit` (optional, default=5)

**Returns**:
- Titles, URLs, snippets
- Publication dates
- Domain sources

**Use cases**:
- Current events (not in papers yet)
- Software documentation
- Industry trends
- Dataset repositories

---

### Tool 8: **research_guidelines**
**Purpose**: Domain-specific research best practices

**How it works**:
1. Detects research domain (AI/ML, HCI, Systems, etc.)
2. Loads stage-specific guidelines
3. Returns curated advice

**Parameters**:
- `domain` (optional): Auto-detected if not provided
- `stage` (optional): Auto-detected from conversation

**Returns**:
- Checklist of best practices
- Common pitfalls to avoid
- Recommended methodologies
- Evaluation metrics

**Use cases**:
- Stage C: Methodology validation
- Stage E: Checklist review
- Stage F: Submission requirements

---

## 3. Citation Framework

### Overview
Ensures all research claims are properly cited and validated.

### Components

#### **3.1 Citation Model**
```python
@dataclass
class Citation:
    id: str              # Unique identifier
    title: str           # Paper title
    url: str             # Landing page
    source: str          # "arXiv", "openreview", etc.
    authors: List[str]   # Author names
    year: int            # Publication year
    venue: str           # Conference/journal
    doi: str             # Digital Object Identifier (optional)
    snippet: str         # Relevant excerpt (optional)
    relevance_score: float  # 0.0-1.0
```

#### **3.2 Citation Validator**
**Purpose**: Quality checks for citations

**Validation checks**:
1. **Required fields**:
   - Title (min 3 chars): -30 points if missing
   - URL (valid format): -25 points if missing
   - Authors (≥1): -15 points if missing
   - Year (1900-2030): -10 points if missing

2. **Optional fields**:
   - Venue: -5 points if missing
   - DOI: -2 points if missing
   - Snippet: -5 points if missing

**Scoring**:
- Perfect citation: 100 points
- Valid citation: ≥70 points
- Completeness: % of fields filled

**Example**:
```python
validator = CitationValidator()
result = validator.validate_citation(citation)
# result = {
#   "valid": True,
#   "score": 85.0,
#   "issues": ["No venue specified", "No DOI available"],
#   "completeness": 71.4
# }
```

#### **3.3 Evidence Grading**
Citations are graded A-F based on:
- **Grade A**: Peer-reviewed journal, ≥50 citations, <2 years old
- **Grade B**: Peer-reviewed conference, ≥20 citations
- **Grade C**: Preprint (arXiv), ≥10 citations
- **Grade D**: Preprint, <10 citations
- **Grade E**: Web source, blog post
- **Grade F**: Invalid/broken citation

#### **3.4 DOI Verification**
Uses Crossref API to verify DOIs:
```python
def verify_doi(doi: str) -> bool:
    response = requests.get(f"https://api.crossref.org/works/{doi}")
    return response.status_code == 200
```

#### **3.5 Citation Enforcement**
- LLM responses must include citations for factual claims
- Tool outputs include source tracking
- Markdown format: `[Paper Title](URL) (Author et al., 2023)`

---

## 4. Guidelines Engine

### Overview
Loads and injects domain-specific research guidelines into the agent's context.

### Architecture

#### **4.1 GuidelinesLoader**
Loads guidelines from markdown files:
```
guidelines/
  ├── ai_ml.md         # AI/ML research
  ├── hci.md           # Human-Computer Interaction
  ├── systems.md       # Systems research
  ├── theory.md        # Theoretical CS
  └── general.md       # Cross-domain guidelines
```

#### **4.2 GuidelinesFormatter**
Formats guidelines for injection:
```python
def format_guidelines(domain: str, stage: str) -> str:
    """
    Returns stage-specific guidelines like:
    
    ## Stage C: Research Plan
    - [ ] Choose appropriate baseline models
    - [ ] Define evaluation metrics
    - [ ] Consider ethical implications
    - [ ] Plan ablation studies
    """
```

#### **4.3 GuidelinesInjector**
Injects guidelines into LLM prompts:
```python
def inject_guidelines(prompt: str, domain: str, stage: str) -> str:
    guidelines = formatter.format(domain, stage)
    return f"{prompt}\n\n## Research Guidelines\n{guidelines}"
```

### Guidelines Content

#### **AI/ML Research Guidelines** (ai_ml.md)
- **Stage A**: Problem selection criteria (impact, novelty, feasibility)
- **Stage B**: Novelty check (search existing solutions, position your contribution)
- **Stage C**: Methodology (baselines, datasets, metrics, ablation plan)
- **Stage D**: Results (statistical significance, error bars, failure analysis)
- **Stage E**: Writing (clear claims, limitations section, reproducibility)
- **Stage F**: Submission (venue fit, checklist, formatting)

#### **HCI Research Guidelines** (hci.md)
- IRB approval requirements
- User study design (sample size, demographics, consent)
- Qualitative vs quantitative methods
- Usability metrics (SUS, task completion time)
- Accessibility considerations

#### **Systems Research Guidelines** (systems.md)
- Performance benchmarks
- Scalability analysis
- Comparison with state-of-the-art
- Reproducibility (code release, hardware specs)
- Real-world deployment considerations

---

## 5. Paper Recommendation System

### Overview
100% FREE paper discovery using OpenAlex API.

### Features

#### **5.1 Find Similar Papers**
```python
def find_similar(paper_id: str, limit: int = 10):
    """
    Input: DOI, arXiv ID, or title
    
    Algorithm:
    1. Get paper metadata from OpenAlex
    2. Fetch "related_works" from OpenAlex graph
    3. Rank by:
       - Similarity score (keyword overlap)
       - Citation count
       - Recency
    
    Output: Top 10 recommendations with:
    - Title, authors, year
    - PDF link (if open access)
    - Similarity score
    - Recommendation reason
    """
```

**Example**:
```python
papers = find_similar("10.1234/example.doi", limit=10)
# papers[0] = {
#   "title": "Similar Paper Title",
#   "similarity_score": 0.85,
#   "citation_count": 42,
#   "recommendation_reason": "cites this paper",
#   "pdf_url": "https://arxiv.org/pdf/...",
#   "year": 2023,
#   "venue": "NeurIPS"
# }
```

#### **5.2 Find Citing Papers**
```python
def find_citing_papers(doi: str, limit: int = 10):
    """
    Input: DOI
    
    Algorithm:
    1. Query OpenAlex: filter=cites:doi:{doi}
    2. Sort by citation count (descending)
    3. Return top 10
    
    Use case: Track impact, find follow-up work
    """
```

#### **5.3 Find Referenced Papers**
```python
def find_referenced_papers(doi: str, limit: int = 10):
    """
    Input: DOI
    
    Algorithm:
    1. Get paper metadata
    2. Extract "referenced_works" list
    3. Fetch metadata for each reference
    
    Use case: Build citation network, find foundational papers
    """
```

#### **5.4 PDF Link Resolution**
```python
def get_paper_pdf_link(paper_id: str) -> str:
    """
    Tries in order:
    1. arXiv PDF (if arXiv ID)
    2. Unpaywall (open access database)
    3. OpenAlex OA links
    4. PubMed Central (if PMC ID)
    
    Returns: Direct PDF URL or None
    """
```

### OpenAlex API Details
- **Endpoint**: `https://api.openalex.org`
- **Rate limit**: Unlimited (polite usage recommended)
- **Coverage**: 200M+ works, 10M+ authors
- **Features**:
  - Citation network
  - Open access links
  - Author profiles
  - Institution data

---

## 6. Session Memory & Logging

### Overview
Comprehensive conversation tracking and transparency logging.

### Components

#### **6.1 SessionLogManager**
```python
class SessionLogManager:
    def __init__(self, log_dir="convo-logs"):
        """
        Creates session directory:
        convo-logs/
          └── chat_20260211_143052/
              ├── chat_20260211_143052_events.jsonl
              └── chat_20260211_143052_session.json
        """
```

#### **6.2 Event Types**
Logs are stored as JSONL (one event per line):

1. **session_started**
```json
{"event": "session_started", "timestamp_ms": 1707662652000, "metadata": {...}}
```

2. **turn_started**
```json
{"event": "turn_started", "turn": 1, "user_prompt": "How do transformers work?", ...}
```

3. **stage_detected**
```json
{"event": "stage_detected", "stage": {"code": "B", "name": "Idea", "confidence": 0.65}}
```

4. **tool_calls**
```json
{"event": "tool_calls", "tool_calls": [{"name": "literature_search", "args": {...}}]}
```

5. **tool_run_linked**
```json
{"event": "tool_run_linked", "run_id": "run_abc123", "tool": "deep_research"}
```

6. **turn_finalized**
```json
{"event": "turn_finalized", "turn": 1, "response": "...", "tokens": 523, ...}
```

7. **session_closed**
```json
{"event": "session_closed", "exit_command": "/quit", "total_turns": 5}
```

#### **6.3 Transparency Recording**
Every tool call is logged with:
- Tool name and parameters
- Execution time
- Output summary
- Error messages (if any)

**Example transparency log**:
```json
{
  "run_id": "run_20260211_143102",
  "tool": "literature_search",
  "args": {"query": "transformer attention", "limit": 5},
  "started_ms": 1707662662000,
  "ended_ms": 1707662668000,
  "duration_ms": 6000,
  "output_summary": "Found 10 papers across 3 providers",
  "providers_used": ["arXiv", "openreview", "pubmed"],
  "error": null
}
```

#### **6.4 Session Metadata**
Stored in `*_session.json`:
```json
{
  "session_id": "chat_20260211_143052",
  "started_ms": 1707662652000,
  "ended_ms": 1707662950000,
  "total_turns": 5,
  "total_tools_called": 8,
  "stages_detected": ["B", "C", "C", "D", "D"],
  "documents_uploaded": 1,
  "exit_command": "/quit"
}
```

### Use Cases
- **Debugging**: Trace tool execution errors
- **Research**: Analyze conversation patterns
- **Audit**: Verify citations and sources
- **Replay**: Reconstruct conversation flow

---

## 7. FastAPI + Next.js Web Interface

### Backend: FastAPI Server

#### **7.1 Server Architecture**
```python
# File: src/academic_research_mentor/server.py

app = FastAPI(title="Academic Research Mentor API")

# Global instances
mentor_agent: MentorAgent  # Core agent
supermemory_client: Supermemory  # Optional memory store
document_store: dict  # Uploaded PDFs
```

#### **7.2 API Endpoints**

**POST /chat** - Main chat endpoint
```python
@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Request:
    {
      "prompt": "User message",
      "document_context": "Optional PDF text",
      "content_parts": []  # For vision/multimodal
    }
    
    Response:
    {
      "response": "Mentor reply",
      "reasoning": "Optional reasoning trace"
    }
    """
```

**POST /stream** - Streaming chat
```python
@app.post("/stream")
async def stream_chat(request: ChatRequest) -> StreamingResponse:
    """
    Returns SSE (Server-Sent Events) stream:
    
    data: {"content": "Hello", "reasoning": null}
    data: {"content": " world", "reasoning": null}
    data: {"content": null, "reasoning": "Thinking..."}
    data: [DONE]
    """
```

**POST /upload** - Upload research document
```python
@app.post("/upload")
async def upload_document(file: UploadFile) -> UploadResponse:
    """
    Accepts: PDF, DOCX, TXT
    
    Process:
    1. Save to temp file
    2. Extract text (PyMuPDF for PDF, python-docx for DOCX)
    3. Store in document_store with UUID
    4. Optionally index in Supermemory
    
    Response:
    {
      "id": "doc_uuid",
      "filename": "paper.pdf",
      "content": "Extracted text...",
      "pages": 10
    }
    """
```

**POST /title** - Generate chat title
```python
@app.post("/title")
async def generate_title(request: TitleRequest) -> TitleResponse:
    """
    Uses LLM to generate semantic title from first message.
    
    Request: {"text": "How do transformers work?"}
    Response: {"title": "Transformer Architecture Basics"}
    """
```

**GET /health** - Health check
```python
@app.get("/health")
def health():
    return {"status": "ok", "agent": mentor_agent is not None}
```

#### **7.3 CORS Configuration**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### **7.4 Document Processing**

**PDF Extraction** (PyMuPDF):
```python
def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    import fitz
    doc = fitz.open(file_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append(f"[Page {i+1}]\n{text}")
    return "\n\n".join(pages), len(doc)
```

**DOCX Extraction** (python-docx):
```python
def extract_text_from_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n\n".join(p.text for p in doc.paragraphs)
```

---

### Frontend: Next.js UI

#### **7.5 Frontend Architecture**
```
web/
├── src/
│   ├── app/
│   │   ├── page.tsx           # Main chat page
│   │   └── layout.tsx         # Root layout
│   ├── components/
│   │   ├── ChatInterface.tsx  # Chat UI
│   │   ├── MessageList.tsx    # Message history
│   │   ├── InputBar.tsx       # Message input
│   │   ├── DocumentUpload.tsx # PDF upload
│   │   └── Sidebar.tsx        # Chat history
│   ├── lib/
│   │   └── api.ts             # API client
│   └── store/
│       └── chatStore.ts       # Zustand state
├── public/
├── package.json
└── tailwind.config.ts
```

#### **7.6 Key Features**

**Real-time Streaming**:
```typescript
// lib/api.ts
async function* streamChat(prompt: string) {
  const response = await fetch('/stream', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        yield data;
      }
    }
  }
}
```

**Markdown Rendering**:
```tsx
import ReactMarkdown from 'react-markdown';

<ReactMarkdown
  components={{
    code: CodeBlock,
    a: LinkComponent,
    img: ImageComponent,
  }}
>
  {message.content}
</ReactMarkdown>
```

**PDF Upload**:
```tsx
<input
  type="file"
  accept=".pdf,.docx,.txt"
  onChange={async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    const result = await fetch('/upload', {
      method: 'POST',
      body: formData,
    });
    
    const data = await result.json();
    // Store document ID for context
  }}
/>
```

**Chat History**:
```typescript
// store/chatStore.ts
interface ChatStore {
  conversations: Conversation[];
  activeConversation: string;
  addMessage: (msg: Message) => void;
  newConversation: () => void;
  deleteConversation: (id: string) => void;
}
```

#### **7.7 UI Features**
- ✅ **Syntax highlighting** for code blocks (Prism.js)
- ✅ **LaTeX rendering** for math equations (KaTeX)
- ✅ **Citation links** - clickable DOI/arXiv links
- ✅ **Dark/light mode** toggle
- ✅ **Responsive design** (mobile, tablet, desktop)
- ✅ **Copy to clipboard** for code/responses
- ✅ **Export chat** (JSON, Markdown)
- ✅ **Stage indicator** - shows detected research stage
- ✅ **Tool activity** - displays when tools are running

---

## 🚀 Starting the System

### Backend
```bash
cd /home/urk23cs7081/ai-research-mentor
PYTHONPATH=src python3 -m uvicorn academic_research_mentor.server:app --reload --port 8000
```

### Frontend
```bash
cd /home/urk23cs7081/ai-research-mentor/web
npm run dev
# Opens http://localhost:3000
```

### Full Stack
```bash
# Terminal 1: Start Ollama Docker
docker start ollama

# Terminal 2: Backend
cd ai-research-mentor
PYTHONPATH=src uvicorn academic_research_mentor.server:app --port 8000

# Terminal 3: Frontend
cd ai-research-mentor/web
npm run dev
```

---

## 📊 Performance Metrics

### Response Times (Average)
- **Literature search**: 5-8 seconds (5 providers × 10 papers)
- **Deep research**: 25-35 seconds (fetch 50 → rank 10 → LLM synthesis)
- **Chat (simple)**: 1-3 seconds (qwen2.5:14b local)
- **Chat (with tools)**: 10-15 seconds (tool call + LLM)

### Resource Usage
- **Memory**: ~12GB RAM (qwen2.5:14b model)
- **GPU**: 32GB VRAM (RTX 5090)
- **Disk**: ~500MB per session (logs + documents)

### Scalability
- **Concurrent users**: 1-5 (single GPU)
- **Sessions per day**: Unlimited (local deployment)
- **Cost**: $0 (100% FREE)

---

## 🎓 Academic Validation

From the METIS research paper:
- **Evaluation dataset**: 90 single-turn prompts × 6 stages
- **Comparison**: GPT-5, Claude Sonnet 4.5
- **LLM judges**: GPT-4o, Claude Opus
- **Results**:
  - **71%** preference over Claude Sonnet 4.5
  - **54%** preference over GPT-5
  - Strongest in Stages D-F (document-grounded)
  - Student rubric scores higher across all stages

