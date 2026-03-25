# 🚀 Quick Start Guide

**Get your Auto-SLR Pipeline running in 5 minutes!**

---

## Streamlit Cloud (Recommended)

### 1️⃣ Deploy (2 minutes)

1. Visit: https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Settings:
   - Repository: `Ziqian-xia/Climate_Intervention_Atlas`
   - Branch: `main`
   - Main file: `app.py`
5. Click "Deploy!"

### 2️⃣ Configure Secrets (2 minutes)

In App Settings → Secrets, paste:

```toml
[llm]
provider = "bedrock"
aws_region = "us-east-1"
aws_model_id = "us.anthropic.claude-sonnet-4-6"
aws_access_key_id = "YOUR_AWS_KEY"
aws_secret_access_key = "YOUR_AWS_SECRET"

[search]
openalex_mailto = "your@email.com"

[screening]
openai_api_key = "YOUR_OPENAI_KEY"

[fulltext]
wiley_tdm_client_token = "YOUR_WILEY_TOKEN"
```

### 3️⃣ Test (1 minute)

1. Open your app: `https://your-app.streamlit.app`
2. Enter a research topic
3. Click "Generate Queries"
4. ✅ Done!

---

## Local Installation

```bash
# Clone & Install
git clone https://github.com/Ziqian-xia/Climate_Intervention_Atlas.git
cd Climate_Intervention_Atlas
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your API keys

# Run
streamlit run app.py
# Open: http://localhost:8501
```

---

## Get API Keys

### Essential (Free)

- **OpenAlex**: Just use your email → `openalex_mailto = "your@email.com"`
- **PubMed**: Register at [NCBI](https://www.ncbi.nlm.nih.gov/account/)

### For Full Features

- **AWS Bedrock**: [AWS Console](https://aws.amazon.com/) → IAM → Create User
- **OpenAI**: [Platform](https://platform.openai.com/) → API Keys
- **Wiley**: [Request](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining)

---

## Usage

### Phase 1: Generate Queries

```
1. Enter topic: "climate change adaptation strategies"
2. Select AWS Bedrock
3. Click "Generate Queries"
4. Review & Approve
```

### Phase 2: Search

```
1. Select databases (OpenAlex, PubMed)
2. Max results: 1000
3. Click "Execute Search"
4. Download CSV
```

### Phase 3: Screen

```
1. Enter criteria: "Include RCT or quasi-experimental..."
2. Mode: Simple
3. Click "Run Screening"
4. Review & Edit
```

### Phase 4: Get Full-Text

```
1. Click "Start Retrieval"
2. Wait 5-10 min
3. Download PDFs
```

---

## Need Help?

- 📖 Full Guide: [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md)
- 🐛 Issues: [GitHub](https://github.com/Ziqian-xia/Climate_Intervention_Atlas/issues)
- 📧 Email: your@email.com

---

**That's it! Happy researching! 📚**
