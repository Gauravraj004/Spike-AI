# System Architecture - Quick Reference

## Overview

AI-driven screenshot diagnosis system using GPT-4o Vision to analyze web page rendering issues and generate intelligent capture recommendations.

---

## Architecture Flow

```
┌─────────────────┐
│  Input Files    │
│  - Screenshot   │
│  - HTML (opt)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTML Analysis   │
│ Extract full    │
│ structure data  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GPT-4o Vision   │
│ - Visual + HTML │
│ - AI Analysis   │
│ - Generate Recs │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Output          │
│ - JSON Reports  │
│ - CSV Summary   │
│ - Console Log   │
└─────────────────┘
```

---

## Core Components

### 1. HTML Structure Extractor
**Purpose:** Extract complete HTML structure for VLM analysis

**Extracts:**
- Element counts, DOM depth, section count
- Framework names: React, Vue, Angular, Next.js
- Class patterns with actual class names
- Modal elements with IDs
- Text content from sections
- Loading indicators, lazy images, AJAX patterns
- Script complexity metrics

**Output:** Complete structure object (not just counts)

### 2. GPT-4o Vision Analyzer
**Purpose:** Intelligent diagnosis via AI

**Process:**
1. Receives screenshot + complete HTML structure
2. Analyzes visually what's rendered
3. Correlates with HTML structure data
4. Identifies root causes intelligently
5. Generates context-aware recommendations

**Output:** Diagnosis + capture_recommendations object

### 3. Results Processor
**Purpose:** Format and export analysis

**Outputs:**
- Individual JSON files per case
- CSV summary with all fields
- Console logs with recommendations

---

## Key Workflow Stages

### Stage 1: Initialization
- Load API key from `.env`
- Create output directories
- Scan for PNG screenshots
- Sort files alphabetically

### Stage 2: HTML Analysis (Per Screenshot)
```python
analyze_html_structure(html_path):
  - Parse with BeautifulSoup
  - Extract complete structure
  - Count elements, find frameworks
  - Detect modals, loaders, lazy images
  - Return full data object (NO recommendations)
```

### Stage 3: VLM Analysis
```python
diagnose_screenshot(screenshot, html_data):
  - Encode screenshot as base64
  - Build prompt with HTML structure
  - Call GPT-4o Vision API
  - VLM analyzes visual + structure
  - VLM generates recommendations
  - Parse JSON response
```

### Stage 4: Output Generation
- Save individual JSON per case
- Aggregate CSV with all cases
- Display console summary
- Calculate total cost/tokens

---

## Data Structures

### HTML Analysis Output
```json
{
  "total_elements": 48,
  "main_sections_count": 3,
  "modal_elements_count": 1,
  "dom_depth": 12,
  "text_content_duplicates": [],
  "suspicious_class_patterns": [
    {"class_name": "article-card", "occurrence_count": 10}
  ],
  "modal_element_ids": ["cookie-consent"],
  "capture_analysis": {
    "is_spa": true,
    "frameworks_detected": ["React"],
    "loading_indicators_count": 2,
    "lazy_images_count": 10,
    "script_complexity": "high",
    "has_ajax_patterns": true,
    "modals_count": 1
  }
}
```

### VLM Response Structure
```json
{
  "status": "CORRECT" | "BROKEN",
  "issue_type": "partial_load" | "js_render_failure" | "normal_page",
  "severity": "critical" | "major" | "minor" | "none",
  "confidence": 0.95,
  "diagnosis": "Full explanation...",
  "capture_recommendations": {
    "primary_issue": "SPA captured before hydration",
    "wait_strategy": "network-idle + selector-based",
    "wait_duration": "3-5 seconds",
    "selectors_to_wait_for": [".main-content"],
    "scroll_needed": false,
    "modal_handling": "Dismiss if present",
    "technical_implementation": "await page.waitForLoadState('networkidle')..."
  }
}
```

---

## Technical Specifications

### Model
- **Engine:** GPT-4o with Vision
- **Temperature:** 0.1 (low randomness)
- **Detail Level:** high (high-resolution)
- **Max Tokens:** unlimited
- **Timeout:** 180 seconds

### Cost
- **Input:** $2.50 per 1M tokens
- **Output:** $10.00 per 1M tokens
- **Average per screenshot:** $0.008-0.011
- **Typical tokens:** 2,500-3,000 input, 250-370 output

### Performance
- **Processing time:** 10-48 seconds per screenshot
- **Retry logic:** 3 attempts with exponential backoff
- **Success rate:** >95%

---

## Key Design Principles

### 1. AI-Driven Analysis
The VLM receives complete HTML structure (class names, IDs, framework names) along with the screenshot. It intelligently analyzes patterns like "48 elements + React framework + blank screen = SPA captured before hydration" to generate context-aware recommendations.

### 2. Complete Data for Context
The system sends full HTML structure including:
- Actual class names (not just counts)
- Framework names (React, Vue, Angular, Next.js)
- Modal element IDs
- Text content snippets
- Loading indicator patterns

### 3. HTML as Context
- HTML shows what should be on page
- Screenshot shows what actually rendered
- VLM correlates discrepancies

### 4. Flexible & Adaptive
- VLM adapts to novel patterns
- Works with new frameworks without code updates
- Handles diverse page types (SPAs, static, hybrid)

---

## Edge Cases & Limitations

### Limitations
1. **No JavaScript execution:** Analyzes static HTML, not runtime DOM
2. **English-centric:** VLM trained primarily on English content
3. **Requires API:** Cannot work offline
4. **Cost scales linearly:** Each screenshot incurs API cost

### Handled Edge Cases
- ✅ Missing HTML files (visual-only analysis)
- ✅ Filename mismatches (suffix stripping)
- ✅ Malformed JSON responses (auto-repair)
- ✅ API timeouts (retry logic)
- ✅ Marketing patterns vs bugs (VLM distinguishes)

---

## Output Files

### Individual JSON (`results/*.json`)
- Complete VLM analysis
- Full HTML structure
- Capture recommendations object
- Token metrics and cost

### CSV Summary (`results/diagnosis_summary.csv`)
- All cases in tabular format
- Full text fields (no truncation)
- VLM recommendations formatted
- Aggregated metrics

### Console Output
- Real-time progress per case
- Top capture recommendations
- Token usage and cost per case
- Final summary statistics

---

## Extension Points

### Adding New Detection Rules
- Update VLM prompt with new patterns to watch for
- No code changes needed for new frameworks/patterns

### Supporting New Output Formats
- Add exporter in results processing stage
- Currently supports: JSON, CSV, Console

### Multi-language Support
- Add language detection to HTML analysis
- Include language context in VLM prompt
- VLM naturally handles multiple languages

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
echo "OPENAI_API_KEY=your_key" > .env

# 3. Add files
# Place screenshots in: data/screenshots/*.png
# Place HTML (optional): data/html/*.html

# 4. Run analysis
python web_diagnosis.py

# 5. Check results
# JSON: diagnosis_results/*.json
# CSV: diagnosis_results/diagnosis_summary.csv
```

---

**Architecture Type:** AI-Driven Analysis  
**Intelligence Source:** GPT-4o Vision  
**Primary Innovation:** VLM analyzes complete HTML structure + screenshot together for context-aware recommendations
