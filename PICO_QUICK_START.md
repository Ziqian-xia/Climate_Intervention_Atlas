# 🚀 PICO Framework Quick Start Guide

**Quick reference for using PICO-based query generation in AutoSR**

---

## ⚡ 5-Minute Quick Start

### 1. Run Example Test (No API Required)

```bash
cd /path/to/Climate_Intervention_Atlas
python3 pico_example_test.py
```

**Output:**
- PICO components (P/I/C/O)
- Structured research question
- Database-specific queries
- JSON export: `pico_test_result.json`

---

### 2. Use in Your Code

```python
from modules.m1_query_gen import QueryGenerationTeam
from utils.llm_providers import AnthropicProvider

# Initialize with API
provider = AnthropicProvider(api_key="your-key")
query_team = QueryGenerationTeam(llm_provider=provider)

# Or use dummy mode (no API)
query_team = QueryGenerationTeam(llm_provider=None)

# Generate PICO-structured queries
topic = "cooling centers and heat-related mortality in elderly populations"
result = query_team.generate_queries(topic)

# Access PICO structure
pico = result['pulse_pico']
print("Population:", pico['population'])
print("Intervention:", pico['intervention'])
print("Outcome:", pico['outcome'])

# Access queries
print("Elsevier:", result['refiner_queries']['elsevier_query'])
print("PubMed:", result['refiner_queries']['pubmed_query'])
print("OpenAlex:", result['refiner_queries']['openalex_query'])
```

---

### 3. Use in Streamlit App

The PICO framework is automatically integrated in Phase 1 of the Streamlit app:

```bash
streamlit run app.py
```

1. Enter your research topic
2. Phase 1 will apply PICO analysis
3. View PICO components in results
4. Get PICO-structured queries

---

## 📊 What You Get

### PICO Analysis

```json
{
  "pico": {
    "population": ["elderly", "older adults", "senior citizens"],
    "intervention": ["cooling center", "heat refuge", "air-conditioned space"],
    "comparison": [],
    "outcome": ["heat-related mortality", "death", "excess mortality"]
  },
  "pico_statement": "In elderly populations (P), what is the effectiveness of cooling centers (I) in reducing heat-related mortality (O)?"
}
```

### Structured Queries

**Elsevier/Scopus:**
```
TITLE-ABS-KEY(
  (P_terms) AND (I_terms) AND (O_terms)
)
```

**PubMed:**
```
((P_terms[Title/Abstract]) AND (I_terms[Title/Abstract]) AND (O_terms[Title/Abstract]))
```

**OpenAlex:**
```
"P_term" "I_term" "O_term"
```

---

## 🎯 PICO Cheat Sheet

| Component | Question | Examples |
|-----------|----------|----------|
| **P** | Who/What? | elderly, urban residents, workers |
| **I** | Intervention/Exposure? | cooling centers, heat waves, policy |
| **C** | Comparison? | no intervention, control areas |
| **O** | Outcome? | mortality, hospitalization, health |

**Tips:**
- C (Comparison) is optional for observational studies
- I can be an exposure (e.g., heat waves) not just intervention
- Include study design terms (RCT, evaluation, cohort)

---

## 📚 Examples

### Example 1: Intervention Study

**Topic:**
> "Effectiveness of early warning systems on heat-related mortality"

**PICO:**
- P: General population, elderly
- I: Early warning system, heat alert
- C: No warning system
- O: Heat-related mortality, death

**Query Structure:** `(P) AND (I) AND (C) AND (O)`

---

### Example 2: Exposure Study

**Topic:**
> "Urban heat islands and cardiovascular health"

**PICO:**
- P: Urban residents
- I: Urban heat island, temperature
- C: (Not applicable)
- O: Cardiovascular health, heart disease

**Query Structure:** `(P) AND (I) AND (O)`

---

### Example 3: Policy Study

**Topic:**
> "Green infrastructure policies and public health outcomes"

**PICO:**
- P: Urban populations
- I: Green infrastructure policy, urban planning
- C: Areas without policy
- O: Public health, mortality, morbidity

**Query Structure:** `(P) AND (I) AND (O)`

---

## 🔧 Customization

### Adjust PICO Elements

After generation, you can manually adjust:

```python
# Get result
result = query_team.generate_queries(topic)

# Modify PICO components
result['pulse_pico']['population'].append("new population term")
result['pulse_pico']['intervention'].extend(["term1", "term2"])

# Re-run Formulator with modified PICO
formulator_result = query_team._agent_formulator(result)
```

### Control Sensitivity vs Specificity

**High Sensitivity (Recall):**
- Include more synonyms in each PICO element
- Use broader population terms
- Add related concepts

**High Specificity (Precision):**
- Use specific terms
- Add methodological filters (RCT, controlled, evaluation)
- Narrow population definition

---

## ❓ FAQ

**Q: What if my topic doesn't fit PICO?**
- Try PECO (Exposure instead of Intervention)
- Try PEO (Experience instead of Comparison)
- The system is flexible - just describe your research question

**Q: Should I always include Comparison?**
- No! Comparison is optional
- Observational studies often don't have explicit comparisons
- Leave comparison empty if not applicable

**Q: Can I use PICO for non-health topics?**
- Yes! PICO works for any systematic review
- P = who/what, I = intervention/exposure, O = outcome
- Adapt the framework to your domain

**Q: How do I get better PICO results?**
- Write clear research topics with explicit elements
- Example: "In [population], what is the effect of [intervention] on [outcome]?"
- Include study design if relevant

---

## 📖 Full Documentation

- **Comprehensive Guide:** [PICO_FRAMEWORK_INTEGRATION.md](PICO_FRAMEWORK_INTEGRATION.md)
- **UNC Reference:** https://guides.lib.unc.edu/pico/frameworks
- **Cochrane Handbook:** https://training.cochrane.org/handbook

---

## 🎓 Training Resources

1. **UNC Health Sciences Library**
   - PICO Framework Guide
   - https://guides.lib.unc.edu/pico

2. **Cochrane Training**
   - Defining the Review Question (Chapter 4)
   - https://training.cochrane.org/handbook

3. **PRISMA Statement**
   - Systematic Review Guidelines
   - http://www.prisma-statement.org/

---

## ✅ Quick Validation Checklist

Before running your PICO query:

- [ ] Population clearly defined?
- [ ] Intervention/Exposure identified?
- [ ] Outcome measurable?
- [ ] Comparison needed? (If yes, defined?)
- [ ] Study design terms included?
- [ ] Synonyms comprehensive?
- [ ] Query structure: (P) AND (I) AND (O)?

---

**Need Help?**
- Run `python3 pico_example_test.py` for a working example
- Check [PICO_FRAMEWORK_INTEGRATION.md](PICO_FRAMEWORK_INTEGRATION.md) for details
- Review examples in this guide

**Happy Researching! 🎉**
