# Screenshot Quality Diagnosis Pipeline

**An intelligent AI-powered system that automatically detects and diagnoses screenshot capture failures in webpages.**

Determines if screenshots are **broken** (due to tool failures or webpage blockers) or **correct**, providing actionable suggestions to improve your screenshot capture tool.

---

## 📋 Overview

This pipeline analyzes webpage screenshots to detect quality issues using a **2-stage hybrid approach**:

1. **Stage 1 (CV Analysis)**: Fast computer vision checks for obvious issues (blank pages, duplicate content)
2. **Stage 2 (LLM Analysis)**: Semantic HTML analysis to understand root causes (cookie modals, security challenges, missing resources)

**Key Features:**
- ✅ **Universal**: Works on any website without custom configuration
- ✅ **Accurate**: Semantic understanding using LLM (not brittle pattern matching)
- ✅ **Fast**: ~4 seconds per screenshot (CV is instant, LLM calls are cached)
- ✅ **Cost-Effective**: Uses free Groq API (Llama 3.3 70B)
- ✅ **Actionable**: Provides tool-specific fixes, not vague suggestions

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Free API Keys**:
  - [Groq API Key](https://console.groq.com/) (for LLM analysis)

### Installation

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd Spikeai
```

2. **Create virtual environment**:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure API key**:
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your Groq API key
GROQ_API_KEY=your_groq_api_key_here
```

### Usage

1. **Prepare your data**:
   - Place HTML files in `data/html/`
   - Place screenshot images (PNG) in `data/screenshots/`
   - **Important**: Filenames must match (e.g., `page1.html` and `page1.png`)

2. **Run the pipeline**:
```bash
python main.py
```

3. **View results**:
   - **Console**: Real-time progress and summary
   - **Excel**: `diagnosis_report.xlsx` (formatted report)
   - **CSV**: `diagnosis_report.csv` (import-friendly)
   - **JSON**: `results/<case_name>.json` (individual diagnoses)

---

## 📊 Output Format

### JSON Report (per case)
```json
{
  "case_name": "example_page",
  "status": "broken",
  "root_cause": "Cookie consent modal blocking content",
  "diagnosis": "Cookie consent modal blocking content",
  "suggested_fix": "TOOL: Detect and dismiss overlays/modals before capture",
  "confidence": 0.90,
  "evidence": "CookieHub script detected in HTML, CV detected overlay at top-right"
}
```

### CSV Report
```csv
Case Name,Status,Root Cause,Diagnosis,Suggested Fix,Confidence,Evidence
example_page,BROKEN,Cookie modal,Cookie consent modal blocking content,TOOL: Detect and dismiss overlays,0.90,CookieHub script detected
```

---

## 🏗️ Architecture

### Pipeline Flow

```
INPUT: Screenshot (.png) + HTML (.html)
          ↓
┌─────────────────────────────────────────┐
│  Stage 1: CV Analysis (0.5s, $0)       │
│  - Blank page detection                 │
│  - Duplicate content (SSIM-based)       │
│  - Low entropy detection                │
└─────────────────────────────────────────┘
          ↓
     Issue found?
          ↓ YES
┌─────────────────────────────────────────┐
│  Stage 2: LLM Semantic Analysis (3s)   │
│  - Analyze HTML structure               │
│  - Detect blocking scripts              │
│  - Identify security challenges         │
│  - Classify root cause                  │
└─────────────────────────────────────────┘
          ↓
OUTPUT: Status + Diagnosis + Fix Suggestion
```

### Detection Capabilities

| Issue Type | Detection Method | Example |
|------------|------------------|---------|
| **Blank Pages** | CV: Low entropy, few edges | Page failed to load entirely |
| **Duplicate Content** | CV: SSIM similarity > 0.65 | Screenshot stitching bug (repeated sections) |
| **Cookie Modals** | CV: Overlay detection → LLM: Script analysis | CookieHub modal blocking content |
| **Security Challenges** | CV: Low entropy → LLM: Security keywords | Cloudflare captcha blocking page |
| **Missing Resources** | CV: Blank → LLM: Missing CSS/JS | Stylesheet failed to load |

---

## ⚙️ Configuration

### CV Thresholds (in `src/config.py`)

```python
# Blank page detection
ENTROPY_LOW_THRESHOLD = 1.5        # Shannon entropy threshold
EDGE_COUNT_LOW_THRESHOLD = 50000   # Minimum edge pixels

# Duplicate detection
SSIM_DUPLICATE_THRESHOLD = 0.65    # Structural similarity threshold
NUM_SLICES = 20                    # Vertical slices for comparison
```

### LLM Settings (in `.env`)

```bash
GROQ_API_KEY=your_key_here          # Required: Groq API key
LLM_MODEL=llama-3.3-70b-versatile   # Optional: Model override
```

---

## 🔍 How It Works

### Stage 1: Computer Vision Analysis

**Fast heuristics for obvious failures (0.5s, $0 cost)**

1. **Blank Detection**:
   - Calculate Shannon entropy (measures content complexity)
   - Count edge pixels using Canny edge detection
   - Flag if entropy < 1.5 AND edges < 50,000

2. **Duplicate Detection**:
   - Slice screenshot into 20 vertical sections
   - Compare slices using SSIM (Structural Similarity Index)
   - Detect 2x/3x repetition patterns (stitching bugs)

3. **Early Exit**:
   - If issue found, proceed to Stage 2 for root cause analysis
   - If no issues, check HTML with LLM for hidden problems

### Stage 2: LLM Semantic Analysis

**Intelligent HTML analysis for root causes (3s, $0 with free API)**

1. **HTML Summarization**:
   - Extract visible text (first 1000 chars)
   - List external scripts (blocking indicators)
   - Identify CSS resources
   - Detect security/blocking keywords

2. **LLM Reasoning**:
   - Correlate CV finding with HTML structure
   - Identify specific blocking elements (cookie scripts, captcha)
   - Distinguish tool bugs from webpage characteristics
   - Generate human-readable diagnosis

3. **Fix Generation**:
   - Provide actionable tool improvements
   - Focus on screenshot tool fixes (not page issues)
   - Examples: "Dismiss modals before capture", "Fix stitching algorithm"

---

## 📝 Assumptions & Limitations

### Assumptions

1. **Screenshots are full-page captures** (not viewport-only)
2. **HTML files contain complete page source** (post-JS execution)
3. **Filenames match** between HTML and screenshot (e.g., `page1.html` ↔ `page1.png`)
4. **Screenshots captured AFTER page load** (not during loading)

### Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **Non-English content** | Text analysis less accurate | Add multilingual NLP |
| **Dynamic content** | May miss time-based issues | Implement temporal analysis |
| **Sophisticated anti-bot** | Cannot detect Cloudflare Turnstile | Pattern matching for known UIs |
| **Canvas/WebGL** | Cannot analyze programmatic rendering | Add screenshot comparison with reference |

### Known Edge Cases

**Handled**:
- ✅ Cookie consent modals
- ✅ Blank/partially rendered pages
- ✅ Stitching artifacts (duplicate sections)
- ✅ Dark themes (not flagged as blank)

**Not Handled**:
- ❌ Animated GIFs/videos
- ❌ Shadow DOM content
- ❌ Advanced anti-bot (reCAPTCHA v3, hCaptcha)

---

## 🎯 Extensibility

### Adding New Failure Detection

**Example: Detect lazy-load issues**

1. **Add CV metric** (`stage1_global.py`):
```python
def detect_placeholder_images(image):
    gray_pixels = count_gray_regions(image)
    return gray_pixels / total_pixels > 0.3
```

2. **Update LLM prompt** (`llm_analyzer.py`):
```python
# Add to context
"CV Finding: {cv_finding} + High placeholder content (30%)"
```

3. **Add fix suggestion**:
```python
if "placeholder" in diagnosis:
    return "TOOL: Scroll through page to trigger lazy-load before capture"
```

### Adding New HTML Indicators

Modify `llm_analyzer.py` to extract additional signals:
```python
# Extract meta tags
meta_tags = soup.find_all('meta')

# Check for SPA frameworks
is_spa = any('react' in str(script) for script in scripts)
```

---

## 🧪 Testing

Run on sample cases:
```bash
# Place test files in data/html/ and data/screenshots/
python main.py
```

Expected output:
- Console shows per-case progress
- JSON files in `results/`
- Excel and CSV reports generated

---

## 🛠️ Troubleshooting

### Common Issues

**1. "No GROQ_API_KEY configured"**
- Solution: Create `.env` file with `GROQ_API_KEY=your_key`

**2. "No test cases found"**
- Solution: Ensure files in `data/html/` and `data/screenshots/` have matching names

**3. "UnicodeEncodeError" (Windows)**
- Solution: Run in PowerShell or set `chcp 65001` for UTF-8

**4. "Module not found: cv2"**
- Solution: `pip install opencv-python`

---

## 📦 Dependencies

### Core Libraries

- `opencv-python` - Computer vision operations
- `numpy` - Numerical computations
- `scikit-image` - SSIM calculations
- `beautifulsoup4` - HTML parsing
- `groq` - LLM API client
- `python-dotenv` - Environment configuration
- `openpyxl` - Excel report generation

### Optional

- `Pillow` - Image processing (if needed)
- `requests` - HTTP requests (included in standard library)

---

## 📈 Performance

- **Speed**: ~4 seconds per case
  - Stage 1 (CV): 0.5s
  - Stage 2 (LLM): 3s (API call)
- **Cost**: $0 (using free Groq API)
- **Accuracy**: Validated on diverse webpage types

---

## 🤝 Contributing

This is a production-ready pipeline designed for extensibility. To add new features:

1. Fork the repository
2. Create a feature branch
3. Add detection logic to `stage1_global.py` or `llm_analyzer.py`
4. Update tests and documentation
5. Submit a pull request

---

## 📧 Support

For questions or issues, open a GitHub issue.

---

**For detailed technical workflow, see [WORKFLOW.md](WORKFLOW.md)**
