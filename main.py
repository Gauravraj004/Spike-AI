"""
LLM-POWERED SCREENSHOT DIAGNOSIS PIPELINE
Intelligent semantic understanding using free Groq API

Stage 1: Quick CV checks (blank, duplicate) - 0.5s, catches obvious issues
Stage 2: LLM analyzes HTML to understand expected components - 2s
Stage 3: VLM verifies screenshot matches expectations - 3s
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Import stage functions
import stage1_global as stage1
import llm_analyzer  # LLM-based universal analysis

# Import Excel export
from src.excel_export import create_excel_report

# Define directories
HTML_DIR = Path("data/html")
SCREENSHOTS_DIR = Path("data/screenshots")
RESULTS_DIR = Path("results")


def get_case_files(html_dir: Path, screenshots_dir: Path) -> List[Dict[str, str]]:
    """
    Get all test cases by matching HTML and screenshot files
    """
    cases = []
    
    # Get all screenshot files
    if not screenshots_dir.exists():
        return cases
    
    screenshot_files = list(screenshots_dir.glob("*.png"))
    
    for screenshot_path in screenshot_files:
        case_name = screenshot_path.stem  # filename without extension
        html_path = html_dir / f"{case_name}.html"
        
        cases.append({
            "case_name": case_name,
            "screenshot_path": str(screenshot_path),
            "html_path": str(html_path)
        })
    
    return cases


def diagnose_screenshot(case: Dict[str, str]) -> Dict[str, Any]:
    """
    Main diagnosis pipeline - runs 3 stages sequentially
    Stops early if high confidence reached
    """
    case_name = case['case_name']
    screenshot_path = case['screenshot_path']
    html_path = case['html_path']
    
    result = {
        "case_name": case_name,
        "status": "UNKNOWN",
        "diagnosis": "",
        "confidence": 0.0,
        "suggested_fix": "",
        "stage_results": {}
    }
    
    print(f"\n{'='*60}")
    print(f"Processing: {case_name}")
    print(f"{'='*60}")
    
    # ========== STAGE 1: CV CHECKS (Blank, Duplicate) ==========
    print("Stage 1: Quick CV checks (blank, duplicate)...")
    stage1_result = stage1.stage1_global_checks(screenshot_path)
    result['stage_results']['stage1'] = stage1_result
    
    print(f"  Status: {stage1_result['status']}")
    if stage1_result.get('diagnosis'):
        print(f"  Finding: {stage1_result['diagnosis']}")
    
    # If Stage 1 found obvious issue (blank/duplicate), use LLM for semantic understanding
    if stage1_result['status'] == 'BROKEN':
        cv_finding = stage1_result['diagnosis']
        print(f"  > CV detected issue: {cv_finding}")
        print(f"\nStage 2: LLM semantic analysis...")
        print("  (Using Groq API - free tier)")
        
        # LLM analyzes HTML to understand WHY (modals, security, etc.)
        llm_result = llm_analyzer.diagnose_with_llm(html_path, screenshot_path, case_name, cv_finding)
        result['stage_results']['llm_analysis'] = llm_result
        
        # Combine CV finding + LLM diagnosis
        result['status'] = 'broken'
        
        # Use LLM diagnosis if it detected something, otherwise use CV finding
        if llm_result.get('issue_detected'):
            result['diagnosis'] = llm_result.get('diagnosis', cv_finding)
            result['root_cause'] = llm_result.get('diagnosis', cv_finding)
            result['suggested_fix'] = llm_result.get('tool_fix', stage1_result.get('suggested_fix', ''))
            result['evidence'] = llm_result.get('evidence', stage1_result.get('evidence', ''))
        else:
            # LLM didn't find HTML issue, use CV finding as diagnosis
            result['diagnosis'] = cv_finding
            result['root_cause'] = cv_finding
            result['suggested_fix'] = stage1_result.get('suggested_fix', '')
            result['evidence'] = stage1_result.get('evidence', '')
        
        result['confidence'] = llm_result.get('confidence', stage1_result['confidence'])
        
        print(f"  > BROKEN (confidence: {result['confidence']:.2f})")
        return result
    
    # ========== STAGE 2: LLM ANALYSIS (Universal HTML Check) ==========
    # No CV issues found - use LLM to check for blocking issues in HTML
    print("\nStage 2: LLM semantic HTML analysis...")
    print("  (Using Groq API - free tier)")
    
    llm_result = llm_analyzer.diagnose_with_llm(html_path, screenshot_path, case_name)
    result['stage_results']['llm_analysis'] = llm_result
    
    print(f"  Status: {llm_result['status']}")
    if llm_result.get('diagnosis'):
        print(f"  Finding: {llm_result['diagnosis']}")
    
    # Map LLM result to pipeline result
    if llm_result['status'] == 'CORRECT':
        result['status'] = 'correct'
        result['diagnosis'] = llm_result['diagnosis']
        result['root_cause'] = 'none'
        result['confidence'] = llm_result['confidence']
        result['suggested_fix'] = 'No action needed'
        result['evidence'] = 'CV Analysis: All visual metrics passed, LLM Analysis: HTML structure appears normal'
        print(f"  > CORRECT (confidence: {result['confidence']:.2f})")
    elif llm_result['status'] == 'BROKEN':
        result['status'] = 'broken'
        result['diagnosis'] = llm_result['diagnosis']
        result['root_cause'] = llm_result['diagnosis']
        result['confidence'] = llm_result['confidence']
        result['suggested_fix'] = llm_result.get('suggested_fix', 'Check page rendering')
        print(f"  > BROKEN detected (confidence: {result['confidence']:.2f})")
    else:
        # Error case
        result['status'] = 'error'
        result['diagnosis'] = llm_result['diagnosis']
        result['root_cause'] = 'Analysis error'
        result['confidence'] = 0.0
        result['suggested_fix'] = 'Retry analysis'
        result['evidence'] = 'LLM API error or parsing failure'
        print(f"  ⚠ Error: {llm_result['diagnosis']}")
    
    return result


def main():
    """Main execution"""
    print("="*80)
    print("COMPONENT-BASED SCREENSHOT DIAGNOSIS PIPELINE")
    print("="*80)
    print("\nApproach:")
    print("  Stage 1: Global checks (blank, duplicate) - Fast heuristics")
    print("  Stage 2: Component matching - CV analysis")
    print("  Stage 3: VLM verification - Only if needed")
    print("="*80)
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Get all test cases
    cases = get_case_files(HTML_DIR, SCREENSHOTS_DIR)
    
    if not cases:
        print("\n❌ ERROR: No test cases found!")
        print(f"Check directories: {HTML_DIR} and {SCREENSHOTS_DIR}")
        return
    
    print(f"\n\nFound {len(cases)} test cases\n")
    
    # Process each case
    all_results = []
    stage1_caught = 0
    stage2_caught = 0
    stage3_used = 0
    
    start_time = time.time()
    
    for case in cases:
        result = diagnose_screenshot(case)
        all_results.append(result)
        
        # Count which stage caught it
        if 'stage1' in result['stage_results'] and result['stage_results']['stage1']['status'] == 'BROKEN':
            stage1_caught += 1
        elif 'stage2' in result['stage_results'] and result['stage_results']['stage2']['status'] == 'BROKEN':
            stage2_caught += 1
        elif 'stage3' in result['stage_results']:
            stage3_used += 1
        
        # Save individual JSON
        output_path = os.path.join(RESULTS_DIR, f"{result['case_name']}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "case_name": result['case_name'],
                "status": result['status'],
                "root_cause": result.get('root_cause', ''),
                "diagnosis": result['diagnosis'],
                "suggested_fix": result['suggested_fix'],
                "confidence": result['confidence'],
                "evidence": result.get('evidence', '')
            }, f, indent=2)
    
    elapsed = time.time() - start_time
    
    # Generate Excel and CSV reports
    print("\n\n" + "="*80)
    print("Generating reports...")
    
    try:
        from src.excel_export import export_to_excel, create_csv_report
        excel_path = os.path.join(os.path.dirname(RESULTS_DIR), "diagnosis_report.xlsx")
        csv_path = os.path.join(os.path.dirname(RESULTS_DIR), "diagnosis_report.csv")
        
        export_to_excel(all_results, excel_path)
        create_csv_report(all_results, csv_path)
        
        print(f"> Excel report: {excel_path}")
        print(f"> CSV report: {csv_path}")
    except Exception as e:
        print(f"⚠ Report generation error: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"{'Case':<20} {'Status':<10} {'Confidence':<12} {'Issue':<35}")
    print("-"*80)
    
    for r in all_results:
        status_label = "[OK]" if r['status'] == 'correct' else "[FAIL]"
        conf = f"{r['confidence']:.2f}"
        issue = r.get('root_cause', 'none')[:32] + "..." if len(r.get('root_cause', '')) > 32 else r.get('root_cause', 'none')
        print(f"{r['case_name']:<20} {status_label:<10} {conf:<12} {issue:<35}")
    
    print("-"*80)
    broken = sum(1 for r in all_results if r['status'] == 'broken')
    correct = sum(1 for r in all_results if r['status'] == 'correct')
    errors = sum(1 for r in all_results if r['status'] == 'error')
    
    print(f"\nTotal: {len(all_results)} | Broken: {broken} | Correct: {correct} | Errors: {errors}")
    print(f"\nStage Performance:")
    print(f"  Stage 1 (CV checks): {stage1_caught} ({stage1_caught/len(cases)*100:.0f}%)")
    print(f"  Stage 2+3 (LLM/VLM): {stage2_caught + stage3_used} ({(stage2_caught + stage3_used)/len(cases)*100:.0f}%)")
    
    print(f"\n⚡ Total time: {elapsed:.1f} seconds ({elapsed/len(cases):.2f}s per case)")
    print(f"\nJSON reports: {RESULTS_DIR}/")
    print("="*80)


if __name__ == "__main__":
    main()
