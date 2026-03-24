# Data Import Guide - Phase 3 & 4

**Complete guide on importing your own data to skip phases**

---

## 📋 Overview

The import portal allows you to bring your own literature search results and jump directly to:
- **Phase 3**: Abstract Screening (requires Title + Abstract)
- **Phase 4**: Full-Text Download (requires Title + Abstract + DOI)

---

## 🎯 Supported Data Sources

### ✅ Compatible Sources

1. **Manual Literature Searches**
   - PubMed exports
   - Web of Science exports
   - Scopus exports
   - Google Scholar (via export tools)
   - Manual spreadsheets

2. **Reference Managers**
   - Zotero (CSV export)
   - Mendeley (CSV export)
   - EndNote (CSV export)
   - RefWorks (CSV export)

3. **Database Exports**
   - OpenAlex API results
   - Europe PMC
   - IEEE Xplore
   - ACM Digital Library
   - Any CSV with title/abstract/DOI

4. **Previous SLR Results**
   - Existing systematic review data
   - Meta-analysis datasets
   - Screening results from other tools

---

## 📄 Required Data Format

### File Type
- **Required**: CSV (Comma-Separated Values)
- **Encoding**: UTF-8 (recommended)
- **Size Limit**: No hard limit (tested up to 10,000 papers)

### Required Columns

#### For Phase 3 (Screening)
| Column | Required? | Description | Example |
|--------|-----------|-------------|---------|
| **Title** | ✅ Yes | Paper title | "Urban heat islands and green infrastructure" |
| **Abstract** | ✅ Yes | Paper abstract | "Green roofs can reduce urban temperatures..." |
| DOI | ⚠️ Optional | Digital Object Identifier | "10.1234/example.001" |
| Authors | ⚠️ Optional | Author names | "Smith J, Jones A" |
| Year | ⚠️ Optional | Publication year | "2023" |
| Journal | ⚠️ Optional | Journal name | "Nature Climate Change" |

#### For Phase 4 (Full-Text Download)
| Column | Required? | Description | Example |
|--------|-----------|-------------|---------|
| **Title** | ✅ Yes | Paper title | "Urban heat islands and green infrastructure" |
| **Abstract** | ✅ Yes | Paper abstract | "Green roofs can reduce urban temperatures..." |
| **DOI** | ✅ Yes | Digital Object Identifier | "10.1234/example.001" |
| Authors | ⚠️ Optional | Author names | "Smith J, Jones A" |
| Year | ⚠️ Optional | Publication year | "2023" |

### Column Names

**Flexible column name matching** - We accept variations:
- **Title**: `title`, `Title`, `paper_title`, `article_title`, `work_title`
- **Abstract**: `abstract`, `Abstract`, `description`, `summary`, `ab`
- **DOI**: `doi`, `DOI`, `digital_object_identifier`
- **Authors**: `authors`, `author`, `creator`, `contributors`
- **Year**: `year`, `publication_year`, `pub_year`, `date`

---

## 📊 Data Quality Requirements

### Minimum Requirements

**For reliable screening**:
- ✅ At least 80% of papers should have titles
- ✅ At least 70% of papers should have abstracts
- ✅ No completely empty rows
- ✅ Consistent encoding (UTF-8)

**For full-text download**:
- ✅ At least 90% of papers should have valid DOIs
- ✅ DOIs should be in standard format (e.g., "10.1234/journal.2023.001")

### Data Validation Checks

When you import, the system checks:
1. ✅ File is valid CSV
2. ✅ Required columns are present
3. ✅ At least one row of data exists
4. ✅ No critical parsing errors

---

## 📝 Example Data Formats

### Example 1: Minimal Format (Phase 3)

```csv
title,abstract
"Urban heat islands","Green roofs can reduce temperatures by 2-5°C"
"Cooling centers","Community cooling centers reduced mortality by 40%"
"Climate adaptation","This review examines 50 studies on heat adaptation"
```

### Example 2: Standard Format (Phase 3)

```csv
title,abstract,doi,authors,year
"Urban heat islands and green infrastructure","Green roofs can reduce urban temperatures by 2-5°C through evapotranspiration","10.1234/example.001","Smith J, Jones A",2023
"Cooling center effectiveness during heat waves","Community cooling centers reduced heat-related mortality by 40%","10.1234/example.002","Chen L, Kumar R",2022
```

### Example 3: Full Format (Phase 4)

```csv
title,abstract,doi,authors,year,journal,citations
"Urban heat islands and green infrastructure","Green roofs can reduce urban temperatures by 2-5°C through evapotranspiration","10.1234/example.001","Smith J, Jones A",2023,"Nature Climate Change",45
"Cooling center effectiveness during heat waves","Community cooling centers reduced heat-related mortality by 40% during the 2022 heat wave","10.1234/example.002","Chen L, Kumar R",2022,"The Lancet Planetary Health",23
```

### Example 4: PubMed Export Format

```csv
PMID,Title,Abstract,Authors,Journal,Year,DOI
12345678,"Heat waves and mortality","Our study examined...",Smith J; Jones A,NEJM,2023,10.1056/NEJMoa123456
```

### Example 5: Zotero Export Format

```csv
Item Type,Title,Abstract Text,Author,Publication Year,DOI
journalArticle,"Urban heat islands","Green roofs...","Smith, John; Jones, Alice",2023,10.1234/example.001
```

---

## 🚀 Step-by-Step Import Instructions

### Prepare Your Data

1. **Export from your source**
   - Use CSV format
   - Include Title and Abstract columns
   - Add DOI if available

2. **Check your file**
   - Open in Excel/Sheets to verify format
   - Ensure UTF-8 encoding
   - Remove any completely empty rows
   - Save as CSV

3. **Validate columns**
   - Title column has data
   - Abstract column has data
   - DOI column exists (if jumping to Phase 4)

### Import Process

1. **Launch Streamlit**
   ```bash
   source .venv/bin/activate
   streamlit run app.py
   ```

2. **Open Import Portal**
   - Look in the **Sidebar**
   - Find **"📥 Import Data (Skip Phases)"**
   - Click to expand

3. **Upload File**
   - Drag & drop your CSV
   - Or click "Browse files"
   - Wait for upload (1-5 seconds)

4. **Review Preview**
   - Check first 3 rows
   - Verify data looks correct
   - Check for encoding issues

5. **Map Columns**
   - **Title Column**: Select your title column
   - **Abstract Column**: Select your abstract column
   - **DOI Column**: Select your DOI column (optional)
   - **Authors Column**: Select your authors column (optional)

6. **Choose Destination**
   - **Phase 3**: Click "→ Phase 3 (Screening)"
   - **Phase 4**: Click "→ Phase 4 (Download)" (requires DOI)

7. **Proceed**
   - App jumps to selected phase
   - Your data is ready to use!

---

## 🔍 Testing Different Data Types

### Test 1: Basic Import (Minimal Data)

**File**: `test_minimal.csv`
```csv
title,abstract
"Paper 1","This is abstract 1"
"Paper 2","This is abstract 2"
```

**Expected**: Should import successfully, jump to Phase 3

### Test 2: Complete Import (Full Metadata)

**File**: `test_complete.csv`
```csv
title,abstract,doi,authors,year,journal
"Paper 1","Abstract 1","10.1234/test.001","Smith J",2023,"Nature"
"Paper 2","Abstract 2","10.1234/test.002","Jones A",2022,"Science"
```

**Expected**: Should import with all metadata preserved

### Test 3: PubMed Format

**File**: `test_pubmed.csv`
```csv
PMID,Title,Abstract,Authors,Journal,Year,DOI
12345678,"Test Paper","Test abstract","Smith J; Jones A","NEJM",2023,"10.1056/test"
```

**Expected**: Should detect columns and allow mapping

### Test 4: Large Dataset

**File**: `test_large.csv` (1000+ papers)

**Expected**:
- Upload may take 5-10 seconds
- Preview shows first 3 rows
- All data imports successfully

### Test 5: Mixed Quality Data

**File**: `test_mixed.csv`
```csv
title,abstract,doi
"Complete Paper","Full abstract text","10.1234/complete"
"No Abstract","","10.1234/no_abstract"
"","Abstract without title","10.1234/no_title"
"Partial","Short abstract",""
```

**Expected**:
- Row 1: ✅ Perfect
- Row 2: ⚠️ Warning (no abstract)
- Row 3: ❌ Error (no title)
- Row 4: ✅ OK (DOI optional for Phase 3)

---

## 🛠️ Troubleshooting

### Issue: "Cannot read file"

**Causes**:
- File is not CSV format
- File is corrupted
- Wrong encoding (not UTF-8)

**Solutions**:
1. Open in Excel, "Save As" → CSV (UTF-8)
2. Check file isn't empty
3. Remove special characters from column names

### Issue: "Required columns not found"

**Causes**:
- Column names don't match expected names
- No header row in CSV
- Columns are empty

**Solutions**:
1. Add header row with column names
2. Rename columns to standard names
3. Check column mapping dropdown

### Issue: "No data in preview"

**Causes**:
- All rows are empty
- File has headers but no data
- Encoding issue

**Solutions**:
1. Check file has data rows
2. Ensure UTF-8 encoding
3. Remove empty rows

### Issue: "DOI column required"

**Causes**:
- Trying to jump to Phase 4 without DOI
- DOI column is empty

**Solutions**:
1. Use Phase 3 instead (doesn't require DOI)
2. Add DOI column to your data
3. Fill in DOIs from another source

### Issue: "Some papers have no abstract"

**Causes**:
- Abstract column has missing values
- Common with some databases

**Solutions**:
1. ✅ Still import - screening will note missing abstracts
2. Fill in abstracts manually if possible
3. Exclude papers without abstracts before import

---

## 📦 Sample Data Files Provided

### 1. sample_import_data.csv (Included)

**Contents**: 10 papers on urban heat
**Format**: Complete (title, abstract, doi, authors, year)
**Use**: Perfect for testing all features

### 2. Create Your Own Test Files

**Minimal Test** (3 papers):
```csv
title,abstract
"Test 1","Abstract 1"
"Test 2","Abstract 2"
"Test 3","Abstract 3"
```

**PubMed Test** (export 5 papers from PubMed, save as CSV)

**Large Test** (export 100+ papers from any source)

---

## ✅ Quality Checklist

Before importing, verify:

- [ ] File is in CSV format
- [ ] Has header row with column names
- [ ] Title column is present and filled
- [ ] Abstract column is present and filled
- [ ] DOI column present (if jumping to Phase 4)
- [ ] No completely empty rows
- [ ] UTF-8 encoding
- [ ] File size < 50MB (for UI performance)
- [ ] Tested preview looks correct

---

## 🎯 Best Practices

### Data Preparation

1. **Clean your data first**
   - Remove duplicate papers
   - Fill in missing DOIs where possible
   - Standardize author names format
   - Remove special characters causing issues

2. **Use standard formats**
   - Prefer standard column names (title, abstract, doi)
   - Use ISO date format (YYYY-MM-DD)
   - Keep DOIs in standard format (10.xxxx/yyyy)

3. **Validate before import**
   - Open in spreadsheet software
   - Check for encoding issues
   - Verify all required columns present
   - Remove completely empty rows

### Import Strategy

**For Small Datasets (< 100 papers)**:
- Import directly
- No special preparation needed
- Should be instant

**For Medium Datasets (100-1000 papers)**:
- Check file size < 10MB
- Consider removing unused columns
- May take 5-10 seconds to import

**For Large Datasets (> 1000 papers)**:
- Split into smaller batches if issues occur
- Remove unused columns to reduce size
- Consider using Phase 2 search instead

---

## 🔬 Testing Scenarios

### Scenario 1: Existing Systematic Review

**You have**: Results from previous SLR with 500 papers
**Goal**: Re-screen with different criteria
**Steps**:
1. Export to CSV (title, abstract, doi)
2. Import to Phase 3
3. Enter new criteria
4. Run screening
5. Compare with previous results

### Scenario 2: Manual Literature Search

**You have**: 50 papers from manual Google Scholar search
**Goal**: Screen abstracts with AI
**Steps**:
1. Create CSV with titles and abstracts
2. Import to Phase 3
3. Configure screening criteria
4. Review AI decisions
5. Override if needed

### Scenario 3: Database Export

**You have**: PubMed search results (200 papers)
**Goal**: Download full-text PDFs
**Steps**:
1. Export PubMed results as CSV
2. Map columns (PMID → Title, Abstract, DOI)
3. Import to Phase 4
4. Download PDFs automatically
5. Get markdown versions

### Scenario 4: Collaborative Work

**You have**: Papers shared by colleague (CSV)
**Goal**: Screen and add to your review
**Steps**:
1. Receive CSV from colleague
2. Import to Phase 3
3. Apply your screening criteria
4. Share results back

---

## 📚 Data Source Examples

### PubMed Export

```csv
PMID,Title,Abstract,Authors,Journal,Publication Date,DOI
12345678,"Title here","Abstract text...","Smith J, Jones A","Journal Name",2023/01/15,10.1234/journal.2023.001
```

**Map to**:
- Title → Title
- Abstract → Abstract
- DOI → DOI
- Authors → Authors

### Scopus Export

```csv
Authors,Title,Year,Abstract,DOI,Source title,EID
"Smith, J., Jones, A.","Paper title",2023,"Abstract text...","10.1234/example","Journal Name",2-s2.0-12345678
```

**Map to**:
- Title → Title
- Abstract → Abstract
- DOI → DOI
- Authors → Authors

### Zotero Export

```csv
Item Type,Title,Abstract Text,Author,Publication Year,DOI,Publication Title
journalArticle,"Paper title","Abstract...","Smith, John; Jones, Alice",2023,10.1234/example,"Journal"
```

**Map to**:
- Title → Title
- Abstract Text → Abstract
- DOI → DOI
- Author → Authors

---

## 🎓 Advanced Tips

### Batch Processing

Import multiple datasets separately:
1. Import Dataset A → Screen → Export results
2. Import Dataset B → Screen → Export results
3. Merge results externally
4. Import merged → Phase 4

### Data Augmentation

Add metadata after import:
1. Import minimal data (title + abstract)
2. Screen papers
3. Export included papers
4. Add DOIs manually
5. Re-import for Phase 4

### Quality Control

Validate your import:
1. Import small sample first (10 papers)
2. Verify mapping is correct
3. Test screening on sample
4. Import full dataset if working

---

## 📊 Expected Performance

| Papers | Upload Time | Preview Load | Import Time |
|--------|-------------|--------------|-------------|
| 10 | < 1s | Instant | < 1s |
| 100 | 1-2s | Instant | 1-2s |
| 1,000 | 2-5s | 1s | 2-5s |
| 10,000 | 5-10s | 2-3s | 5-10s |

**Note**: Times vary based on file size and computer performance

---

## 🆘 Need Help?

If you encounter issues:

1. **Check this guide** - Most answers are here
2. **Try sample file** - `sample_import_data.csv` always works
3. **Simplify your data** - Remove extra columns, test with 3 papers
4. **Check encoding** - Save as CSV UTF-8
5. **Review error messages** - They usually tell you what's wrong

---

## ✨ Summary

**Import portal supports**:
- ✅ CSV files from any source
- ✅ Flexible column names
- ✅ Optional metadata (DOI, authors, year)
- ✅ Small to large datasets (10 - 10,000 papers)
- ✅ Jump to Phase 3 (screening) or Phase 4 (download)

**Required for Phase 3**: Title + Abstract
**Required for Phase 4**: Title + Abstract + DOI

**Test with**: `sample_import_data.csv` (provided, 10 papers)

**Ready to import!** 🚀
