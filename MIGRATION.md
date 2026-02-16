# Migration Guide: v1 → v2

This guide helps you migrate from the old Infinite Lives system to the new v2.0 architecture.

## Quick Comparison

| Aspect | v1 | v2 |
|--------|----|----|
| **Security** | Hardcoded org ID, API key prints | Environment-only, no logging of secrets |
| **Efficiency** | Creates assistant each time | Caches and reuses assistant |
| **Error Handling** | Minimal | Comprehensive with retries |
| **Thread Management** | Manual cleanup | Automatic cleanup |
| **Logging** | Print statements | Professional logger with file output |
| **API Calls** | 25s hardcoded sleep | Dynamic polling |
| **Configuration** | Scattered across files | Centralized in config.py |

## Step-by-Step Migration

### 1. Install New System

```bash
# Navigate to new directory
cd infinite_lives_v2

# Install dependencies
pip install -r requirements.txt
```

### 2. Migrate Environment Variables

**Old (config.py):**
```python
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
print(f"✓ Config loaded: {OPENAI_KEY[:10]}...")  # DON'T DO THIS
```

**New (.env file):**
```bash
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_ORG_ID=org-xxxxx
MODEL_NAME=gpt-4o-2024-08-06
```

### 3. Migrate Documents

```bash
# Copy reference documents
mkdir -p docs/
cp /path/to/old/supporting_documents/*.docx docs/
```

### 4. Update Code Usage

#### Old Way (v1):
```python
from VG_assistant_manager import create_openai_assistant, get_response_from_assistant

# Creates NEW assistant every time (wasteful)
assistant = create_openai_assistant()
response = get_response_from_assistant(
    assistant.id,
    content,
    instructions,
    verify_and_correct=True
)
```

#### New Way (v2):
```python
from src import GameResearchProcessor

# Reuses cached assistant
processor = GameResearchProcessor()
response = processor.assistant.query(content, instructions)

# Or with verification
response = processor.assistant.query_with_verification(content, instructions)
```

### 5. Update Data Processing

#### Old Way (v1):
```python
from custom_RAG import apply_paperwise_sectionwise_summary_to_row

df = prepare_input_file_data(filepath)
# Complex, incomplete function with no error handling
apply_paperwise_sectionwise_summary_to_row(filepath)
```

#### New Way (v2):
```bash
# Command line
python -m src.main process input.csv -o output.csv

# Or in code
from src import GameResearchProcessor

processor = GameResearchProcessor()
result_df = processor.process_dataset("input.csv", "output.csv")
```

## Breaking Changes

### 1. Configuration Access

**Old:**
```python
from config import OPENAI_KEY, OPENAI_ORG, MODEL_NAME
```

**New:**
```python
from src.config import Config

api_key = Config.OPENAI_API_KEY
org_id = Config.OPENAI_ORG_ID
model = Config.MODEL_NAME
```

### 2. Assistant Creation

**Old:**
```python
assistant = create_openai_assistant(model_name)
```

**New:**
```python
from src import AssistantManager

manager = AssistantManager()
assistant_id = manager.get_or_create_assistant()
```

### 3. Querying

**Old:**
```python
response = get_response_from_assistant(
    assistant_id,
    content,
    instructions,
    temperature=0,
    verify_and_correct=True
)
```

**New:**
```python
# Simple query
response = manager.query(content, instructions, temperature=0)

# With verification
response = manager.query_with_verification(content, instructions)
```

## Security Fixes Applied

### ✅ Fixed Issues

1. **Hardcoded Organization ID**
   - **Before:** `OpenAI(organization='org-QYLV5ByGzWg3rl4MalRgn5nj')`
   - **After:** `OpenAI(organization=Config.OPENAI_ORG_ID)`

2. **API Key Logging**
   - **Before:** `print(f"✓ Config loaded: {OPENAI_KEY[:10]}...")`
   - **After:** No logging of credentials

3. **Inconsistent Client Creation**
   - **Before:** Multiple `OpenAI()` instantiations
   - **After:** Singleton pattern with one client

4. **Missing Error Handling**
   - **Before:** No try-catch blocks
   - **After:** Comprehensive error handling with retries

## Performance Improvements

### API Call Reduction

**Old system (v1):**
- Create new assistant: 1 call
- Create vector store: 1 call
- Upload files: 2+ calls
- Process query: 1 call
- Verification: 1 call
- **Total: ~6 calls per query** ❌

**New system (v2):**
- First time setup: 5 calls (one-time)
- Subsequent queries: 1-2 calls (depending on verification)
- **Total: 1-2 calls per query** ✅

### Time Savings

**Old system:**
- 25 second hardcoded sleep per query
- Thread creation overhead
- **~30 seconds minimum per query** ❌

**New system:**
- Dynamic polling (typically 2-5 seconds)
- Automatic thread cleanup
- **~5-10 seconds per query** ✅

## Verification Comparison

Both systems support two-pass verification, but v2 is more efficient:

**Old:**
```python
response = get_response_from_assistant(..., verify_and_correct=True)
# Always does verification, can't disable easily
```

**New:**
```python
# Choose based on needs
processor = GameResearchProcessor(use_verification=False)  # Fast
# or
processor = GameResearchProcessor(use_verification=True)   # Accurate
```

## Testing Your Migration

### 1. Verify Configuration
```bash
python -c "from src.config import Config; Config.validate(); print('✅ Config OK')"
```

### 2. Test Setup
```bash
python -m src.main setup
```

### 3. Test Simple Query
```bash
python -m src.main query
# Type: "Hello, test query"
```

### 4. Test Processing (Optional)
```bash
# Copy sample data
cp /path/to/old/VG_input.csv data/test_input.csv

# Process
python -m src.main process data/test_input.csv -o data/test_output.csv
```

## Rollback Plan

If you need to rollback:

1. Keep old code in separate directory
2. Old `.env` file backed up
3. Assistant IDs are independent (old and new can coexist)
4. Switch by changing working directory

## Need Help?

Common issues and solutions:

**"Configuration validation failed"**
- Check `.env` file exists
- Verify API key format (starts with `sk-`)
- Verify org ID format (starts with `org-`)

**"No module named 'src'"**
- Run from project root: `cd infinite_lives_v2`
- Use `-m` flag: `python -m src.main`

**"Assistant not found"**
- Run setup: `python -m src.main setup`
- Check ASSISTANT_ID in `.env`

**"Rate limit error"**
- System auto-retries with backoff
- If persistent, wait a few minutes
- Check OpenAI usage dashboard

## Additional Resources

- [README.md](README.md) - Full documentation
- [examples.py](examples.py) - Code examples
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants)
