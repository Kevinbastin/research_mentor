#!/bin/bash
# Quick verification script for Docker container 16f34e20f044

echo "=================================================="
echo "  METIS AI Research Mentor — Container Test"
echo "=================================================="
echo ""

# Check Python
echo "1. Python version:"
python3 --version
echo ""

# Check if we're in the right directory
echo "2. Current directory:"
pwd
ls -la | head -10
echo ""

# Check if source code is available
echo "3. Source code check:"
if [ -d "src/academic_research_mentor" ]; then
    echo "   ✅ Source code found"
    ls src/academic_research_mentor/ | head -5
else
    echo "   ❌ Source code not found. Mount your code at /workspace/ai-research-mentor"
    exit 1
fi
echo ""

# Check Ollama connectivity
echo "4. Ollama connectivity:"
for url in "http://localhost:11434" "http://172.17.0.3:11434" "http://host.docker.internal:11434"; do
    if curl -s -m 2 "$url/api/tags" > /dev/null 2>&1; then
        echo "   ✅ Reachable: $url"
        MODEL=$(curl -s "$url/api/tags" | python3 -c 'import json,sys; print(json.load(sys.stdin)["models"][0]["name"])' 2>/dev/null || echo "unknown")
        echo "      Model: $MODEL"
        break
    else
        echo "   ❌ Not reachable: $url"
    fi
done
echo ""

# Check dependencies
echo "5. Python dependencies:"
export PYTHONPATH=src
python3 -c "
import sys
sys.path.insert(0, 'src')

deps = []
try:
    import fastapi
    deps.append('fastapi')
except:
    print('   ❌ fastapi not installed (run: pip install fastapi)')

try:
    import uvicorn
    deps.append('uvicorn')
except:
    print('   ❌ uvicorn not installed (run: pip install uvicorn)')

if deps:
    print(f'   ✅ Found: {deps}')
"
echo ""

# Test server imports
echo "6. Server import test:"
export PYTHONPATH=src
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from academic_research_mentor.server import app
    print('   ✅ Server imports successfully')
    print(f'      App title: {app.title}')
    routes = [r.path for r in app.routes if hasattr(r, \"path\")]
    print(f'      Routes: {len(routes)} endpoints')
except Exception as e:
    print(f'   ❌ Import failed: {e}')
    sys.exit(1)
" || exit 1
echo ""

# Test LLM client
echo "7. LLM client test:"
export PYTHONPATH=src
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from academic_research_mentor.llm.client import _detect_ollama_url
    url = _detect_ollama_url()
    if url:
        print(f'   ✅ Ollama detected at: {url}')
    else:
        print('   ⚠️  Ollama not detected (but will retry at runtime)')
except Exception as e:
    print(f'   ❌ LLM client test failed: {e}')
" 
echo ""

# GPU check
echo "8. GPU availability:"
if command -v nvidia-smi &> /dev/null; then
    GPU=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1)
    if [ -n "$GPU" ]; then
        echo "   ✅ GPU: $GPU"
    else
        echo "   ⚠️  nvidia-smi found but no GPU info"
    fi
else
    echo "   ⚠️  nvidia-smi not available (OK for CPU mode)"
fi
echo ""

echo "=================================================="
echo "  All checks complete!"
echo "=================================================="
echo ""
echo "To start the backend server:"
echo "  export PYTHONPATH=src"
echo "  python3 -m uvicorn academic_research_mentor.server:app --host 0.0.0.0 --port 8000"
echo ""
echo "Then test from host machine:"
echo "  curl http://localhost:8000/health | python3 -m json.tool"
echo ""
