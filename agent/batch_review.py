"""
Batch Code Review - Review multiple files or a full directory
"""

import os
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent.reviewer import review_file, format_report

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".go", ".java", ".rs",
    ".cpp", ".c", ".rb", ".php", ".cs"
}


def review_directory(dirpath: str, exclude: list = None, max_workers: int = 3) -> list:
    """
    Review all code files in a directory.
    
    Args:
        dirpath: Path to directory
        exclude: List of patterns to exclude (e.g., ['node_modules', '__pycache__'])
        max_workers: Number of parallel review threads
    
    Returns:
        List of (filepath, review_dict) tuples
    """
    exclude = exclude or ["node_modules", "__pycache__", ".git", "venv", ".env", "dist", "build"]
    path = Path(dirpath)
    
    files = []
    for f in path.rglob("*"):
        if f.is_file() and f.suffix in SUPPORTED_EXTENSIONS:
            if not any(ex in str(f) for ex in exclude):
                files.append(str(f))
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(review_file, f): f for f in files}
        for future in as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                review = future.result()
                results.append((filepath, review))
                print(f"  ✓ Reviewed: {filepath} (score: {review.get('score', '?')}/100)")
            except Exception as e:
                print(f"  ✗ Failed: {filepath} — {e}")
    
    return sorted(results, key=lambda x: x[1].get("score", 100))


def generate_summary_report(results: list) -> str:
    """Generate a high-level summary across all reviewed files."""
    if not results:
        return "No files reviewed."
    
    total_score = sum(r[1].get("score", 0) for r in results)
    avg_score = total_score / len(results)
    
    all_issues = []
    for filepath, review in results:
        for issue in review.get("issues", []):
            issue["file"] = filepath
            all_issues.append(issue)
    
    critical = [i for i in all_issues if i.get("severity") == "critical"]
    high = [i for i in all_issues if i.get("severity") == "high"]
    
    lines = [
        "\n" + "═" * 60,
        "  BATCH REVIEW SUMMARY",
        "═" * 60,
        f"\n  Files Reviewed : {len(results)}",
        f"  Average Score  : {avg_score:.1f}/100",
        f"  Total Issues   : {len(all_issues)}",
        f"  Critical       : {len(critical)} 🔴",
        f"  High           : {len(high)} 🟠",
        "\n  ── File Scores (worst first) ────────────────",
    ]
    
    for filepath, review in results:
        score = review.get("score", 0)
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        lines.append(f"  [{bar}] {score:3d}  {filepath}")
    
    if critical:
        lines.append("\n  ── Critical Issues ─────────────────────")
        for issue in critical[:5]:
            lines.append(f"  🔴 {issue['file']}")
            lines.append(f"     {issue.get('description', '')}")
    
    lines.append("\n" + "═" * 60 + "\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Batch AI Code Review")
    parser.add_argument("--dir", help="Directory to review")
    parser.add_argument("--files", nargs="+", help="Specific files to review")
    parser.add_argument("--exclude", nargs="*", default=[], help="Patterns to exclude")
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--output", help="Save report to file")
    
    args = parser.parse_args()
    
    results = []
    
    if args.dir:
        print(f"\nScanning directory: {args.dir}")
        results = review_directory(args.dir, args.exclude, args.workers)
    elif args.files:
        for f in args.files:
            try:
                review = review_file(f)
                results.append((f, review))
                print(f"  ✓ Reviewed: {f}")
            except Exception as e:
                print(f"  ✗ Failed: {f} — {e}")
    
    if args.json_output:
        output = json.dumps([{"file": f, "review": r} for f, r in results], indent=2)
    else:
        individual = "\n".join(format_report(r, f) for f, r in results)
        output = individual + generate_summary_report(results)
    
    if args.output:
        Path(args.output).write_text(output)
        print(f"\nReport saved to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
