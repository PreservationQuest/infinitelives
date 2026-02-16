# Infinite Lives v2.0 🎮

A production-ready RAG (Retrieval-Augmented Generation) system for analyzing video game research papers using OpenAI's Assistants API.

## ✨ Features

- **Efficient**: Singleton client with connection pooling and automatic retry logic
- **Secure**: Environment-based configuration, no hardcoded credentials
- **Reliable**: Exponential backoff, timeout handling, and graceful error recovery
- **Flexible**: Batch processing, interactive queries, and optional verification mode
- **Production-ready**: Comprehensive logging, checkpointing, and error handling

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or create project
cd infinite_lives_v2

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_ORG_ID=org-...
MODEL_NAME=gpt-4o-2024-08-06
```

### 3. Place Documents

Put your reference documents in the `docs/` folder:
```bash
mkdir -p docs
cp /path/to/Detailed_Instructions.docx docs/
cp /path/to/Video_Game_Attributes.docx docs/
```

### 4. Setup Assistant

```bash
python -m src.main setup
```

This creates the assistant and vector store. Save the `ASSISTANT_ID` to your `.env` file.

## 📖 Usage

### Process a Dataset

Process a CSV file with research papers:

```bash
# Basic processing
python -m src.main process input.csv -o results.csv

# With two-pass verification (slower but more accurate)
python -m src.main process input.csv -o results.csv --verify
```

**Expected CSV format:**
- `ID`: Paper identifier
- `Subject of Effect`: Category (e.g., "Behavioral", "Psychological")
- `Abstract`, `Introduction`, `Methods`, `Conclusion`: Paper sections
- Other columns preserved in output

### Interactive Queries

Ask questions about video game research:

```bash
python -m src.main query
```

Example queries:
- "What games are studied for cognitive benefits?"
- "Summarize research on violence in video games"
- "What methodologies are common in player behavior studies?"

### Reset Assistant

Delete and recreate the assistant:

```bash
python -m src.main setup --reset
```

## 🏗️ Architecture

```
infinite_lives_v2/
├── src/
│   ├── config.py          # Environment configuration with validation
│   ├── client.py          # OpenAI client with retry logic
│   ├── assistant.py       # Assistant lifecycle management
│   ├── processor.py       # RAG processing pipeline
│   ├── logging_config.py  # Logging setup
│   └── main.py            # CLI interface
├── docs/                  # Reference documents for RAG
├── data/                  # Input/output data
├── logs/                  # Application logs
├── tests/                 # Unit tests (TODO)
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `OPENAI_ORG_ID` | Yes | - | Your OpenAI organization ID |
| `MODEL_NAME` | No | `gpt-4o-2024-08-06` | Model to use |
| `ASSISTANT_ID` | No | - | Cached assistant ID (auto-set) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `MAX_RETRIES` | No | `3` | API retry attempts |
| `REQUEST_TIMEOUT` | No | `60` | Request timeout (seconds) |

### Verification Mode

Enable with `--verify` flag for two-pass processing:

1. **First pass**: Generate response
2. **Second pass**: Verify and correct response

**Trade-offs:**
- ✅ Higher accuracy, catches hallucinations
- ❌ 2x slower, 2x more expensive

## 📊 API Usage Optimization

### What's Different from v1?

| Feature | v1 (Old) | v2 (New) |
|---------|----------|----------|
| Client creation | Multiple instances | Singleton |
| Retry logic | Manual | Exponential backoff |
| Thread cleanup | Manual | Automatic |
| Assistant reuse | Creates new each time | Cached |
| Error handling | Minimal | Comprehensive |
| Logging | Print statements | Professional logger |
| Hardcoded delays | 25s sleep | Dynamic polling |

### Cost Savings

- **Assistant reuse**: Create once, use forever
- **No redundant sleeps**: Poll dynamically instead of waiting 25s
- **Optional verification**: Skip when accuracy isn't critical
- **Efficient threading**: Auto-cleanup prevents orphaned threads

## 🐛 Troubleshooting

### "Configuration validation failed"

Make sure your `.env` file has valid credentials:
```bash
# Check format
cat .env | grep OPENAI
```

### "Rate limit hit"

The system automatically retries with exponential backoff. If persistent:
- Check your OpenAI usage limits
- Reduce concurrent processing
- Increase `MAX_RETRIES` in `.env`

### "No documents found"

Place reference documents in `docs/` folder:
```bash
ls docs/
# Should show: Detailed_Instructions.docx, Video_Game_Attributes.docx
```

## 🔒 Security Best Practices

✅ **DO:**
- Keep `.env` in `.gitignore`
- Use environment variables for secrets
- Rotate API keys regularly
- Review logs before sharing

❌ **DON'T:**
- Commit `.env` to git
- Share API keys in code
- Log full API keys
- Hardcode credentials

## 📝 Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests (TODO)
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint
flake8 src/

# Type check
mypy src/
```

## 🤝 Contributing

1. Follow existing code structure
2. Add logging for debugging
3. Handle errors gracefully
4. Update documentation
5. Add tests for new features

## 📄 License

MIT License - see LICENSE file for details

## 👤 Author

**Ashutosh Khatavkar**
- MS Computer Science, Syracuse University
- Former SDET at Ubisoft Entertainment India
- Specializing in test automation, AI/ML, and game development

## 🙏 Acknowledgments

- OpenAI Assistants API
- Video game research community
- Syracuse University iSchool
