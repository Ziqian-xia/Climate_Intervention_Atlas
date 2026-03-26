# Publication-Quality Figure: Robustness Analysis

This directory contains high-quality figures for the query robustness analysis.

## Files

### Main Figure (3-Panel Comprehensive Analysis)

- **Robustness_Analysis_Figure.png** (326 KB)
  - Format: PNG raster image
  - Resolution: 300 DPI (publication quality)
  - Dimensions: 16 × 14 inches (40.6 × 35.6 cm)
  - Best for: Presentations, reports, web display

- **Robustness_Analysis_Figure.pdf** (6.9 KB)
  - Format: PDF vector graphics
  - Resolution: Scalable (infinite)
  - Best for: Journal submissions, print publications, editing in Illustrator

## Figure Content

### Panel A: Result Distribution (Top, Full Width)
- **What it shows**: Bar chart of papers retrieved across 20 query variations
- **Color coding**:
  - 🟢 Green: Good (100-1,500 papers) - 12 queries
  - 🟠 Orange: Acceptable (1,500-5,000 papers) - 6 queries
  - 🔴 Red: Too Narrow (<100 papers) - 1 query
  - 🔴 Dark Red: Too Broad (>5,000 papers) - 1 query (Variation 2 defect)
- **Highlight**: Variation 1 (recommended) marked with blue border
- **Statistics box**: CV = 378.6%, Range: 9-87,884, Median: 499

### Panel B: Top Expanding Terms (Bottom Left)
- **What it shows**: Top 8 terms that INCREASE result count
- **Visualization**: Red horizontal bar chart
- **Interpretation**: Generic methodology terms (must be combined with domain constraints)
- **Top terms**:
  1. discontinuity threshold: +87,089 papers (+10,968%)
  2. event study design: +87,089 papers (+10,968%)
  3. fixed effects: +87,089 papers (+10,968%)
  4. endogeneity: +87,089 papers (+10,968%)
  5. parallel trends: +87,089 papers (+10,968%)
  6. matching estimator: +87,089 papers (+10,968%)
  7. identification strategy: +87,089 papers (+10,968%)
  8. diff-in-diff: +87,089 papers (+10,968%)

### Panel C: Top Restricting Terms (Bottom Right)
- **What it shows**: Top 8 terms that DECREASE result count
- **Visualization**: Green horizontal bar chart
- **Interpretation**: Domain-specific terms (heat-health interventions)
- **Top terms**:
  1. excess mortality: -43,891 papers (-98.3%)
  2. heat action plan: -28,637 papers (-97.1%)
  3. heat-related mortality: -18,049 papers (-96.6%)
  4. heat warning system: -11,046 papers (-93.8%)
  5. heat-related death: -11,003 papers (-93.6%)
  6. heat alert system: -8,304 papers (-93.5%)
  7. cardiovascular mortality: -7,656 papers (-93.2%)
  8. heat early warning: -7,347 papers (-90.8%)

## Design Features

✓ **300 DPI resolution** (meets most journal requirements)
✓ **Professional color palette** (color-blind friendly)
✓ **Clear fonts and labels** (Arial/Helvetica)
✓ **Black borders** for visual clarity
✓ **Grid lines** for easier reading
✓ **Statistics boxes** and annotations
✓ **Complete legends**
✓ **Panel labels** (A, B, C)
✓ **White background** (suitable for printing)
✓ **Vector PDF format** (lossless scaling)

## Usage Recommendations

### For Presentations/Reports
- Use the **PNG file**
- Insert directly into PowerPoint, Keynote, or Word
- 300 DPI ensures crisp display

### For Journal Submissions
- Use the **PDF file** (vector graphics)
- Lossless scaling to any size
- Editable in Adobe Illustrator if needed
- Meets most journal technical requirements

### For Web Display
- Use the **PNG file**
- Can be compressed further without quality loss
- Fast loading times

### For Print Publications
- Use the **PDF file**
- CMYK color mode compatible
- High-quality print output

## Key Findings Illustrated

1. **Extreme Query Instability** (CV = 378.6%)
   - Results range from 9 to 87,884 papers (9,765:1 ratio)

2. **Critical Defect in Variation 2**
   - Missing health intervention terms
   - Retrieved 87,884 papers (85% of total)
   - Demonstrates catastrophic failure mode

3. **Term Sensitivity Patterns**
   - Generic methodology terms massively expand results
   - Domain-specific terms effectively narrow to target literature
   - Balance is crucial for successful queries

4. **Recommended Action**
   - Use Variation 1 (219 papers)
   - Balanced three-concept structure
   - Good precision and recall

## How to View

### On Mac:
```bash
# Open in default viewer
open Robustness_Analysis_Figure.png

# Open in Preview
open -a Preview Robustness_Analysis_Figure.pdf

# View in file manager
open .
```

### On Windows:
```bash
# Open in default viewer
start Robustness_Analysis_Figure.png

# Open PDF in Adobe Acrobat
start Robustness_Analysis_Figure.pdf
```

### In VS Code:
```bash
code Robustness_Analysis_Figure.png
```

## Regenerating the Figure

If you need to regenerate the figure (e.g., after data updates):

```bash
cd robustness_testing/results/20260325_194108_complete
Rscript generate_figure_temp.R
```

Requirements:
- R (≥ 4.0)
- R packages: ggplot2, dplyr, jsonlite, gridExtra, scales, ggpubr

## Citation

If you use this figure in publications, please cite:

```
Auto-SLR Query Robustness Analysis (2026). Query Generation Stability Test:
20 Variations on Heat-Health Intervention Literature.
Internal Research Report, March 25, 2026.
```

## Contact

For questions about the figure or data, contact the Auto-SLR research team.

---

**Figure Generated:** March 25, 2026
**Software:** R 4.x with ggplot2
**Analysis:** Python 3.11+ with pandas, scipy
