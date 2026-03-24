# Environment Setup Guide

**Complete guide to configuring API keys and credentials safely**

---

## 🔐 Quick Start

### Step 1: Copy Template

```bash
cp .env.example .env
```

### Step 2: Edit .env File

```bash
# Use your preferred editor
nano .env
# or
code .env
# or
vim .env
```

### Step 3: Fill in Your API Keys

Replace `your_*_here` with your actual credentials (see sections below)

### Step 4: Verify

```bash
# Check file exists and is ignored by git
ls -la .env
git status .env  # Should show: "not tracked" or nothing
```

---

## 🔑 Getting API Keys

### Required for Basic Functionality

#### Option A: Anthropic Direct (Easiest)

1. Go to https://console.anthropic.com/
2. Sign up / Log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy key to `.env`:
   ```bash
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
   ```

#### Option B: AWS Bedrock (Recommended for Enterprise)

1. **AWS Account Setup**:
   - Go to https://console.aws.amazon.com/
   - Sign up or log in
   - Enable Bedrock in your region (us-east-1 recommended)

2. **Model Access**:
   - Navigate to Bedrock console
   - Go to "Model access"
   - Request access to Anthropic Claude models
   - Wait for approval (usually instant)

3. **IAM Credentials**:

   **Method 1: IAM User (Simple)**
   - Go to IAM console
   - Create new user: "bedrock-user"
   - Attach policy: "AmazonBedrockFullAccess"
   - Create access key
   - Copy credentials to `.env`:
     ```bash
     LLM_PROVIDER=bedrock
     AWS_REGION=us-east-1
     AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
     AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```

   **Method 2: IAM Role (More Secure)**
   - For EC2/Lambda: Use IAM roles (no keys needed)
   - Application automatically uses role credentials

4. **Verify Access**:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

#### Option C: Dummy Provider (Testing Only)

No API keys needed - uses pre-defined test data:

```bash
LLM_PROVIDER=dummy
```

---

### Optional APIs (Enhance Functionality)

#### OpenAlex (Free, Recommended)

**Without API Key** (Polite Pool):
```bash
# OPENALEX_API_KEY=  # Leave blank
OPENALEX_MAILTO=your_email@domain.com
```

**With API Key** (Higher Rate Limits):
1. Go to https://openalex.org/
2. Create account
3. Request API key (free)
4. Add to `.env`:
   ```bash
   OPENALEX_API_KEY=your_key_here
   OPENALEX_MAILTO=your_email@domain.com
   ```

#### PubMed / NCBI (Free)

**Without API Key** (3 requests/second):
```bash
# PUBMED_API_KEY=  # Leave blank
PUBMED_EMAIL=your_email@domain.com
```

**With API Key** (10 requests/second):
1. Go to https://www.ncbi.nlm.nih.gov/account/
2. Create NCBI account
3. Generate API key under "API Key Management"
4. Add to `.env`:
   ```bash
   PUBMED_API_KEY=your_ncbi_key_here
   PUBMED_EMAIL=your_email@domain.com
   ```

#### Scopus / Elsevier (Requires Subscription)

1. **Check Institution Access**:
   - Ask your library if they have Scopus API access
   - Many universities have institutional agreements

2. **Get API Key**:
   - Go to https://dev.elsevier.com/
   - Create developer account
   - Register your application
   - Get API key and institutional token

3. **Add to `.env`**:
   ```bash
   ELSEVIER_API_KEY=your_elsevier_key_here
   ELSEVIER_INST_TOKEN=your_inst_token_here
   ```

---

## 🧪 Testing Your Configuration

### Test 1: Check Environment File

```bash
# Verify .env exists and is not tracked by git
ls -la .env
git check-ignore .env  # Should output: .env
```

### Test 2: Test LLM Provider

```bash
source .venv/bin/activate

# Test with Python
python3 -c "
from utils.llm_providers import create_llm_provider
import os

provider_type = os.environ.get('LLM_PROVIDER', 'dummy')
print(f'Testing {provider_type} provider...')

if provider_type == 'anthropic':
    from utils.llm_providers import AnthropicProvider
    provider = AnthropicProvider(api_key=os.environ.get('ANTHROPIC_API_KEY'))
elif provider_type == 'bedrock':
    from utils.llm_providers import BedrockProvider
    provider = BedrockProvider(
        region=os.environ.get('AWS_REGION'),
        model_id=os.environ.get('BEDROCK_MODEL_ID')
    )
else:
    from utils.llm_providers import DummyProvider
    provider = DummyProvider()

if provider.is_available():
    print(f'✅ SUCCESS: {provider.get_model_name()}')
else:
    print('❌ ERROR: Provider not available')
"
```

### Test 3: Test Search APIs

```bash
# Test OpenAlex
python3 -c "
import os
print('OpenAlex Email:', os.environ.get('OPENALEX_MAILTO', 'NOT SET'))
print('OpenAlex Key:', 'SET' if os.environ.get('OPENALEX_API_KEY') else 'NOT SET (OK for polite pool)')
"

# Test PubMed
python3 -c "
import os
print('PubMed Email:', os.environ.get('PUBMED_EMAIL', 'NOT SET'))
print('PubMed Key:', 'SET' if os.environ.get('PUBMED_API_KEY') else 'NOT SET (OK, slower rate limit)')
"

# Test Scopus
python3 -c "
import os
print('Scopus Key:', 'SET' if os.environ.get('ELSEVIER_API_KEY') else 'NOT SET')
print('Scopus Token:', 'SET' if os.environ.get('ELSEVIER_INST_TOKEN') else 'NOT SET')
"
```

---

## 🔒 Security Best Practices

### DO ✅

1. **Use `.env` file for all credentials**
   ```bash
   # Good
   API_KEY=$(cat .env | grep ANTHROPIC_API_KEY | cut -d'=' -f2)
   ```

2. **Keep `.env` in `.gitignore`**
   ```bash
   # Verify it's ignored
   cat .gitignore | grep .env
   ```

3. **Use separate keys for dev/prod**
   ```bash
   # Development
   .env

   # Production
   .env.production
   ```

4. **Rotate keys regularly**
   - Every 90 days minimum
   - Immediately if compromised
   - Track rotation dates

5. **Use IAM roles when possible** (AWS)
   - No keys to manage
   - Automatic rotation
   - Better security

### DON'T ❌

1. **Never hardcode credentials**
   ```python
   # BAD - Don't do this!
   api_key = "sk-ant-api03-xxxxx"

   # Good
   api_key = os.environ.get("ANTHROPIC_API_KEY")
   ```

2. **Never commit `.env` to git**
   ```bash
   # If accidentally committed:
   git rm --cached .env
   git commit -m "Remove .env file"
   # Then revoke all keys in that file!
   ```

3. **Never share `.env` file**
   - Don't email it
   - Don't upload to Slack/Discord
   - Don't share via cloud drives
   - Use secure credential managers instead

4. **Never use production keys for testing**
   - Always use separate keys
   - Production keys should have restricted permissions

---

## 🚨 What to Do if Keys are Compromised

### Immediate Actions

1. **Revoke compromised keys immediately**
   - Anthropic: console.anthropic.com → API Keys → Revoke
   - AWS: IAM console → Delete access key
   - Others: Check provider documentation

2. **Generate new keys**
   - Create new keys with same permissions
   - Update `.env` file
   - Test functionality

3. **Check for unauthorized usage**
   - Review API logs
   - Check billing for unusual charges
   - Look for suspicious activity

4. **Notify relevant parties**
   - Security team (if enterprise)
   - Cloud provider support (if major breach)
   - Team members using affected systems

### Prevention

1. **Never commit keys to git**
   ```bash
   # Check before committing
   git diff --cached | grep -i "api.*key"
   ```

2. **Use git-secrets** (automated checking)
   ```bash
   # Install
   brew install git-secrets  # macOS

   # Setup
   cd /path/to/repo
   git secrets --install
   git secrets --register-aws
   ```

3. **Enable 2FA on all accounts**
   - Anthropic console
   - AWS account
   - GitHub account

4. **Monitor API usage**
   - Set up billing alerts
   - Review usage weekly
   - Watch for spikes

---

## 📦 Deployment Configurations

### Local Development

```bash
# .env (local)
LLM_PROVIDER=dummy  # Use dummy to avoid API costs
OPENALEX_MAILTO=dev@localhost.com
DEBUG=1
```

### Production (Streamlit Cloud / Heroku)

**Don't use `.env` file - use platform secrets:**

**Streamlit Cloud**:
1. Go to app settings
2. Navigate to "Secrets"
3. Add each variable:
   ```toml
   LLM_PROVIDER = "bedrock"
   AWS_REGION = "us-east-1"
   AWS_ACCESS_KEY_ID = "AKIAXXXXXXXX"
   AWS_SECRET_ACCESS_KEY = "xxxxxxxx"
   ```

**Heroku**:
```bash
heroku config:set LLM_PROVIDER=bedrock
heroku config:set AWS_REGION=us-east-1
heroku config:set AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
heroku config:set AWS_SECRET_ACCESS_KEY=xxxxxxxx
```

**Docker**:
```bash
# Pass via environment
docker run -e LLM_PROVIDER=bedrock \
  -e AWS_REGION=us-east-1 \
  --env-file .env \
  climate-atlas
```

---

## 🔍 Troubleshooting

### Issue: "No API key found"

**Check**:
```bash
# Is .env file present?
ls -la .env

# Is it being loaded?
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.environ.get('LLM_PROVIDER'))"
```

**Fix**:
1. Ensure `.env` exists
2. Check variable names match exactly
3. No spaces around `=` in `.env`
4. Values don't need quotes

### Issue: "Provider not available"

**AWS Bedrock**:
```bash
# Check credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

**Anthropic**:
```bash
# Test key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

### Issue: "Rate limit exceeded"

**Solutions**:
1. Add API key (increases limits)
2. Reduce thread count
3. Add delays between requests
4. Upgrade API plan

---

## 📚 Additional Resources

### Documentation Links
- **Anthropic**: https://docs.anthropic.com/
- **AWS Bedrock**: https://docs.aws.amazon.com/bedrock/
- **OpenAlex**: https://docs.openalex.org/
- **PubMed**: https://www.ncbi.nlm.nih.gov/books/NBK25500/
- **Elsevier**: https://dev.elsevier.com/documentation.html

### Cost Calculators
- **Anthropic**: https://console.anthropic.com/settings/cost
- **AWS**: https://calculator.aws/

### Security Tools
- **git-secrets**: https://github.com/awslabs/git-secrets
- **AWS IAM**: https://console.aws.amazon.com/iam/

---

## ✅ Setup Checklist

- [ ] Copied `.env.example` to `.env`
- [ ] Filled in at least one LLM provider (Anthropic or Bedrock)
- [ ] Added email for OpenAlex
- [ ] Added email for PubMed (optional)
- [ ] Tested configuration (providers available)
- [ ] Verified `.env` is in `.gitignore`
- [ ] Confirmed `.env` not tracked by git
- [ ] Set calendar reminder to rotate keys in 90 days
- [ ] Enabled 2FA on provider accounts
- [ ] Documented keys in secure password manager

---

**Once completed, you're ready to run the application!**

```bash
source .venv/bin/activate
streamlit run app.py
```

🎉 Enjoy your secure, configured environment!
