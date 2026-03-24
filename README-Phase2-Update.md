# Auto-SLR Pipeline - Phase 1 & 2 Complete! 🎉

## ✅ What's New

### Part A: API Settings with AWS Bedrock Support

**Added Features:**
1. **Sidebar API Configuration**
   - Select LLM provider: Anthropic Direct API | AWS Bedrock | Dummy Mode
   - Configure provider-specific settings
   - Test connection button

2. **AWS Bedrock Integration**
   - Full support for Claude models via AWS Bedrock
   - Configurable AWS region
   - Optional AWS credentials or IAM role
   - Model selection: Sonnet 3.5, Opus 3, Haiku 3

3. **Provider Abstraction Layer**
   - New `utils/llm_providers.py` module
   - Clean abstraction for multiple LLM backends
   - Easy to extend with additional providers

### Part B: Phase 2 - Metadata Search Execution

**Added Features:**
1. **Multi-Database Search**
   - OpenAlex integration ✅
   - PubMed integration ✅
   - Scopus integration ✅
   - Select databases and configure max results

2. **Search Execution Module**
   - New `modules/m2_search_exec.py`
   - Orchestrates existing search wrappers
   - Progress tracking with real-time updates

3. **Results Viewer**
   - Preview search results in UI
   - Download CSV, JSON, JSONL formats
   - Expandable result panels per database

4. **Complete Workflow**
   - Query Generation (Phase 1) → Search Execution (Phase 2)
   - Human-in-the-Loop at each phase
   - Persistent results across sessions

## 📦 Installation

```bash
cd /Users/ziqianxia/Documents/GitHub/Climate_Intervention_Atlas

# Install updated dependencies
pip install -r requirements-slr.txt

# This includes:
# - boto3 (for AWS Bedrock)
# - pandas (for results handling)
# - All existing dependencies
```

## 🚀 Quick Start

### Step 1: Configure Environment (Optional)

Create a `.env` file or set environment variables:

```bash
# AWS Bedrock (Recommended)
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Or use Anthropic Direct
export ANTHROPIC_API_KEY=your_key_here

# Search API Keys (Optional but recommended)
export OPENALEX_API_KEY=your_key
export OPENALEX_MAILTO=your@email.com
export PUBMED_API_KEY=your_key
export PUBMED_EMAIL=your@email.com
export ELSEVIER_API_KEY=your_key
export ELSEVIER_INST_TOKEN=your_token
```

### Step 2: Run the Application

```bash
streamlit run app.py
```

### Step 3: Use the Pipeline

**Phase 1: Query Generation**
1. In sidebar, select LLM provider (recommend: **bedrock**)
2. Configure AWS region and model
3. (Optional) Test connection
4. Enter research topic
5. Click "🚀 Generate Queries"
6. Review and edit queries
7. Click "🟢 Approve & Proceed to Phase 2"

**Phase 2: Metadata Search**
1. Select databases (OpenAlex, PubMed, Scopus)
2. Set max results per database
3. (Optional) Enter API credentials in expander
4. Click "🚀 Execute Search"
5. Wait for progress bar to complete
6. Review results in expandable panels
7. Download CSV/JSON/JSONL files
8. Click "🟢 Approve & Proceed to Phase 3"

## 🎯 New Files Created

```
/Users/ziqianxia/Documents/GitHub/Climate_Intervention_Atlas/
├── utils/
│   └── llm_providers.py          # NEW: Provider abstraction (200 lines)
├── modules/
│   ├── m1_query_gen.py           # MODIFIED: Uses provider abstraction
│   ├── m2_search_exec.py         # NEW: Search orchestration (380 lines)
│   └── __init__.py               # MODIFIED: Adds search packages to path
├── app.py                         # MODIFIED: API settings + Phase 2 UI
├── requirements-slr.txt          # MODIFIED: Added boto3, pandas
└── .env.example                  # MODIFIED: AWS Bedrock variables
```

## 🔧 Configuration Options

### LLM Provider Selection

**Anthropic Direct:**
- Simple setup with API key
- Direct connection to Anthropic API
- No AWS account needed

**AWS Bedrock (Recommended):**
- Enterprise-grade security
- Use existing AWS credentials
- IAM role support
- Region selection for compliance

**Dummy Mode:**
- No API key required
- Uses pre-defined test queries
- Great for UI testing

### Search Database Options

**OpenAlex:**
- Free, no key required
- Comprehensive coverage
- Fast pagination

**PubMed:**
- Biomedical focus
- NCBI E-utilities API
- Optional key for higher rate limits

**Scopus:**
- Requires Elsevier API key
- Extensive citation data
- Optional institutional token

## 📊 Output Format

All search results follow a unified structure:

```
search_results_20260323_120000/
├── openalex/
│   ├── run_summary.json       # Query metadata
│   ├── works_summary.csv      # Flattened table
│   └── works_full.jsonl       # Full metadata
├── pubmed/
│   ├── run_summary.json
│   ├── works_summary.csv
│   └── works_full.jsonl
└── scopus/
    ├── run_summary.json
    ├── works_summary.csv
    └── works_full.jsonl
```

## 🧪 Testing Guide

### Test AWS Bedrock Integration

1. **Setup:**
   ```bash
   export AWS_REGION=us-east-1
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

2. **In UI:**
   - Select "bedrock" provider
   - Choose region (us-east-1)
   - Click "🔌 Test Connection"
   - Should see: "✅ Connected to AWS Bedrock (anthropic.claude-3-5-sonnet...)"

3. **Generate Queries:**
   - Enter topic: "heat waves and mortality"
   - Click "Generate Queries"
   - Verify agents use Bedrock in logs

### Test Phase 2 Search

1. **OpenAlex (No Key Needed):**
   - Complete Phase 1 approval
   - In Phase 2, select only "OpenAlex"
   - Set max results to 100
   - Click "Execute Search"
   - Verify CSV downloads

2. **PubMed:**
   - Add API key if available
   - Select "PubMed"
   - Verify two-step process (esearch + efetch)
   - Check PMID column in results

3. **All Three Databases:**
   - Select all checkboxes
   - Watch progress bar increment
   - Verify 3 result panels appear
   - Download all output files

## 🆘 Troubleshooting

### AWS Bedrock Not Connecting

**Problem:** "❌ Connection failed"

**Solution:**
- Verify AWS credentials are valid
- Check region supports Bedrock
- Ensure model ID is correct: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Try IAM role instead of access keys

### Search Wrapper Import Errors

**Problem:** `ImportError: No module named 'openalex_search_wrapper'`

**Solution:**
- Verify `Search and full-text packages/search-packages/` exists
- Check subdirectories: `openalex-searcher/`, `pubmed-searcher/`, `scopus-searcher/`
- Restart Streamlit app

### Empty Search Results

**Problem:** "Results Found: 0"

**Solution:**
- Verify query syntax is correct for the database
- Check API credentials are valid
- Try lower max_results (e.g., 10) for testing
- Check logs for detailed error messages

## 📝 Next Steps

**Phase 3: Abstract Screening** (Not yet implemented)
- Integrate existing LLMscreen tool
- HITL screening interface
- Export screened results

**Phase 4: Full-Text Retrieval** (Not yet implemented)
- Integrate fulltext-chain wrapper
- OA-first → Publishers → Playwright fallback
- PDF/XML to Markdown conversion

**Phase 5: Data Analysis** (Not yet implemented)
- Synthesis and extraction
- Visualization
- Export final report

## 🎓 Documentation

- **Main README**: [README-SLR.md](README-SLR.md)
- **Repository Overview**: [CLAUDE.md](CLAUDE.md)
- **Environment Template**: [.env.example](.env.example)
- **Search Wrappers**: `Search and full-text packages/*/README.md`

## 💡 Tips

1. **Use Bedrock for Production**: More reliable, better security
2. **Start with OpenAlex**: Free and fast for testing
3. **Set Reasonable Limits**: Start with 100-500 results per database
4. **Review Before Approval**: Edit queries in Phase 1 if needed
5. **Check Logs**: Detailed agent activity in bottom panel

---

**Status:** ✅ Phase 1 Complete | ✅ Phase 2 Complete | ⏸️ Phase 3-5 Pending

**Last Updated:** 2026-03-23

**Need Help?** Check logs at `logs/slr_pipeline.log` for detailed diagnostics.
