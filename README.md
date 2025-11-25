# Web Screenshot Diagnosis with AI-Driven Capture Analysis

Advanced VLM-powered system using GPT-4o Vision to diagnose rendering issues **AND generate intelligent capture recommendations** based on HTML metrics.

## ✅ Key Features

### 🔍 Intelligent Visual Diagnosis
- **GPT-4o Vision Analysis**: AI detects rendering issues in screenshots
- **HTML Correlation**: VLM analyzes raw HTML metrics to understand root causes
- **Accurate Detection**: Identifies rendering issues through intelligent analysis

### 🎯 AI-Generated Capture Recommendations
- **VLM Intelligence**: AI analyzes HTML metrics and generates recommendations
- **Context-Aware**: Correlates visual screenshot with HTML structure data
- **Actionable Fixes**: Provides specific code examples (Puppeteer/Playwright)
- **Wait Strategies**: Determines optimal wait conditions and timing
- **Selector Identification**: Suggests specific CSS selectors to wait for

### 📊 Comprehensive Output
- **Individual JSON Files**: Full diagnosis + capture recommendations
- **CSV/Excel Export**: All fields without truncation
- **Console Reports**: Top 3 issues per case with color-coded severity
- **Documentation**: Complete guides and examples

## What It Detects

🔍 **Visual Issues**:
  - Partial page loads / blank pages
  - Duplicate content (2x, 3x repetitions)
  - Cookie/modal overlays blocking content
  - Security blocks and error pages
  - JavaScript rendering failures

🎯 **Complete HTML Structure Data for VLM**:
  - Total elements + DOM depth + section count
  - Framework names ("React", "Vue", "Angular", "Next.js")
  - Actual class names and patterns (e.g., ".article-card", ".loading-spinner")
  - Modal elements with IDs for specific selectors
  - Text content from sections
  - Loading indicators + lazy images (counts + classes)
  - AJAX/fetch patterns in scripts
  - Script complexity and behavior indicators
  
  **VLM analyzes full structure + screenshot to generate intelligent recommendations**

## Performance

- **Cost**: ~$0.008-0.011 per screenshot (with full analysis)
- **Time**: 10-48 seconds per screenshot
- **Tokens**: 2,500-3,000 input, 250-370 output per case  

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Configure

Create `.env`:
```
OPENAI_API_KEY=your_openai_api_key
```

### 3. Run

```bash
python web_diagnosis.py
```

## Input

Place files in these directories:
- **Screenshots**: `data/screenshots/*.png` (required)
- **HTML Files**: `data/html/*.html` (optional but recommended for capture analysis)

## Output

### 1. Individual JSON Files (`diagnosis_results/*.json`)
Complete analysis with:
- Visual diagnosis and confidence scoring
- Raw HTML metrics (element counts, frameworks, etc.)
- **VLM-generated capture_recommendations object**
  - Primary issue identified
  - Wait strategy (time-based, selector-based, network-idle)
  - Wait duration in seconds
  - CSS selectors to wait for
  - Scroll requirements
  - Modal handling instructions
  - Technical implementation (Puppeteer/Playwright code)
- Token usage and cost metrics

### 2. Summary CSV (`diagnosis_results/diagnosis_summary.csv`)
Excel-compatible export with:
- All diagnosis fields (no truncation)
- **Complete capture improvement recommendations**
- **Formatted capture issues with cause/fix/technical details**
- HTML metadata (element count, frameworks, SPA detection)

### 3. Console Output
Real-time progress with:
- **Top 3 capture issues per screenshot** with severity badges
- VLM recommendations preview
- Token usage and cost tracking

## Example Output Structure

```json
{
  "analysis": {
    "status": "BROKEN",
    "diagnosis": "Page appears to be SPA with minimal HTML...",
    "capture_improvement": "Wait 3-5 seconds after page load..."
  },
  "capture_recommendations": {
    "top_recommendation": "Wait 3-5 seconds after page load for JavaScript to populate DOM",
    "all_issues": [
      {
        "issue": "Issue description",
        "cause": "Root cause analysis",
        "recommendation": "Actionable fix recommendation",
        "technical": "Implementation code example",
        "severity": "critical|major|minor"
      }
    ]
  }
}
```

## How It Works

### Dual Analysis Approach

1. **HTML Structure Analysis** (Local)
   - Parse DOM with BeautifulSoup
   - Detect frameworks (React, Vue, Next.js, Angular)
   - Find loading indicators and modals
   - Analyze script complexity and AJAX patterns
   - **Generate capture issue recommendations**

2. **Visual Diagnosis** (Cloud - GPT-4o Vision)
   - Encode screenshot as base64
   - Build enhanced prompt with HTML context
   - AI analyzes visual rendering issues
   - **Provides capture improvement suggestions**

3. **Combined Output**
   - Correlate HTML structure with visual issues
   - Rank recommendations by severity
   - Generate actionable technical fixes
   - Export to JSON, CSV, and console

### Why This Approach?

✅ **Accurate Root Cause Analysis**: Correlates HTML structure with visual issues  
✅ **Actionable Recommendations**: Specific code examples, not generic advice  
✅ **Prioritized Fixes**: Severity ranking (Critical → Major → Minor)  
✅ **Complete Context**: VLM sees both image AND HTML analysis  
✅ **Cost Effective**: HTML analysis is local/free, VLM provides intelligence

## Example Console Output

```
================================================================================
🔍 Analyzing: [screenshot-name]
================================================================================
🤖 Analyzing with GPT-4o vision model...

✅ Analysis Complete:
   Status: BROKEN/CORRECT
   Issue Type: [detected-issue-type]
   Severity: [critical/major/minor]
   Confidence: [percentage]

📋 Diagnosis: [AI-generated diagnosis]

🎯 CAPTURE IMPROVEMENT RECOMMENDATIONS:
   [VLM-generated recommendations with severity, cause, and technical fix]

💡 VLM Recommendation: [Detailed recommendation from AI]

📊 Token Usage:
   Input Tokens: [count]
   Output Tokens: [count]
   Total Tokens: [count]
   Cost: $[amount]
   Time: [seconds]s
   💾 Saved: diagnosis_results\[filename].json
```

## Documentation

📚 **Available Documentation:**

- **[WORKFLOW_EXPLANATION.md](WORKFLOW_EXPLANATION.md)** - Complete step-by-step system walkthrough
  - Phase-by-phase execution details (Initialization → HTML Analysis → VLM Analysis → Output)
  - Code locations and data flow
  - Real-world examples with input/output

- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Technical architecture (5 pages)
  - System components and design
  - Data structures and API integration
  - Performance metrics and cost analysis
  - Edge cases and limitations

- **[MERMAID_DIAGRAMS.md](MERMAID_DIAGRAMS.md)** - Visual diagrams
  - Architecture flow diagram
  - Data processing pipeline
  - Component interactions

## Cost Breakdown

- **Model**: GPT-4o ($2.50 per 1M input, $10.00 per 1M output)
- **Avg Tokens**: 1,558 per case
- **Avg Cost**: $0.0045 per screenshot
- **100 screenshots**: ~$0.45
- **1,000 screenshots**: ~$4.50



