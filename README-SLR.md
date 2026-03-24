# Auto-SLR Multi-Agent Pipeline

An intelligent, multi-phase pipeline for automating Systematic Literature Reviews (SLR) using AI agents and Human-in-the-Loop (HITL) workflows.

## 🎯 Current Status: Phase 1 Complete

**Phase 1: Multi-Agent Query Generator** ✅
- Three AI agents (Pulse → Formulator → Sentinel) work together to generate optimized Boolean search queries
- Streamlit HITL interface for human review and editing
- Database-specific query formats (Elsevier/Scopus, PubMed, OpenAlex)

**Upcoming Phases:**
- Phase 2: Metadata Search Execution ⏸️
- Phase 3: Abstract Screening ⏸️
- Phase 4: Full-Text Retrieval ⏸️
- Phase 5: Data Analysis & Synthesis ⏸️

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/ziqianxia/Documents/GitHub/Climate_Intervention_Atlas
pip install -r requirements-slr.txt
```

### 2. Set Up API Key (Optional but Recommended)

Create a `.env` file or export the environment variable:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

**Note:** The system will work without an API key by providing high-quality dummy queries, but using the API enables intelligent, context-aware query generation.

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 How to Use Phase 1

1. **Enter Research Topic**: Type your research topic in the input field
   - Example: *"extreme heat and mortality"*
   - Example: *"tropical cyclones and mental health impacts"*

2. **Generate Queries**: Click the 🚀 **Generate Queries** button
   - Wait 30-60 seconds for the agent team to work
   - Watch the agents think in the expanders

3. **Review Agent Outputs**:
   - **Pulse Agent**: See expanded keywords and synonyms
   - **Formulator Agent**: View query construction strategy
   - **Sentinel Agent**: Check validation notes and warnings

4. **Edit Queries** (Optional): Manually refine the Boolean queries in the text areas

5. **Approve & Lock**: Click 🟢 **Approve & Proceed to Phase 2**
   - Phase 1 locks and cannot be regenerated
   - Ready for Phase 2 (coming soon)

## 🤖 The Three-Agent Team

### 🔍 Agent 1: Pulse (Keyword Expander)
- **Role**: Expert research librarian
- **Task**: Expand research topics with synonyms, related terms, and domain vocabulary
- **Output**: 10-20 carefully selected keywords

### ⚙️ Agent 2: Formulator (Query Constructor)
- **Role**: Database search syntax expert
- **Task**: Create database-specific Boolean queries
- **Output**: Three optimized queries for Elsevier/Scopus, PubMed, and OpenAlex

### 🛡️ Agent 3: Sentinel (Quality Controller)
- **Role**: Search strategy validator
- **Task**: Check syntax, balance, and quality
- **Output**: Final validated queries with notes and warnings

## 📁 Project Structure

```
Climate_Intervention_Atlas/
├── app.py                  # Streamlit HITL interface
├── modules/
│   └── m1_query_gen.py    # Phase 1: 3-agent query generation team
├── utils/
│   └── logger.py          # Unified dual-output logger
├── logs/
│   └── slr_pipeline.log   # Detailed operation logs
├── requirements-slr.txt   # Python dependencies
└── .env.example           # Environment variable template
```

## 🔧 Technical Details

**Agent Communication**: Sequential chain (Pulse → Formulator → Sentinel)

**LLM Model**: Claude 3.5 Sonnet (Anthropic)

**Logging**: Dual output
- File: `logs/slr_pipeline.log` (persistent)
- UI: Live stream in Streamlit interface (last 50 entries)

**Session Management**: Streamlit `st.session_state` for HITL workflow

**Error Handling**:
- Graceful fallback to dummy data if no API key
- Retry logic with exponential backoff
- Detailed error logging

## 📊 Example Queries

**Topic**: *"climate change and mental health"*

**Elsevier/Scopus**:
```
TITLE-ABS-KEY(("climate change" OR "global warming" OR "extreme weather") AND ("mental health" OR "psychological distress" OR "anxiety" OR "depression") AND (adapt* OR resilien* OR coping))
```

**PubMed**:
```
(("climate change"[Title/Abstract] OR "global warming"[Title/Abstract] OR "extreme weather"[Title/Abstract]) AND ("mental health"[Title/Abstract] OR "psychological distress"[Title/Abstract]) AND (adapt*[Title/Abstract] OR resilien*[Title/Abstract]))
```

**OpenAlex**:
```
"climate change" mental health adaptation resilience
```

## 🧪 Testing

### Test with API Key
1. Set `ANTHROPIC_API_KEY` environment variable
2. Run app: `streamlit run app.py`
3. Enter topic and generate queries
4. Verify all 3 agents execute successfully

### Test without API Key
1. Unset/remove `ANTHROPIC_API_KEY`
2. Run app
3. Verify dummy queries appear without crashes
4. Check warning in logs about missing API key

## 🔐 Security Notes

- API keys are loaded from environment variables only
- No hardcoded credentials in source files
- `.env` file is gitignored (use `.env.example` as template)
- Logs do not contain sensitive information

## 📚 Integration with Existing Tools

This new pipeline complements the existing `Search and full-text packages/`:
- **Phase 1** (new): Intelligent query generation
- **Phase 2** (planned): Will use existing search wrappers (OpenAlex, PubMed, Scopus)
- **Phase 4** (planned): Will use existing fulltext-chain wrapper

## 🛠️ Development

**Next Steps for Phase 2**:
- Integrate with existing search wrappers
- Add batch query execution
- Implement result deduplication
- Export to CSV/JSON

**Contributing**: This is a work in progress. Phase 1 is complete and ready for testing.

## 📄 License

See repository root LICENSE file.

## 🙏 Acknowledgments

- Claude 3.5 Sonnet (Anthropic) for agent intelligence
- Streamlit for HITL interface
- Existing search/fulltext packages for workflow integration
