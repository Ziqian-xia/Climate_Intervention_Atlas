# 🎯 PICO Framework Integration

**Date:** March 25, 2026
**Version:** 1.0
**Status:** ✅ Implemented

---

## 📋 Overview

AutoSR now uses the **PICO Framework** for systematic literature review query generation, following evidence-based best practices from the UNC Health Sciences Library.

**PICO Reference:** https://guides.lib.unc.edu/pico/frameworks

---

## 🔍 What is PICO?

PICO is a structured framework for formulating clinical and research questions, widely used in systematic reviews and evidence synthesis.

### PICO Components

| Component | Meaning | Research Question | Example Keywords |
|-----------|---------|-------------------|------------------|
| **P** | Population/Patient/Problem | Who is the study about? | elderly, urban residents, heat-exposed workers |
| **I** | Intervention/Exposure | What is being done or studied? | cooling centers, heat waves, climate adaptation |
| **C** | Comparison/Control | What is the alternative? | no intervention, control group, pre-period |
| **O** | Outcome | What are you measuring? | mortality, hospitalization, health outcomes |

**Note:** Comparison (C) is optional for observational studies or when no explicit control exists.

---

## 🎨 How AutoSR Uses PICO

### Phase 1: Multi-Agent Query Generation

#### Agent 1: Pulse (PICO-Based Keyword Expansion)

**Before PICO:**
```
Input: "cooling centers and heat-related mortality"
Output: [flat keyword list]
- cooling center, heat refuge, mortality, death, extreme heat, ...
```

**After PICO:**
```
Input: "cooling centers and heat-related mortality"

Output: {
  "pico": {
    "population": ["general population", "elderly", "urban residents"],
    "intervention": ["cooling center", "cooling shelter", "heat refuge", "air-conditioned space"],
    "comparison": [],
    "outcome": ["heat-related mortality", "death", "excess mortality", "heat stroke"]
  },
  "study_design": ["intervention", "evaluation", "quasi-experimental"],
  "pico_statement": "In general populations (P), what is the effectiveness of cooling centers (I) in reducing heat-related mortality (O)?",
  "expanded_keywords": [all_combined_keywords]
}
```

**Benefits:**
- ✅ Structured keyword organization
- ✅ Clear research question formulation
- ✅ Comprehensive coverage of each PICO element
- ✅ Easier to identify missing elements

#### Agent 2: Formulator (PICO-Structured Query Construction)

**Before PICO:**
```
Query: TITLE-ABS-KEY("cooling center" OR "heat refuge" OR "mortality" OR "death")
Problem: Keywords mixed together, unclear structure
```

**After PICO:**
```
Query: TITLE-ABS-KEY(
  ("general population" OR "elderly" OR "urban residents")  -- P
  AND
  ("cooling center" OR "cooling shelter" OR "heat refuge")   -- I
  AND
  ("heat-related mortality" OR "death" OR "excess mortality") -- O
)

Structure: (P) AND (I) AND (O)
```

**Benefits:**
- ✅ Clear query structure matching PICO elements
- ✅ Logical grouping of synonyms within each element
- ✅ AND connects PICO blocks (high precision)
- ✅ OR connects synonyms within blocks (high sensitivity)
- ✅ Easier to debug and refine

---

## 📊 PICO Output Structure

### Pulse Agent Output

```json
{
  "pico": {
    "population": ["keyword1", "keyword2", ...],
    "intervention": ["keyword1", "keyword2", ...],
    "comparison": ["keyword1", "keyword2", ...],  // Empty if N/A
    "outcome": ["keyword1", "keyword2", ...]
  },
  "study_design": ["keyword1", "keyword2", ...],
  "expanded_keywords": ["all_keywords_flat_list"],
  "pico_statement": "Structured research question in PICO format",
  "reasoning": "Explanation of PICO identification and expansion"
}
```

### Formulator Agent Output

```json
{
  "elsevier_query": "TITLE-ABS-KEY((P) AND (I) AND (O))",
  "pubmed_query": "(P[Title/Abstract]) AND (I[Title/Abstract]) AND (O[Title/Abstract])",
  "openalex_query": "P I O keywords",
  "pico_structure": {
    "population": "Terms used for P",
    "intervention": "Terms used for I",
    "comparison": "Terms used for C or 'Not applicable'",
    "outcome": "Terms used for O"
  },
  "reasoning": "Explanation of PICO-based query construction"
}
```

---

## 🎓 PICO Examples

### Example 1: Intervention Study

**Topic:** "Effectiveness of early warning systems on heat-related mortality in elderly populations"

**PICO Analysis:**
```
P (Population):    elderly, older adults, senior citizens, aged ≥65
I (Intervention):  early warning system, heat alert, heat advisory, advance warning
C (Comparison):    no warning system, control areas (optional)
O (Outcome):       heat-related mortality, excess death, temperature-related death

Study Design:      evaluation, quasi-experimental, impact assessment
```

**PICO Statement:**
> "In elderly populations (P), what is the effectiveness of early warning systems (I) compared to no warning systems (C) in reducing heat-related mortality (O)?"

**Query Structure:**
```
(P) AND (I) AND (C) AND (O)
```

### Example 2: Observational Study

**Topic:** "Climate change impacts on mental health"

**PICO Analysis:**
```
P (Population):    general population, vulnerable groups, communities
I (Intervention):  climate change, global warming, extreme weather (exposure, not intervention)
C (Comparison):    [] (no explicit comparison)
O (Outcome):       mental health, psychological distress, anxiety, depression

Study Design:      observational, cohort, cross-sectional
```

**PICO Statement:**
> "In general populations (P), what is the impact of climate change (I) on mental health outcomes (O)?"

**Query Structure:**
```
(P) AND (I) AND (O)
```
Note: No C block since it's an observational study.

### Example 3: Mixed Research

**Topic:** "Green infrastructure and urban heat island effects on public health"

**PICO Analysis:**
```
P (Population):    urban residents, city populations, metropolitan areas
I (Intervention):  green infrastructure, urban trees, green spaces, parks, vegetation
C (Comparison):    areas without green infrastructure, gray infrastructure (optional)
O (Outcome):       urban heat island, temperature reduction, heat exposure, public health

Study Design:      observational, natural experiment, before-after
```

**PICO Statement:**
> "In urban populations (P), what is the effect of green infrastructure (I) compared to areas without green infrastructure (C) on urban heat island effects and public health outcomes (O)?"

**Query Structure:**
```
(P) AND (I) AND (O)
```
C can be implicit in the study design.

---

## 📈 Benefits of PICO Integration

### 1. **Improved Query Structure**
- Clear separation of concepts
- Logical Boolean organization
- Easier to balance sensitivity vs specificity

### 2. **Better Research Question Formulation**
- Structured thinking about research objectives
- Identification of missing elements
- Clearer scope definition

### 3. **Enhanced Reproducibility**
- Documented PICO rationale
- Transparent keyword selection
- Easier peer review and validation

### 4. **Flexible Application**
- Works for interventional studies (P-I-C-O)
- Works for observational studies (P-I-O)
- Works for exposure studies (P-E-O where E=exposure)

### 5. **Standardized Methodology**
- Follows evidence-based best practices
- Aligned with systematic review guidelines (PRISMA, Cochrane)
- Recognized by academic community

---

## 🔧 Technical Implementation

### Modified Components

1. **modules/m1_query_gen.py**
   - `_agent_pulse()`: Now returns PICO-structured output
   - `_agent_formulator()`: Now accepts PICO structure and builds queries accordingly
   - `generate_queries()`: Returns PICO information in results

2. **System Prompts**
   - Pulse: Added PICO framework guidance with examples
   - Formulator: Added PICO-based query construction instructions

3. **Output Schema**
   - Added `pulse_pico`: PICO dictionary with P/I/C/O arrays
   - Added `pulse_pico_statement`: Structured research question
   - Added `pulse_study_design`: Study design keywords
   - Added `formulator_pico_structure`: PICO structure used in queries

### Backward Compatibility

✅ **Fully backward compatible**
- `expanded_keywords` still provided as flat list
- Existing query parsing logic unchanged
- UI can display PICO structure optionally

---

## 🎯 User Guide

### For Researchers

**Writing Better Research Topics:**

❌ **Vague:**
> "climate and health"

✅ **PICO-Structured:**
> "In urban populations (P), what is the impact of extreme heat events (I) on cardiovascular mortality (O)?"

**Tips:**
1. Identify who/what the study is about (P)
2. Specify the exposure or intervention (I)
3. Define what you're measuring (O)
4. Include comparison if relevant (C)

### For Developers

**Accessing PICO Structure:**

```python
result = query_team.generate_queries(topic)

# Access PICO components
pico = result['pulse_pico']
population = pico['population']
intervention = pico['intervention']
outcome = pico['outcome']

# Access PICO statement
pico_statement = result['pulse_pico_statement']

# Access PICO structure used in queries
formulator_pico = result['formulator_pico_structure']
```

---

## 📚 References

1. **UNC Health Sciences Library - PICO Framework**
   - https://guides.lib.unc.edu/pico/frameworks
   - Comprehensive guide to PICO and related frameworks

2. **Cochrane Handbook for Systematic Reviews**
   - https://training.cochrane.org/handbook
   - Chapter 4: Defining the review question

3. **PRISMA Statement**
   - http://www.prisma-statement.org/
   - Preferred Reporting Items for Systematic Reviews

4. **Richardson et al. (1995)**
   - "The well-built clinical question: a key to evidence-based decisions"
   - ACP J Club, 123(3), A12-13
   - Original PICO framework paper

---

## 🔄 PICO Variants

AutoSR primarily uses **PICO**, but the framework is flexible for other variants:

| Variant | Components | Use Case |
|---------|------------|----------|
| **PICO** | P-I-C-O | Clinical interventions |
| **PECO** | P-E-C-O | Exposure studies (E = Exposure) |
| **PEO** | P-E-O | Qualitative research (E = Experience) |
| **SPICE** | S-P-I-C-E | Social sciences (S=Setting, E=Evaluation) |
| **SPIDER** | S-P-I-DE-R | Qualitative/mixed methods |

**Current Implementation:** PICO/PECO (uses "Intervention" field for both interventions and exposures)

---

## ✅ Validation

### Test Cases

1. **Test 1: Intervention Study**
   - Input: "cooling centers and heat-related mortality"
   - Expected P: populations, elderly
   - Expected I: cooling center, heat refuge
   - Expected O: mortality, death
   - Result: ✅ Passed

2. **Test 2: Exposure Study**
   - Input: "climate change impacts on mental health"
   - Expected P: populations, communities
   - Expected I: climate change, extreme weather
   - Expected O: mental health, anxiety
   - Result: ✅ Passed

3. **Test 3: No Explicit Comparison**
   - Input: "urban heat islands and public health"
   - Expected C: [] (empty)
   - Result: ✅ Passed

### Quality Checks

- ✅ PICO elements correctly identified
- ✅ Synonyms appropriately grouped
- ✅ Query structure follows (P) AND (I) AND (O) pattern
- ✅ Fallback to flat keywords if PICO parsing fails
- ✅ Backward compatible with existing code

---

## 🚀 Future Enhancements

1. **Interactive PICO Editor**
   - UI for users to review and edit PICO elements
   - Visual query builder based on PICO structure

2. **PICO Validation**
   - Check for completeness of PICO elements
   - Suggest missing components

3. **PICO-Based Query Refinement**
   - Allow users to adjust sensitivity per PICO element
   - P: broad/narrow, I: specific/general, O: proximal/distal

4. **Multi-Framework Support**
   - PECO for environmental exposures
   - SPIDER for mixed-methods research

5. **PICO Citation Export**
   - Generate PICO tables for manuscript methods sections
   - Export PICO structure for PROSPERO registration

---

## 📞 Support

**Questions about PICO?**
- See UNC guide: https://guides.lib.unc.edu/pico/frameworks
- Check Cochrane Handbook Chapter 4
- Review examples in this document

**Technical Issues?**
- Check `modules/m1_query_gen.py` implementation
- Review test cases above
- Examine log output for PICO parsing

---

**Document Version:** 1.0
**Last Updated:** 2026-03-25
**Author:** Claude Sonnet 4.5
**Integrated by:** Ziqian Xia
