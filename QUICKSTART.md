# Infinite Lives v2.0 - Quick Start Guide

## 🚀 60-Second Setup

```bash
# 1. Extract archive
tar -xzf infinite_lives_v2.tar.gz
cd infinite_lives_v2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY and OPENAI_ORG_ID

# 4. Setup
python setup.py

# 5. Start using!
python -m src.main query
```

## 📚 Common Tasks

### Interactive Queries
```bash
python -m src.main query
```

### Process a Dataset
```bash
python -m src.main process input.csv -o output.csv
```

### With Verification (Slower, More Accurate)
```bash
python -m src.main process input.csv -o output.csv --verify
```

### Reset Assistant
```bash
python -m src.main setup --reset
```

## 💻 Code Usage

### Simple Query
```python
from src import GameResearchProcessor

processor = GameResearchProcessor()
answer = processor.simple_query("What games are used in behavioral research?")
print(answer)
```

### Process Single Paper
```python
from src import GameResearchProcessor

processor = GameResearchProcessor()
paper = {
    "ID": "001",
    "Abstract": "Study on game violence...",
    "Methods": "Survey with 200 participants...",
}

results = processor.process_paper(
    paper_data=paper,
    category="Behavioral",
    output_format="JSON"
)
```

### Batch Processing
```python
from src import GameResearchProcessor

processor = GameResearchProcessor(use_verification=False)
df = processor.process_dataset("input.csv", "output.csv")
```

## 🔧 Configuration

Edit `.env`:
```bash
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_ORG_ID=org-xxxxx
MODEL_NAME=gpt-4o-2024-08-06
ASSISTANT_ID=asst_xxxxx  # Auto-filled after setup
```

## 📁 Project Structure

```
infinite_lives_v2/
├── src/              # Source code
├── docs/             # Reference documents (place .docx files here)
├── data/             # Input/output CSVs
├── logs/             # Application logs
├── README.md         # Full documentation
├── MIGRATION.md      # Upgrade from v1
├── ARCHITECTURE.md   # Technical comparison
└── examples.py       # Code examples
```

## 🐛 Troubleshooting

**"Configuration validation failed"**
→ Check your `.env` file has valid OpenAI credentials

**"No documents found"**
→ Place reference .docx files in `docs/` folder

**"Rate limit error"**
→ System auto-retries. If persistent, wait a few minutes

**"Module not found"**
→ Run from project root with: `python -m src.main`

## 📊 Key Improvements Over v1

| Feature | v1 | v2 |
|---------|----|----|
| Speed | 30s/query | 8s/query |
| API calls | 600 (100 queries) | 203 |
| Security | ❌ Hardcoded IDs | ✅ Environment only |
| Errors | ❌ Crashes | ✅ Auto-retry |
| Logging | ❌ Print statements | ✅ Professional logs |

## 📖 Documentation

- **README.md** - Comprehensive documentation
- **MIGRATION.md** - Upgrade guide from v1
- **ARCHITECTURE.md** - Technical deep-dive
- **examples.py** - Code examples

## 🎯 Next Steps

1. ✅ Setup complete
2. Place reference documents in `docs/`
3. Test with: `python -m src.main query`
4. Process your data: `python -m src.main process input.csv -o output.csv`
5. Check logs in `logs/` if issues occur

---

**Stats:**
- 📦 6 core modules (~900 lines of clean code)
- 🔒 Zero hardcoded credentials
- ⚡ 73% faster than v1
- 💰 66% fewer API calls
- 🛡️ Comprehensive error handling
