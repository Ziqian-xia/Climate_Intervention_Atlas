# Winnow — Systematic Literature Search

**Find the right papers. Faster. AI-powered search using systematic review methods.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)

---

## Features

### 📊 Four-Phase Workflow

- **Phase 1: Query Generation** 🤖
  - 4-agent team (Pulse, Formulator, Sentinel, Refiner)
  - Generates optimized Boolean queries
  - Supports AWS Bedrock & Anthropic API
  - Query variations for comprehensive coverage

- **Phase 2: Metadata Search** 🔍
  - Multi-database search (OpenAlex, PubMed, Scopus)
  - Parallel query execution
  - Unified CSV/JSON export

- **Phase 3: Abstract Screening** ✅
  - LLM-assisted abstract screening (LLMscreen)
  - Human-in-the-loop review interface
  - Paginated table with edit capabilities
  - Simple or Zeroshot screening modes

- **Phase 4: Full-Text Retrieval** 📄
  - Multi-source PDF/XML download
  - API fallback chain (OpenAlex → Wiley → Elsevier)
  - Automatic Markdown conversion
  - Optional Playwright browser automation

---

## Quick Start

### 🚀 Option 1: Streamlit Cloud (Recommended)

**Visit the deployed app:** [https://your-app.streamlit.app](https://your-app.streamlit.app)

No installation required! Configure your API keys in the sidebar.

### 💻 Option 2: Local Installation

```bash
# Clone repository
git clone https://github.com/your-username/Climate_Intervention_Atlas.git
cd Climate_Intervention_Atlas

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
nano .env  # Fill in your API keys

# Run application
streamlit run app.py
```

Open browser at: **http://localhost:8501**

---

## Configuration

### Required APIs

#### Phase 1: Query Generation
- **AWS Bedrock** (Recommended) or **Anthropic API**
- Get AWS credentials: [AWS Console](https://aws.amazon.com/)
- Or Anthropic API key: [Anthropic Console](https://console.anthropic.com/)

#### Phase 2: Search (Optional but Recommended)
- **OpenAlex**: Free, email required → [OpenAlex](https://openalex.org/)
- **PubMed**: Free API key → [NCBI](https://www.ncbi.nlm.nih.gov/account/)
- **Scopus**: Institutional access → [Elsevier](https://dev.elsevier.com/)

#### Phase 3: Screening
- **OpenAI API**: For LLMscreen → [OpenAI](https://platform.openai.com/)

#### Phase 4: Full-Text Retrieval (Optional)
- **Wiley TDM**: Request token → [Wiley](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining)
- **Elsevier API**: Institutional access → [Elsevier](https://dev.elsevier.com/)

### For Streamlit Cloud

1. Go to **App Settings** → **Secrets**
2. Copy content from `.streamlit/secrets.toml.example`
3. Fill in your actual API keys
4. Save and reboot app

---

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Step-by-step usage instructions
- **[API Setup](docs/API_SETUP.md)** - Detailed API configuration guide
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Deploy to Streamlit Cloud/Docker
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Quick Links

- **Full-Text Retrieval**: [FULLTEXT_USAGE_GUIDE.md](FULLTEXT_USAGE_GUIDE.md)
- **Environment Setup**: [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md)
- **Query Variations**: [QUERY_VARIATION_SUMMARY_FOR_ADVISOR.md](QUERY_VARIATION_SUMMARY_FOR_ADVISOR.md)

---

## Project Structure

```
Climate_Intervention_Atlas/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── modules/                        # Application modules
│   ├── m1_query_gen.py            # Phase 1: Query generation
│   ├── m2_search_exec.py          # Phase 2: Search execution
│   ├── m3_screening.py            # Phase 3: Screening
│   └── m4_fulltext.py             # Phase 4: Full-text retrieval
├── utils/                          # Utility functions
│   ├── logger.py
│   ├── llm_providers.py
│   └── prompt_inspector.py
├── Search and full-text packages/ # Search & retrieval tools
│   ├── search-packages/
│   └── fulltext-packages/
└── Legacy code and supporting packages/  # Additional tools
    ├── LLMscreen/                  # Abstract screening
    └── exTweather-hazard/          # Climate cascade analysis
```

---

## Usage Example

### Phase 1: Generate Queries

```python
# Enter your research topic
topic = """
I am interested in research on cooling centers and their impact
on heat-related mortality, with a focus on causal research designs.
"""

# Select LLM provider (AWS Bedrock recommended)
# Click "Generate Queries"
# Review and edit the generated Boolean queries
# Click "Approve & Lock Phase 1"
```

### Phase 2: Search Databases

```python
# Select databases (OpenAlex, PubMed, Scopus)
# Configure max results per database
# Click "Execute Search"
# Download results as CSV/JSON
```

### Phase 3: Screen Abstracts

```python
# Enter inclusion/exclusion criteria
# Select screening mode (Simple or Zeroshot)
# Click "Run Screening"
# Review and edit decisions in paginated table
# Click "Approve & Proceed"
```

### Phase 4: Retrieve Full-Text

```python
# Configure retrieval options
# Optionally enable Playwright fallback
# Click "Start Retrieval"
# Download PDFs and Markdown files
```

---

## Features Highlights

### 🔧 Advanced Capabilities

- **Query Variations**: Generate multiple query variations for comprehensive coverage
- **Multi-Database Search**: Search OpenAlex, PubMed, Scopus simultaneously
- **HITL Review**: Human-in-the-loop review at every phase
- **API Fallback**: Automatic fallback chain for full-text retrieval
- **Markdown Conversion**: Convert PDFs/XMLs to Markdown for analysis
- **Export Formats**: CSV, JSON, JSONL support

### 📊 Performance

- **Query Generation**: ~1-2 minutes per query set
- **Search Execution**: ~2-5 minutes for 1000 papers
- **Abstract Screening**: ~5-10 minutes for 100 abstracts
- **Full-Text Retrieval**: 5-10 seconds per paper (API), 30-60 seconds (Playwright)

---

## Requirements

- **Python**: 3.12+
- **Streamlit**: 1.31+
- **API Keys**: See [Configuration](#configuration) section

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -m 'Add YourFeature'`)
4. Push to branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

---

## Support

**Issues or Questions?**

- 📖 Check [Documentation](docs/)
- 🐛 Report bugs: [GitHub Issues](https://github.com/your-username/Climate_Intervention_Atlas/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-username/Climate_Intervention_Atlas/discussions)

---

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{auto_slr_pipeline,
  title = {Winnow — Systematic Literature Search},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/your-username/Climate_Intervention_Atlas}
}
```

---

## Acknowledgments

- **Claude AI** (Anthropic) - Multi-agent query generation
- **OpenAlex** - Open access metadata
- **Streamlit** - Web application framework
- **LLMscreen** - Abstract screening tool

---

**Built with ❤️ for systematic literature review automation**
