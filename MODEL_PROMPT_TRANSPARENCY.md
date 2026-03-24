# Model & Prompt Transparency Feature

**Added**: 2026-03-24
**Status**: ✅ **IMPLEMENTED**

---

## Overview

Added comprehensive model and prompt transparency to the Auto-SLR application. Users can now view detailed information about:
- Active LLM models used in each phase
- Complete system-level prompts for all agents
- Model configuration and parameters

---

## Features

### 1. Sidebar: Model & Prompt Information Panel

**Location**: Sidebar → Expandable section "🔍 Model & Prompt Information"

**Contents**:
- **Active Model Configuration**
  - Provider type (Bedrock/Anthropic/Dummy)
  - Model name and ID
  - AWS region (if applicable)
  - Availability status

- **Phase 1: Query Generation Prompts** (4 agents)
  - **Pulse Agent**: Keyword expansion system prompt
  - **Formulator Agent**: Query construction system prompt
  - **Sentinel Agent**: Quality control system prompt
  - **Refiner Agent**: Final polish system prompt

- **Phase 3: Abstract Screening Prompts** (2 modes)
  - **Simple Mode**: Single-pass JSON decision prompt
  - **Zeroshot Mode**: Two-step reasoning prompts
    - Step 1: Reasoning generation
    - Step 2: Final decision

### 2. In-Context Model Information

**Phase 1 - Query Generation**:
- Shows active model at start of agent execution
- Includes link to full prompt details in sidebar

**Phase 3 - Screening Configuration**:
- Displays active model above configuration options
- Links to prompt information in sidebar

**Phase 3 - Results Display**:
- Shows model used for screening in results header
- Displays screening mode (simple/zeroshot)
- Links to prompt details

**Agent Outputs Section**:
- Info banner directing users to sidebar for complete prompts

---

## Implementation Details

### New Module: `utils/prompt_inspector.py`

```python
def get_phase1_agent_prompts() -> Dict[str, str]
    """Returns all Phase 1 agent system prompts."""

def get_phase3_screening_prompts() -> Dict[str, str]
    """Returns Phase 3 screening prompts for both modes."""

def get_model_information(provider) -> Dict
    """Extracts model details from provider instance."""

def format_prompt_display(name, text) -> str
    """Formats prompt for display."""
```

### Updated Files

1. **`app.py`**
   - Imported prompt_inspector module
   - Added sidebar Model & Prompt Information expander
   - Added model info displays in Phase 1 status widget
   - Added model info in Phase 3 configuration
   - Added model info in Phase 3 results
   - Added info banner in Agent Outputs section

2. **`utils/prompt_inspector.py`** (NEW)
   - Centralized prompt storage
   - Model information extraction
   - Display formatting utilities

---

## User Benefits

### 1. **Transparency**
- Users can see exactly what prompts are used
- Complete visibility into agent instructions
- Clear model identification

### 2. **Reproducibility**
- Prompts are documented and version-controlled
- Users can cite exact prompt text in publications
- Enables systematic review protocol documentation

### 3. **Debugging**
- Users can understand why agents made certain decisions
- Helps identify prompt engineering opportunities
- Facilitates troubleshooting

### 4. **Trust**
- No "black box" AI operations
- Clear methodology for peer review
- Compliance with systematic review standards (PRISMA)

---

## Usage Guide

### Viewing System Prompts

1. **Open Sidebar Panel**
   - Look for "🔍 Model & Prompt Information" in sidebar
   - Click to expand

2. **View Active Model**
   - See current provider and model name
   - Check availability status
   - View AWS region (if using Bedrock)

3. **Browse Phase 1 Prompts**
   - Expand any of the 4 agent sections:
     - Pulse (Keyword Expansion)
     - Formulator (Query Construction)
     - Sentinel (Quality Control)
     - Refiner (Final Polish)
   - Full prompt text shown in code block

4. **Browse Phase 3 Prompts**
   - View Simple Mode prompt
   - View Zeroshot Mode prompts (both steps)
   - Parameter placeholders shown: `{k_strictness}`, `{criteria}`

### Model Information Display

**During Query Generation**:
- Model name shown at start of 4-agent execution
- Link to full prompts provided

**During Screening**:
- Model name shown in configuration section
- Model name + mode shown in results header
- Link to prompts in both locations

---

## Example Output

### Sidebar Display

```
🔍 Model & Prompt Information

Active Model Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━
Provider: BedrockProvider
Status: ✅ Available

Model: AWS Bedrock (us.anthropic.claude-sonnet-4-6)
Region: us-east-1
Model ID: us.anthropic.claude-sonnet-4-6

Phase 1: Query Generation Prompts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Pulse (Keyword Expansion)
[Full prompt text shown in code block...]

🤖 Formulator (Query Construction)
[Full prompt text shown in code block...]

🤖 Sentinel (Quality Control)
[Full prompt text shown in code block...]

🤖 Refiner (Final Polish)
[Full prompt text shown in code block...]

Phase 3: Abstract Screening Prompts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Simple Mode
[Full prompt text shown in code block...]

✅ Zeroshot Mode - Step 1 (Reasoning)
[Full prompt text shown in code block...]

✅ Zeroshot Mode - Step 2 (Decision)
[Full prompt text shown in code block...]
```

### In-Context Display

**Phase 1 Status Widget**:
```
🤖 Active Model: AWS Bedrock (us.anthropic.claude-sonnet-4-6)
💡 View system prompts: Sidebar → 'Model & Prompt Information'

🔍 Agent 1: Pulse - Diving into academic jargon soup...
```

**Phase 3 Configuration**:
```
⚙️ Screening Configuration
━━━━━━━━━━━━━━━━━━━━━━

🤖 Active Model: AWS Bedrock (us.anthropic.claude-sonnet-4-6)
💡 View system prompts in sidebar: '🔍 Model & Prompt Information'

[Mode selection dropdown...]
[Thread count slider...]
```

**Phase 3 Results**:
```
📊 Screening Results & Review
━━━━━━━━━━━━━━━━━━━━━━━━━

Included: 45
Excluded: 155
Errors: 0

🤖 Model: AWS Bedrock (us.anthropic.claude-sonnet-4-6) | Mode: simple
💡 View prompts: Sidebar → 'Model & Prompt Information'
```

---

## Maintenance Notes

### Adding New Agents/Phases

1. **Add prompts to `prompt_inspector.py`**:
   ```python
   def get_phaseN_prompts():
       return {
           "Agent Name": """System prompt text..."""
       }
   ```

2. **Import and display in `app.py`**:
   ```python
   phaseN_prompts = get_phaseN_prompts()
   for name, prompt in phaseN_prompts.items():
       with st.expander(f"🤖 {name}"):
           st.code(prompt, language="text")
   ```

### Updating Existing Prompts

1. **Edit `prompt_inspector.py`**
2. Prompts are immediately reflected in UI (no caching)
3. Keep prompts in sync with actual agent code in modules/

### Version Control

- All prompts are in `utils/prompt_inspector.py`
- Git tracks all prompt changes
- Easy to diff prompt versions
- Enables prompt versioning for reproducibility

---

## Testing

### Verification Checklist

- [x] Sidebar expander displays without errors
- [x] All 4 Phase 1 agent prompts load correctly
- [x] All 3 Phase 3 screening prompts load correctly
- [x] Model information displays in sidebar
- [x] Model information displays in Phase 1 status
- [x] Model information displays in Phase 3 config
- [x] Model information displays in Phase 3 results
- [x] Links to sidebar are functional
- [x] Code blocks render properly
- [x] No import errors

### Test Command

```bash
source .venv/bin/activate
python3 -c "
from utils.prompt_inspector import *
print('Phase 1 prompts:', len(get_phase1_agent_prompts()))
print('Phase 3 prompts:', len(get_phase3_screening_prompts()))
"
```

Expected output:
```
Phase 1 prompts: 4
Phase 3 prompts: 3
```

---

## Future Enhancements

### Potential Additions

1. **Prompt Version History**
   - Track prompt changes over time
   - Allow users to see historical prompts
   - Compare prompt versions

2. **Export Functionality**
   - Export all prompts as text/PDF
   - Include in systematic review protocols
   - Attach to publications as supplementary material

3. **Custom Prompts**
   - Allow users to modify prompts
   - Save custom prompt sets
   - Share prompt configurations

4. **Prompt Metrics**
   - Token counts for each prompt
   - Estimated API costs
   - Performance statistics

5. **Phase 2 Query Details**
   - Show database-specific query syntax
   - Display actual queries sent to APIs
   - Include search parameters (filters, limits, etc.)

6. **Phase 4 Full-Text Retrieval**
   - Show retrieval strategy prompts (if any)
   - Display API call details
   - Include fallback chain information

---

## Compliance & Standards

### Systematic Review Standards

This feature helps comply with:

- **PRISMA 2020**: Search strategy reporting requirements
- **Cochrane Handbook**: Documentation of search methods
- **MECIR Standards**: Reproducible search strategies

### Publication Ready

Users can:
- Copy exact prompts for methods sections
- Include prompts in supplementary materials
- Cite specific prompt versions in protocols
- Share prompt configurations with collaborators

---

## Conclusion

✅ **Feature Complete**

The Model & Prompt Transparency feature provides comprehensive visibility into:
- LLM model configuration
- Agent system prompts
- Screening methodology

This enhances:
- **Transparency**: No black-box AI
- **Reproducibility**: Exact prompts documented
- **Trust**: Clear methodology for peer review
- **Compliance**: Meets systematic review standards

**Ready for Production** 🚀
