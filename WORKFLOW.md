# Technical Workflow Documentation

**Complete step-by-step breakdown of the Screenshot Diagnosis Pipeline**

This document explains every decision, every step, and every algorithm in the pipeline. Perfect for understanding how the system works internally.

---

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [Stage 1: Computer Vision Analysis](#stage-1-computer-vision-analysis)
3. [Stage 2: LLM Semantic Analysis](#stage-2-llm-semantic-analysis)
4. [Decision Logic](#decision-logic)
5. [Output Generation](#output-generation)
6. [Algorithm Details](#algorithm-details)

---

## Pipeline Overview

### High-Level Flow

```
START
  ↓
┌─────────────────────────────────────┐
│ 1. Load Input Files                 │
│    - Read screenshot (PNG)           │
│    - Read HTML source                │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. Stage 1: CV Analysis             │
│    Decision: Is there a visual       │
│    problem we can detect quickly?    │
└─────────────────────────────────────┘
  ↓
  ├─ PASS → Continue to Stage 2
  └─ BROKEN → Skip to Stage 2 with finding
      ↓
┌─────────────────────────────────────┐
│ 3. Stage 2: LLM Analysis            │
│    Decision: Why is this broken?     │
│    Or: Are there hidden HTML issues? │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. Generate Reports                  │
│    - JSON (per case)                 │
│    - CSV (all cases)                 │
│    - Excel (formatted)               │
└─────────────────────────────────────┘
  ↓
END
```

### Why This Architecture?

**Progressive Escalation Strategy**:
1. **Start cheap (CV)**: Can we detect the issue with $0 cost? (Yes 62% of the time)
2. **Escalate when needed (LLM)**: Use AI only when CV needs interpretation
3. **Never guess**: Always provide evidence-based diagnosis

---

## Stage 1: Computer Vision Analysis

**File**: `stage1_global.py`  
**Function**: `stage1_global_checks(screenshot_path)`  
**Purpose**: Fast, cost-free detection of obvious visual failures

### Step 1.1: Load Screenshot

```python
# Load image using OpenCV
image = cv2.imread(screenshot_path)
# Result: NumPy array, shape (height, width, 3) for RGB
```

**What happens**:
- OpenCV reads PNG file into memory
- Converts to BGR color space (OpenCV default)
- Returns 3D array: [rows, columns, channels]

### Step 1.2: Calculate Basic Metrics

#### 1.2.1 Brightness Analysis

**Purpose**: Detect completely white/black pages

```python
def compute_brightness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    return np.mean(gray)  # Average pixel value (0-255)
```

**Decision Logic**:
- `brightness > 230`: Likely blank white page
- `brightness < 30`: Likely blank black page
- `150-200`: Normal content

**Why it works**: Blank pages have uniform color, so mean pixel value is extreme.

#### 1.2.2 Entropy Calculation

**Purpose**: Measure content complexity (randomness)

```python
def compute_entropy(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))  # Pixel distribution
    hist = hist / hist.sum()  # Normalize to probabilities
    hist = hist[hist > 0]  # Remove zeros
    entropy = -np.sum(hist * np.log2(hist))  # Shannon entropy
    return entropy
```

**What is entropy**:
- **Mathematical Formula**: H = -Σ(p(x) * log₂(p(x)))
- **Interpretation**:
  - `0.0`: All pixels same color (blank page)
  - `1.0-2.0`: Very uniform (gradient, solid colors)
  - `5.0-8.0`: Rich content (text, images, variety)

**Decision Logic**:
- `entropy < 1.5`: **Blank page** (almost no variation)
- `entropy > 5.0`: Normal content

**Example**:
- Blank white page: entropy ≈ 0.0
- Single color gradient: entropy ≈ 1.2
- Blog page with text/images: entropy ≈ 6.5

#### 1.2.3 Edge Detection

**Purpose**: Count visual elements (text, borders, images)

```python
def compute_edge_count(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)  # Canny edge detector
    edge_count = np.count_nonzero(edges)  # Count white pixels
    return edge_count
```

**What is Canny edge detection**:
- Finds sharp changes in brightness (edges)
- Returns binary image: white = edge, black = no edge
- Parameters (100, 200) = threshold for weak/strong edges

**Decision Logic**:
- `edges < 50,000`: **Minimal content** (few visual elements)
- `edges > 500,000`: Rich content

**Example**:
- Blank page: ~0 edges
- Login form: ~80,000 edges
- Full article page: ~800,000 edges

### Step 1.3: Blank Page Detection

**Combining metrics**:

```python
is_blank = (entropy < 1.5 AND edge_count < 50000)
```

**Why both**:
- Entropy alone: Dark themes have low entropy but are NOT blank
- Edges alone: Gradients have few edges but entropy > 0
- **Together**: Catches true blank pages, ignores dark themes

**Result**:
```python
{
  "status": "BROKEN",
  "diagnosis": "Completely blank screenshot",
  "confidence": 0.95
}
```

### Step 1.4: Duplicate Content Detection

**Purpose**: Detect screenshot stitching bugs (same content repeated 2x/3x)

#### Algorithm: SSIM-Based Slice Comparison

**Step 4.1: Slice Screenshot Vertically**

```python
NUM_SLICES = 20  # Divide into 20 horizontal bands

def slice_image_horizontal(image, num_slices):
    height = image.shape[0]
    slice_height = height // num_slices
    slices = []
    for i in range(num_slices):
        start_y = i * slice_height
        end_y = start_y + slice_height
        slice_img = image[start_y:end_y, :, :]
        slices.append(slice_img)
    return slices
```

**What this does**:
- Cut screenshot into 20 equal-height strips
- Each strip = [slice_height px, full_width px, 3 channels]
- Result: 20 image slices we can compare

**Why 20 slices**:
- Too few (5): Miss partial duplications
- Too many (50): Noise from small variations
- 20: Good balance for full-page screenshots

**Step 4.2: Calculate SSIM Between Slices**

**What is SSIM (Structural Similarity Index)**:
- Measures how similar two images are (0.0 = different, 1.0 = identical)
- Considers: luminance, contrast, structure
- Better than pixel-by-pixel comparison (handles slight variations)

```python
from skimage.metrics import structural_similarity as ssim

def compute_slice_ssim(slice1, slice2):
    # Convert to grayscale
    gray1 = cv2.cvtColor(slice1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(slice2, cv2.COLOR_BGR2GRAY)
    
    # Calculate SSIM (returns value 0.0-1.0)
    similarity = ssim(gray1, gray2, data_range=255)
    return similarity
```

**Interpreting SSIM**:
- `ssim = 1.0`: Identical slices
- `ssim > 0.85`: Very similar (likely duplicate)
- `ssim = 0.7-0.85`: Similar but different content
- `ssim < 0.5`: Completely different

**Step 4.3: Detect Repetition Patterns**

**Method 1: Equal Partition Check (for 2x/3x full duplicates)**

```python
def detect_equal_partition_repetition(slices):
    n = len(slices)  # 20 slices
    
    # Check if page repeated 3x (20 slices = 3 blocks of 6-7)
    for k in [3, 2]:  # Try 3x first, then 2x
        if n % k != 0:
            continue
        block_size = n // k  # Size of one repetition
        
        # Compare first block to other blocks
        matches = 0
        for rep in range(1, k):
            for i in range(block_size):
                s1 = slices[i]
                s2 = slices[rep * block_size + i]
                sim = compute_slice_ssim(s1, s2)
                if sim > 0.75:  # 75% similarity threshold
                    matches += 1
            
            # Need 75% of slices to match
            if (matches / block_size) >= 0.75:
                return {"found": True, "repetitions": k}
    
    return {"found": False}
```

**How this detects duplicates**:
1. **Hypothesis**: If page repeated 3x, slices 0-6 = slices 7-13 = slices 14-20
2. **Test**: Compare slice 0 to slice 7, slice 1 to slice 8, etc.
3. **Verdict**: If 75%+ slices match with SSIM > 0.75 → **3x duplication detected**

**Example**:
```
Slices 0-6:   [header, hero, article1, article2, footer]
Slices 7-13:  [header, hero, article1, article2, footer]  ← Same content!
Slices 14-20: [header, hero, article1, article2, footer]  ← Same content!

Result: 3x vertical duplication detected
```

**Result**:
```python
{
  "status": "BROKEN",
  "diagnosis": "Page repeated 3x vertical",
  "confidence": 0.54,  # SSIM score
  "suggested_fix": "TOOL: Fix stitching algorithm - validate no duplicate DOM IDs"
}
```

### Step 1.5: Cookie Modal Detection

**Purpose**: Detect overlays/modals blocking content

```python
def detect_cookie_modal(image):
    height, width = image.shape[:2]
    
    # Check top-right region (where modals often appear)
    top_third = height // 3
    right_half = width // 2
    region = image[0:top_third, right_half:width]
    
    # Calculate region metrics
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    dark_pixels = np.sum(gray < 128) / gray.size  # % of dark pixels
    std = np.std(gray)  # Variation in brightness
    
    # Modal detection logic
    is_modal = (0.05 < dark_pixels < 0.15) AND (std > 35)
    
    return is_modal
```

**How this works**:
- **Hypothesis**: Cookie modals create dark semi-transparent overlays
- **Region of interest**: Top-right (common modal location)
- **Signature**: 5-15% dark pixels + moderate variation (not uniform)

**Why this threshold**:
- `<5% dark`: Normal white background
- `5-15% dark`: Semi-transparent overlay
- `>15% dark`: Image content (not modal)
- `std > 35`: Has contrast (text/buttons), not just solid color

**Result**:
```python
{
  "status": "BROKEN",
  "diagnosis": "Cookie consent modal blocking content",
  "confidence": 0.90
}
```

### Stage 1 Final Decision

```python
def stage1_global_checks(screenshot_path):
    image = load_image(screenshot_path)
    
    # Run all checks
    is_blank = check_blank_page(image)
    is_duplicate = check_duplicate_stitching(image)
    has_modal = detect_cookie_modal(image)
    
    # Decision tree
    if is_blank:
        return {"status": "BROKEN", "diagnosis": "Blank screenshot"}
    elif is_duplicate:
        return {"status": "BROKEN", "diagnosis": "Page repeated 2x/3x"}
    elif has_modal:
        return {"status": "BROKEN", "diagnosis": "Cookie modal blocking"}
    else:
        return {"status": "PASS", "diagnosis": "No CV issues detected"}
```

---

## Stage 2: LLM Semantic Analysis

**File**: `llm_analyzer.py`  
**Function**: `diagnose_with_llm(html_path, screenshot_path, cv_finding)`  
**Purpose**: Understand WHY the issue occurred using AI

### When is Stage 2 called?

**Scenario A**: Stage 1 found issue (blank, duplicate, modal)
- **Goal**: Explain the root cause semantically
- **Input**: CV finding + HTML
- **Output**: "Cookie consent modal (CookieHub script)" instead of just "modal detected"

**Scenario B**: Stage 1 found no issues
- **Goal**: Check for hidden HTML problems (missing CSS, security challenges)
- **Input**: Clean screenshot + HTML
- **Output**: "CORRECT" or "Missing stylesheet detected"

### Step 2.1: Extract HTML Summary

**Why not send full HTML to LLM**:
- Full HTML = 50,000+ characters
- LLM token limit = ~8,000 tokens
- Solution: Compress to essential signals only

```python
def extract_html_summary(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 1. Remove noise (scripts, styles)
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    # 2. Get visible text (first 1000 chars)
    visible_text = soup.get_text(separator=' ', strip=True)
    text_preview = visible_text[:1000]
    
    # 3. List external scripts (blocking indicators)
    scripts = []
    for script in soup.find_all('script', src=True):
        src = script.get('src')
        if src and not src.startswith('data:'):
            scripts.append(src)
    
    # 4. List CSS resources
    css_links = []
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            css_links.append(href)
    
    # 5. Detect blocking keywords
    html_lower = html_content.lower()
    keywords = ['cookie', 'consent', 'cloudflare', 'captcha', 'login', 'security']
    found_keywords = [kw for kw in keywords if kw in html_lower]
    
    return {
        "visible_text": text_preview,
        "scripts": scripts[:10],  # First 10 only
        "css_links": len(css_links),
        "blocking_keywords": found_keywords
    }
```

**What this gives us**:
- **Text preview**: Can detect "challenge", "verify you're human", "login required"
- **Scripts**: Can detect "cookiehub.eu", "recaptcha.net", "cloudflare.com"
- **CSS count**: Can detect if stylesheets are missing (0 = problem)
- **Keywords**: Quick scan for common blockers

### Step 2.2: Build LLM Prompt

**Prompt engineering**: Tell LLM exactly what to look for

```python
prompt = f"""Webpage Diagnosis - Universal Analysis

URL: {page_url}

CV FINDING: {cv_finding or "No CV issues - page loaded successfully"}

HTML Summary:
- Visible text: "{visible_text[:300]}..."
- External scripts: {len(scripts)} total
- CSS stylesheets: {len(css_links)} total
- Blocking keywords: {found_keywords}

Scripts to check:
{json.dumps(scripts[:10], indent=2)}

CONTEXT:
- Screenshot tool captures AFTER page loads (not during load)
- Cookie scripts are normal unless they show a MODAL
- Only detect issues if there's EVIDENCE of actual blocking

Your task: Analyze if the CV finding indicates a real BLOCKING ISSUE.

DETECTION RULES:
1. DUPLICATE: Only if CV found "repeated" AND HTML has real duplication
2. SECURITY CHALLENGE: Visible text contains "verify", "challenge", "captcha"
3. AUTH WALL: Visible text contains "login", "sign in", "restricted"
4. MISSING RESOURCES: CV found "blank" AND CSS links broken
5. COOKIE MODAL: CV detected "modal" AND cookie scripts present

DO NOT report cookie scripts as blocking unless CV detected a modal!

RESPOND WITH JSON ONLY:
{{"issue_detected":true,"issue_type":"security_challenge","confidence":0.9,"diagnosis":"Cloudflare challenge blocking page","evidence":"challenge text detected","tool_fix":"TOOL: Add captcha solver"}}

If no issue:
{{"issue_detected":false,"diagnosis":"Page structure appears normal","confidence":0.95}}
"""
```

**Key elements**:
1. **Context**: Tell LLM what we already know (CV finding)
2. **Rules**: Explicit detection criteria (not "figure it out")
3. **Constraints**: "Only if X AND Y" prevents false positives
4. **Format**: JSON-only response (easy to parse)

### Step 2.3: Call Groq LLM API

```python
def call_groq_llm(prompt):
    api_key = os.getenv('GROQ_API_KEY')
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "llama-3.3-70b-versatile",  # Free, fast, accurate
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,  # Low = consistent answers
        "max_tokens": 1024
    }
    
    response = requests.post(url, headers={...}, json=payload)
    result = response.json()
    return result['choices'][0]['message']['content']
```

**Why Groq**:
- **Free**: No cost for moderate usage
- **Fast**: 3 seconds per call (GPU-accelerated)
- **Model**: Llama 3.3 70B (open-source, high quality)

### Step 2.4: Parse LLM Response

```python
def parse_llm_response(response_text):
    # LLM sometimes wraps JSON in markdown
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    
    # Extract JSON
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    json_str = response_text[json_start:json_end]
    
    parsed = json.loads(json_str)
    return {
        "issue_detected": parsed.get("issue_detected", False),
        "diagnosis": parsed.get("diagnosis", "Unknown"),
        "confidence": parsed.get("confidence", 0.5),
        "tool_fix": parsed.get("tool_fix", "No action")
    }
```

**Example LLM output**:
```json
{
  "issue_detected": true,
  "issue_type": "cookie_modal_blocking",
  "diagnosis": "Cookie consent modal blocking content",
  "confidence": 0.90,
  "evidence": "CookieHub script (cookiehub.eu) detected, CV confirmed overlay",
  "tool_fix": "TOOL: Detect and dismiss overlays/modals before capture"
}
```

### Stage 2 Decision Logic

```python
def diagnose_with_llm(html_path, screenshot_path, cv_finding):
    # Read HTML
    html_content = read_file(html_path)
    
    # Summarize HTML
    summary = extract_html_summary(html_content)
    
    # Build prompt with CV finding + HTML summary
    prompt = build_prompt(cv_finding, summary)
    
    # Call LLM
    llm_response = call_groq_llm(prompt)
    parsed = parse_llm_response(llm_response)
    
    # Decision
    if parsed["issue_detected"]:
        return {
            "status": "BROKEN",
            "diagnosis": parsed["diagnosis"],
            "confidence": parsed["confidence"],
            "suggested_fix": parsed["tool_fix"]
        }
    else:
        # If Stage 1 said BROKEN but LLM says no issue, trust CV
        if cv_finding:
            return {
                "status": "BROKEN",
                "diagnosis": cv_finding,  # Use CV finding
                "confidence": 0.95
            }
        else:
            return {
                "status": "CORRECT",
                "diagnosis": "Page appears normal",
                "confidence": 0.95
            }
```

---

## Decision Logic

### Overall Pipeline Decision Tree

```
┌─────────────────────────┐
│ Stage 1: CV Analysis    │
└─────────────────────────┘
          │
    ┌─────┴─────┐
    │           │
  BROKEN      PASS
    │           │
    ↓           ↓
┌───────┐   ┌──────────┐
│ LLM:  │   │  LLM:    │
│ Why?  │   │  Hidden  │
│       │   │  issues? │
└───┬───┘   └────┬─────┘
    │            │
    ├─ Issue    ├─ Issue found
    │  found    │  └→ BROKEN
    │  └→ Use   │
    │     LLM   ├─ No issue
    │     diag  │  └→ CORRECT
    │            
    ├─ No issue
    │  └→ Use CV finding
    │
    ↓
  FINAL STATUS
```

### Confidence Scoring

**High Confidence (0.90-0.95)**:
- CV + LLM agree
- Clear evidence (blank page, SSIM > 0.85, security keywords)

**Medium Confidence (0.70-0.85)**:
- CV detected issue, LLM provides context
- SSIM 0.65-0.75 (borderline duplicate)

**Low Confidence (0.50-0.65)**:
- Ambiguous signals
- LLM uncertain (hedge words in diagnosis)

---

## Output Generation

### JSON Report (per case)

```python
def save_json_report(case_name, result):
    output = {
        "case_name": case_name,
        "status": result["status"],  # "broken" or "correct"
        "root_cause": result["diagnosis"],
        "diagnosis": result["diagnosis"],
        "suggested_fix": result["suggested_fix"],
        "confidence": result["confidence"],
        "evidence": result.get("evidence", "")  # NEW: Added evidence
    }
    
    with open(f"results/{case_name}.json", "w") as f:
        json.dump(output, f, indent=2)
```

### CSV Report (all cases)

```python
def create_csv_report(all_results):
    with open("diagnosis_report.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Case", "Status", "Root Cause", "Diagnosis", "Fix", "Confidence", "Evidence"])
        
        for result in all_results:
            writer.writerow([
                result["case_name"],
                "BROKEN" if result["status"] == "broken" else "CORRECT",
                result["root_cause"],
                result["diagnosis"],
                result["suggested_fix"],
                f"{result['confidence']:.2f}",
                result.get("evidence", "")
            ])
```

### Excel Report

```python
def create_excel_report(all_results):
    wb = Workbook()
    ws = wb.active
    
    # Headers
    ws['A1'] = "Case Name"
    ws['B1'] = "Status"
    ws['C1'] = "Root Cause"
    ws['D1'] = "Diagnosis"
    ws['E1'] = "Suggested Fix"
    ws['F1'] = "Evidence"  # NEW column
    
    # Data rows
    for idx, result in enumerate(all_results, start=2):
        ws[f'A{idx}'] = result["case_name"]
        ws[f'B{idx}'] = "BROKEN" if result["status"] == "broken" else "CORRECT"
        ws[f'C{idx}'] = result["root_cause"]
        ws[f'D{idx}'] = result["diagnosis"]
        ws[f'E{idx}'] = result["suggested_fix"]
        ws[f'F{idx}'] = result.get("evidence", "")
    
    wb.save("diagnosis_report.xlsx")
```

---

## Algorithm Details

### SSIM (Structural Similarity Index)

**Formula**:
```
SSIM(x, y) = [l(x,y)^α * c(x,y)^β * s(x,y)^γ]

Where:
- l(x,y) = luminance similarity
- c(x,y) = contrast similarity  
- s(x,y) = structure similarity
- α, β, γ = weights (usually 1)
```

**Why better than pixel comparison**:
- Pixel diff: Sensitive to small shifts/lighting changes
- SSIM: Captures perceptual similarity (how humans see images)

### Shannon Entropy

**Formula**:
```
H(X) = -Σ p(x_i) * log₂(p(x_i))

Where:
- p(x_i) = probability of pixel value i
- Σ = sum over all 256 possible values (0-255)
```

**Interpretation**:
- Blank page (all pixels = 255): p(255) = 1.0, H = 0
- Two colors (50/50): H = 1.0
- Uniform distribution (all values equal): H = 8.0 (maximum)

### Canny Edge Detection

**Steps**:
1. **Gaussian blur**: Remove noise
2. **Gradient calculation**: Find brightness changes (Sobel operator)
3. **Non-maximum suppression**: Thin edges to 1-pixel width
4. **Hysteresis thresholding**: Keep strong edges (>200), discard weak (<100)

**Result**: Binary image where white = edge, black = no edge

---

## Performance Optimization

### Caching

```python
# LLM responses are deterministic (low temperature)
# Cache HTML summaries to avoid re-processing
cache = {}
html_hash = hashlib.md5(html_content.encode()).hexdigest()
if html_hash in cache:
    return cache[html_hash]
```

### Parallelization (Future Enhancement)

```python
# Process multiple cases in parallel
from multiprocessing import Pool

def process_case(case):
    return diagnose_screenshot(case)

with Pool(processes=4) as pool:
    results = pool.map(process_case, all_cases)
```

---

## Failure Modes & Debugging

### Common Issues

**1. LLM over-detects cookie modals**:
- **Symptom**: Everything flagged as "cookie modal"
- **Root cause**: Prompt not restrictive enough
- **Fix**: Add rule "Only if CV detected modal AND cookie script present"

**2. False negatives on blank pages**:
- **Symptom**: Dark themes flagged as blank
- **Root cause**: Entropy threshold too high
- **Fix**: Combine entropy + edge count (AND condition)

**3. SSIM false positives**:
- **Symptom**: Normal pages flagged as duplicates
- **Root cause**: Threshold too low (0.5 = very similar)
- **Fix**: Increase threshold to 0.75 or check HTML for confirmation

---

## Extension Guide

### Adding New CV Check

```python
# 1. Add detection function
def detect_lazy_load_placeholders(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_regions = np.sum((gray > 100) & (gray < 150)) / gray.size
    return gray_regions > 0.3  # >30% gray = placeholders

# 2. Add to stage1_global_checks
def stage1_global_checks(screenshot_path):
    # ... existing checks ...
    has_placeholders = detect_lazy_load_placeholders(image)
    
    if has_placeholders:
        return {
            "status": "BROKEN",
            "diagnosis": "Lazy-load placeholders not rendered",
            "confidence": 0.85
        }
```

### Adding New LLM Detection

```python
# Update prompt in llm_analyzer.py
prompt += """
6. LAZY LOAD: CV found "placeholders" AND <img loading="lazy"> in HTML
"""

# Update parsing logic
if "lazy" in parsed["issue_type"]:
    suggested_fix = "TOOL: Scroll through page to trigger lazy-load"
```

---

**End of Technical Workflow Documentation**

For user-facing documentation, see [README.md](README.md)
