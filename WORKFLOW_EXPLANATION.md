# Web Diagnosis System - Complete Workflow Explanation

## System Overview

**Purpose:** AI-driven screenshot diagnosis system that analyzes web page screenshots to detect rendering issues, UI bugs, and provides intelligent capture recommendations using GPT-4o Vision.

**Key Capabilities:**
- Detects content duplication (repeating sections, elements)
- Identifies blocking modals (cookie consent, security gates)
- Recognizes blank/failed pages and partial loads
- Analyzes layout integrity and visual hierarchy
- Provides HTML-level insights into root causes
- Generates intelligent capture recommendations
- Pure AI intelligence for diagnosis

**Technology Stack:**
- **Vision Model:** GPT-4o with high-detail image analysis
- **HTML Parser:** BeautifulSoup4
- **Output:** JSON (detailed reports) + CSV (summary)
- **API:** OpenAI GPT-4o API with unlimited token analysis

---

## Architecture Overview

```
Input Files (PNG + HTML)
    ↓
HTML Structure Analysis (BeautifulSoup)
    ↓
GPT-4o Vision Analysis (Screenshot + HTML Data)
    ↓
Intelligent Diagnosis + Capture Recommendations
    ↓
Output (JSON per case + CSV summary)
```

---

## Phase 1: Initialization

### Step 1.1: Environment Setup
```python
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
```
- Loads API key from `.env` file
- Validates environment configuration

### Step 1.2: Directory Structure
```python
SCREENSHOTS_DIR = Path("data/screenshots")
HTML_DIR = Path("data/html")
RESULTS_DIR = Path("diagnosis_results")
RESULTS_DIR.mkdir(exist_ok=True)
```
- **Input directories:**
  - `data/screenshots/` - PNG screenshot files
  - `data/html/` - Optional HTML source files
- **Output directory:**
  - `diagnosis_results/` - JSON reports + CSV summary

### Step 1.3: File Discovery
```python
screenshots = sorted(list(SCREENSHOTS_DIR.glob("*.png")))
```
- Scans for all PNG files in screenshots directory
- Sorts alphabetically for consistent processing order
- Case names derived from filenames (without .png extension)

---

## Phase 2: HTML Structure Analysis

### Step 2.1: HTML File Matching
```python
html_path = HTML_DIR / f"{case_name}.html"
if not html_path.exists() and case_name.endswith('_correct'):
    base_name = case_name.rsplit('_correct', 1)[0]
    html_path = HTML_DIR / f"{base_name}.html"
```
- Matches screenshot to corresponding HTML file
- Handles suffix variations (`_correct`, etc.)
- Proceeds with visual-only analysis if HTML not found

### Step 2.2: HTML Parsing
```python
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()
soup = BeautifulSoup(html_content, 'html.parser')
```
- Loads HTML content with UTF-8 encoding
- Parses into BeautifulSoup DOM tree
- Enables structural querying

### Step 2.3: Content Container Detection
```python
main_sections = soup.find_all(['main', 'article', 'section'], 
                              class_=lambda x: x and any(term in str(x).lower() 
                              for term in ['content', 'main', 'article', 'section', 'container']))
```
**Extracts:**
- Main content containers
- Article sections
- Primary content areas

**Purpose:** Identify major page structures for duplication analysis

### Step 2.4: Modal/Overlay Detection
```python
modals = soup.find_all(['div', 'section'], 
                       class_=lambda x: x and any(term in str(x).lower() 
                       for term in ['modal', 'overlay', 'popup', 'cookie', 'consent']))
```
**Identifies:**
- Modal dialogs
- Cookie consent banners
- Popup overlays
- Blocking elements

**Returns:** Element IDs for specific selector recommendations

### Step 2.5: Text Content Extraction
```python
section_texts = []
for section in main_sections[:10]:
    text = section.get_text(strip=True)[:500]
    if len(text) > 100:
        section_texts.append(text)
```
**Extracts:**
- First 500 characters from each major section
- Only sections with meaningful content (>100 chars)
- Limited to first 10 sections for performance

**Purpose:** Enable real text comparison (not just class counting)

### Step 2.6: Duplicate Content Detection
```python
text_duplicates = []
seen = {}
for idx, text in enumerate(section_texts):
    if text in seen:
        text_duplicates.append({
            'section_index': idx,
            'duplicate_of': seen[text],
            'text_preview': text[:100]
        })
    else:
        seen[text] = idx
```
**Detects:**
- Identical text content across sections
- Real duplication (not just similar styling)
- Preview of duplicated text for validation

### Step 2.7: Class Pattern Analysis
```python
all_classes = []
for tag in soup.find_all(class_=True):
    all_classes.extend(tag.get('class', []))

class_counts = {}
for cls in all_classes:
    class_counts[cls] = class_counts.get(cls, 0) + 1

suspicious_duplication = []
for cls, count in class_counts.items():
    if count > 10 and any(term in cls.lower() for term in ['article', 'post', 'entry']):
        suspicious_duplication.append({
            'class_name': cls,
            'occurrence_count': count,
            'note': 'High repetition - check if content is identical'
        })
```
**Identifies:**
- High-frequency semantic classes (>10 occurrences)
- Article/post/entry patterns
- Excludes utility classes (btn, text-center, etc.)

**Output:** Actual class names (not just counts) for VLM analysis

### Step 2.8: DOM Depth Calculation
```python
def get_max_depth(element, depth=0):
    if not element or not hasattr(element, 'children'):
        return depth
    children_with_names = [child for child in element.children if hasattr(child, 'name') and child.name]
    if not children_with_names:
        return depth
    return max(get_max_depth(child, depth + 1) for child in children_with_names)

max_depth = get_max_depth(soup.body) if soup.body else 0
```
**Measures:**
- Maximum nesting level of DOM elements
- Indicates page complexity
- Helps identify over-engineered structures

### Step 2.9: Footer CTA Detection
```python
footer = soup.find('footer') or soup.find(class_=lambda x: x and 'footer' in str(x).lower())
has_footer_cta = False
if footer:
    footer_text = footer.get_text(strip=True).lower()
    has_footer_cta = any(term in footer_text for term in ['subscribe', 'sign up', 'newsletter'])
```
**Identifies:**
- Marketing pattern: footer CTAs
- Helps distinguish intentional duplication (hero + footer CTA) from bugs

### Step 2.10: Framework Detection
```python
script_tags = soup.find_all('script')
framework_indicators = {
    'react': any('react' in str(script.get('src', '')).lower() for script in script_tags),
    'vue': any('vue' in str(script.get('src', '')).lower() for script in script_tags),
    'angular': any('angular' in str(script.get('src', '')).lower() for script in script_tags),
    'next': any('next' in str(script.get('src', '')).lower() or '_next' in html_content for script in script_tags),
}
is_spa = any(framework_indicators.values())
```
**Detects:**
- React, Vue, Angular, Next.js frameworks
- SPA indicators
- JavaScript rendering requirements

**Returns:** Framework names (not boolean flags) for VLM context

### Step 2.11: Loading Indicator Detection
```python
loading_indicators = soup.find_all(class_=lambda x: x and any(
    term in str(x).lower() for term in ['loading', 'spinner', 'skeleton', 'placeholder']
))
```
**Identifies:**
- Loading spinners
- Skeleton screens
- Placeholder content
- Signals: page may not be fully loaded

### Step 2.12: Lazy Loading Detection
```python
lazy_images = soup.find_all('img', attrs={'loading': 'lazy'}) or \
             soup.find_all(attrs={'data-src': True})
```
**Detects:**
- Lazy-loaded images
- Images not loaded until scrolled into view
- Deferred content loading patterns

### Step 2.13: Infinite Scroll Detection
```python
has_infinite_scroll = bool(soup.find_all(class_=lambda x: x and any(
    term in str(x).lower() for term in ['infinite', 'load-more', 'pagination']
)))
```
**Identifies:**
- Infinite scroll implementations
- Load-more buttons
- Pagination indicators

### Step 2.14: Script Complexity Analysis
```python
inline_scripts = [s for s in script_tags if not s.get('src')]
total_script_size = sum(len(s.string or '') for s in inline_scripts)
has_heavy_js = total_script_size > 10000 or len(script_tags) > 10
```
**Measures:**
- Inline script size
- Total script count
- Complexity level (high/normal)

### Step 2.15: AJAX Pattern Detection
```python
has_ajax_patterns = 'fetch(' in html_content or 'XMLHttpRequest' in html_content or \
                   'axios' in html_content or '$.ajax' in html_content
```
**Detects:**
- AJAX/fetch API usage
- Dynamic content loading
- Asynchronous data retrieval

### Step 2.16: HTML Analysis Output
```python
return {
    'total_elements': len(soup.find_all()),
    'main_sections_count': len(main_sections),
    'modal_elements_count': len(modals),
    'dom_depth': max_depth,
    'text_content_duplicates': text_duplicates,
    'suspicious_class_patterns': suspicious_duplication[:3],
    'has_cookie_consent': 'cookie' in html_content.lower(),
    'has_footer_cta': has_footer_cta,
    'modal_element_ids': [m.get('id', 'no-id') for m in modals[:3]],
    'capture_analysis': {
        'is_spa': is_spa,
        'frameworks_detected': [k for k, v in framework_indicators.items() if v],
        'loading_indicators_count': len(loading_indicators),
        'lazy_images_count': len(lazy_images),
        'has_infinite_scroll': has_infinite_scroll,
        'empty_containers': empty_containers_count,
        'script_complexity': 'high' if has_heavy_js else 'normal',
        'has_ajax_patterns': has_ajax_patterns,
        'modals_count': len(modals)
    }
}
```

**Complete structure includes:**
- Element counts and metrics
- Actual class names (not just counts)
- Framework names (React, Vue, etc.)
- Modal IDs for selectors
- Text content snippets
- Capture analysis object with detailed metrics

---

## Phase 3: GPT-4o Vision Analysis

### Step 3.1: Screenshot Encoding
```python
with open(screenshot_path, 'rb') as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')
```
- Loads PNG screenshot
- Encodes as base64 for API transmission
- Preserves image quality

### Step 3.2: Prompt Construction

The system builds a comprehensive prompt that:

1. **Provides HTML validation context**
   - If HTML has <100 elements, flags potential SPA skeleton
   - Warns about JavaScript rendering requirements

2. **Defines detection rules** (for VLM guidance)
   - Partial page loads / incomplete rendering
   - Overlays blocking content
   - Marketing page patterns (hero + footer CTAs = normal)
   - Blog article lists (multiple similar cards = normal)
   - Real duplication (entire sections repeating identically)

3. **Provides HTML analysis data**
   - Complete structure object
   - Framework names
   - Class patterns with actual names
   - Modal IDs
   - Text content duplicates

4. **Requests intelligent analysis**
```
**YOUR TASK - INTELLIGENT ANALYSIS:**
You have access to:
1. The VISUAL screenshot - what the page actually looks like
2. The HTML STRUCTURE - element counts, frameworks, class patterns, text content
3. The HTML FILE metadata - total elements, DOM depth, script complexity

Use ALL of this information together to make intelligent decisions:
- Look at what the screenshot SHOWS visually
- Cross-reference with HTML structure (e.g., "HTML has 48 elements but screenshot is blank")
- Identify the ROOT CAUSE (e.g., "Low element count + blank visual = SPA captured too early")
- Determine the BEST capture strategy for THIS specific page

Do NOT just count things and apply rules. UNDERSTAND what's happening:
- WHY does this page look this way?
- WHAT does the HTML tell us about loading behavior?
- HOW should we capture THIS specific page?

Think like an engineer debugging a capture issue, not a pattern matcher.
```

5. **Defines output format**
```json
{
    "status": "CORRECT" or "BROKEN",
    "issue_type": "partial_load | js_render_failure | ...",
    "severity": "critical | major | minor | none",
    "confidence": 0.0-1.0,
    "diagnosis": "Clear explanation...",
    "capture_recommendations": {
        "primary_issue": "What is the main capture problem?",
        "wait_strategy": "time-based/selector-based/network-idle/hybrid - explain why",
        "wait_duration": "How long based on page characteristics",
        "selectors_to_wait_for": ["Realistic selectors based on HTML"],
        "scroll_needed": true/false,
        "modal_handling": "Best approach for modals",
        "technical_implementation": "Complete working code snippet"
    }
}
```

Note: capture_recommendations is generated by VLM analysis

### Step 3.3: API Call
```python
response = requests.post(
    'https://api.openai.com/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'gpt-4o',
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:image/png;base64,{base64_image}',
                        'detail': 'high'
                    }
                }
            ]
        }],
        # NO max_tokens limit - unlimited analysis
        'temperature': 0.1
    },
    timeout=180
)
```

**Parameters:**
- **Model:** `gpt-4o` (latest vision model)
- **Temperature:** 0.1 (low randomness, consistent analysis)
- **Detail:** `high` (high-resolution image analysis)
- **Max tokens:** Unlimited (no cap on response length)
- **Timeout:** 180 seconds

### Step 3.4: Retry Logic
```python
max_retries = 3
for attempt in range(max_retries):
    try:
        # API call
        if response.status_code != 200:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
    except requests.exceptions.Timeout:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
            continue
```

**Retry strategy:**
- 3 attempts maximum
- Exponential backoff (2^attempt seconds)
- Handles timeouts and API errors gracefully

### Step 3.5: JSON Parsing with Repair
```python
content = data['choices'][0]['message']['content']

# Extract JSON from markdown code blocks
if '```json' in content:
    content = content.split('```json')[1].split('```')[0].strip()
elif '```' in content:
    content = content.split('```')[1].split('```')[0].strip()

# Try to parse
try:
    result = json.loads(content)
except json.JSONDecodeError as e:
    # Repair: Replace unescaped newlines within strings
    import re
    content_fixed = re.sub(r'("(?:[^"\\]|\\.)*")', 
                          lambda m: m.group(0).replace('\n', '\\n'), 
                          content)
    result = json.loads(content_fixed)
```

**Handles:**
- Markdown code blocks (```json)
- Unescaped newlines in strings
- Malformed JSON responses

### Step 3.6: Token & Cost Calculation
```python
usage = data.get('usage', {})
tokens_in = usage.get('prompt_tokens', 0)
tokens_out = usage.get('completion_tokens', 0)
total_tokens = tokens_in + tokens_out

# GPT-4o pricing
cost = (tokens_in * 2.50 + tokens_out * 10.00) / 1_000_000
```

**Pricing (GPT-4o):**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- Average cost per screenshot: $0.008-0.011

---

## Phase 4: Output Generation

### Step 4.1: Console Output
```python
print(f"\n[OK] Analysis Complete:")
print(f"   Status: {result['status']}")
print(f"   Issue Type: {result['issue_type']}")
print(f"   Severity: {result['severity']}")
print(f"   Confidence: {result['confidence']:.0%}")
print(f"\n[DIAGNOSIS] {result['diagnosis']}")
```

**Displays:**
- Analysis status (CORRECT/BROKEN/ERROR)
- Issue type classification
- Severity level
- Confidence percentage
- Full diagnosis text

### Step 4.2: Capture Recommendations Display
```python
if result.get('capture_recommendations'):
    print(f"\n[CAPTURE RECOMMENDATIONS] VLM Analysis:")
    capture_recs = result['capture_recommendations']
    print(f"\n   Primary Issue: {capture_recs.get('primary_issue')}")
    print(f"   Wait Strategy: {capture_recs.get('wait_strategy')}")
    print(f"   Wait Duration: {capture_recs.get('wait_duration')}")
    if capture_recs.get('selectors_to_wait_for'):
        print(f"   Selectors: {', '.join(capture_recs['selectors_to_wait_for'][:3])}")
    print(f"   Scroll Needed: {capture_recs.get('scroll_needed')}")
```

**Shows top 3 selectors and key recommendations**

### Step 4.3: JSON File Creation
```python
case_result = {
    'case_name': case_name,
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'analysis': {
        'status': result['status'],
        'issue_type': result['issue_type'],
        'diagnosis': result['diagnosis'],  # Full text
        'capture_improvement': result.get('capture_improvement')  # Full text
        # ... all fields
    },
    'html_structure_analysis': html_analysis,  # Complete HTML data
    'capture_recommendations': result.get('capture_recommendations', {}),
    'metrics': {
        'tokens_input': tokens_in,
        'tokens_output': tokens_out,
        'cost_usd': cost,
        'processing_time_seconds': processing_time
    }
}

json_path = RESULTS_DIR / f"{case_name}.json"
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(case_result, f, indent=2, ensure_ascii=False)
```

**Individual JSON includes:**
- Complete analysis
- Full HTML structure data
- VLM-generated capture recommendations
- Token metrics and cost

### Step 4.4: CSV Summary Generation
```python
# Format capture recommendations for CSV
capture_rec_text = ""
if result.get('capture_recommendations'):
    recs = result['capture_recommendations']
    capture_rec_text = f"""Primary Issue: {recs.get('primary_issue', 'N/A')}
Wait Strategy: {recs.get('wait_strategy', 'N/A')}
Wait Duration: {recs.get('wait_duration', 'N/A')}
Selectors: {', '.join(recs.get('selectors_to_wait_for', [])) if recs.get('selectors_to_wait_for') else 'None'}
Scroll Needed: {recs.get('scroll_needed', False)}
Modal Handling: {recs.get('modal_handling', 'N/A')}
Technical Implementation: {recs.get('technical_implementation', 'N/A')}"""

return {
    'case': case_name,
    'status': result['status'],
    'diagnosis': result['diagnosis'],  # FULL text, no truncation
    'capture_improvement': result.get('capture_improvement', 'N/A'),  # FULL text
    'capture_recommendations_details': capture_rec_text,  # Formatted
    # ... other fields
}
```

**CSV contains:**
- All analysis fields
- Full text (no truncation)
- Formatted capture recommendations
- Token metrics and cost

### Step 4.5: Final Statistics
```python
print("\n📊 DIAGNOSIS SUMMARY")
print(f"   Total Analyzed: {total_cases}")
print(f"   Correct Pages: {len(correct_cases)}")
print(f"   Broken Pages: {len(broken_cases)}")

print("\n🔍 Issue Types Detected:")
for issue_type, count in sorted(issue_counts.items()):
    print(f"   {issue_type}: {count}")

print("\n💰 Token Usage & Cost Analysis:")
print(f"   Total Tokens: {total_tokens:,}")
print(f"   Total Cost: ${total_cost:.4f}")
print(f"   Average Cost/Case: ${avg_cost:.4f}")
```

**Summary includes:**
- Result counts (correct/broken/errors)
- Issue type breakdown
- Token usage statistics
- Cost analysis
- Performance metrics

---

## Data Flow Example

### Input Files
```
data/screenshots/maven.png
data/html/maven.html
```

### HTML Analysis Output
```json
{
  "total_elements": 48,
  "main_sections_count": 3,
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
    "has_ajax_patterns": true
  }
}
```

### VLM Analysis
- Receives screenshot + complete HTML structure
- Analyzes: "48 elements + React + blank screenshot"
- Concludes: "SPA captured before hydration"
- Generates recommendations:
  - Primary issue: Early capture before JS execution
  - Wait strategy: network-idle + selector-based
  - Wait duration: 3-5 seconds
  - Selectors: [".main-content", ".article-card"]
  - Technical implementation: Complete Playwright code

### Output Files

**JSON (`diagnosis_results/maven.json`):**
```json
{
  "case_name": "maven",
  "timestamp": "2025-11-25 14:32:10",
  "analysis": {
    "status": "BROKEN",
    "issue_type": "partial_load",
    "diagnosis": "Full detailed explanation...",
    "capture_improvement": "Complete VLM recommendation..."
  },
  "html_structure_analysis": { /* complete HTML data */ },
  "capture_recommendations": {
    "primary_issue": "SPA captured before hydration",
    "wait_strategy": "network-idle + selector-based",
    "technical_implementation": "await page.waitForLoadState('networkidle')..."
  },
  "metrics": {
    "tokens_input": 2234,
    "tokens_output": 274,
    "cost_usd": 0.0083,
    "processing_time_seconds": 20.1
  }
}
```

**CSV (`diagnosis_results/diagnosis_summary.csv`):**
```csv
case,status,issue_type,diagnosis,capture_recommendations_details,tokens_in,cost
maven,BROKEN,partial_load,"Full diagnosis...","Primary Issue: SPA captured before hydration\nWait Strategy: network-idle + selector-based\n...",2234,0.0083
```

---

## Performance Metrics

### Per-Case Averages
- **Processing time:** 10-48 seconds
- **Input tokens:** 2,000-3,000
- **Output tokens:** 250-370
- **Cost:** $0.008-0.011

### Batch Performance (8 cases)
- **Total time:** 160.7 seconds (~2.7 minutes)
- **Total tokens:** 20,067
- **Total cost:** $0.0666

### Scalability
- **100 cases:** ~33.5 minutes, ~$0.83
- **1,000 cases:** ~5.6 hours, ~$8.30
- **10,000 cases:** ~55.8 hours, ~$83.00

---

## Key Design Principles

### 1. AI-Driven Analysis
- VLM receives complete HTML structure (class names, IDs, framework names)
- Intelligently correlates visual evidence with HTML data
- Generates context-aware recommendations

### 2. Complete Data, Not Just Counts
- Sends actual class names, not just counts
- Framework names (React, Vue, Angular)
- Modal element IDs
- Text content snippets

### 3. HTML as Context
- HTML shows what should be on page
- Screenshot shows what actually rendered
- VLM correlates discrepancies

### 4. Flexible & Adaptive
- VLM adapts to novel patterns
- Works with new frameworks without code updates
- Handles diverse page types (SPAs, static, hybrid)

### 5. Comprehensive Output
- Individual JSON per case (complete analysis)
- CSV summary (all fields, no truncation)
- Console logs (real-time progress)

---

## Error Handling

### API Errors
- 3 retry attempts with exponential backoff
- Timeout handling (180s limit)
- Graceful degradation to ERROR status

### JSON Parsing
- Automatic repair of common issues
- Unescaped newline handling
- Fallback error messages

### File Locking
- Alternative filename with timestamp if CSV locked
- Permission error handling
- User notification

---

## Usage

### Basic Execution
```bash
python web_diagnosis.py
```

### Expected Output
1. Real-time progress per case
2. Diagnosis + capture recommendations
3. Token metrics and cost
4. Final summary statistics

### Output Files
- `diagnosis_results/*.json` - Individual detailed reports
- `diagnosis_results/diagnosis_summary.csv` - Aggregate table

---

## Conclusion

This system provides:
- **AI-driven diagnosis** using GPT-4o Vision
- **Complete HTML structure** analysis (not just counts)
- **Intelligent capture recommendations** from VLM
- **Comprehensive output** (JSON + CSV)
- **Production-ready** error handling and retry logic
- **Cost-effective** with detailed metrics tracking

The workflow ensures accurate detection of rendering issues while providing actionable recommendations for improving screenshot capture quality.
