"""
Code Review Agent - AI-powered code review using Claude
Specialized in: security, performance, logic bugs, and style issues
"""

import os
import sys
import json
import argparse
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of:
- Security vulnerabilities (OWASP Top 10, injection attacks, auth flaws)
- Performance bottlenecks (complexity, memory leaks, inefficient patterns)
- Logic bugs (edge cases, off-by-one errors, race conditions)
- Code style & maintainability (readability, naming, structure)
- Best practices for Python, JavaScript, TypeScript, Go, and Java

When reviewing code, always structure your response as JSON with this exact format:
{
  "summary": "1-2 sentence overview",
  "score": <integer 0-100>,
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "category": "security|performance|logic|style",
      "line": <line number or null>,
      "description": "clear description of the issue",
      "suggestion": "concrete fix or improvement"
    }
  ],
  "strengths": ["list of things done well"],
  "metrics": {
    "security_score": <0-100>,
    "performance_score": <0-100>,
    "maintainability_score": <0-100>,
    "logic_score": <0-100>
  }
}

Be precise, actionable, and prioritize critical issues first."""


def review_code(code: str, language: str = "auto", context: str = "") -> dict:
    """
    Run AI-powered code review on the given code.
    
    Args:
        code: Source code to review
        language: Programming language (auto-detect if not specified)
        context: Optional context about what the code does
    
    Returns:
        dict with review results
    """
    user_message = f"""Please review the following{' ' + language if language != 'auto' else ''} code:

```{language if language != 'auto' else ''}
{code}
```
{f'Context: {context}' if context else ''}

Provide a thorough review focusing on security, performance, logic correctness, and maintainability."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    raw = response.choices[0].message.content.strip()
    
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw)


def review_file(filepath: str, context: str = "") -> dict:
    """Review a code file by path."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Detect language from extension
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".go": "go", ".java": "java", ".rs": "rust", ".cpp": "cpp",
        ".c": "c", ".rb": "ruby", ".php": "php", ".cs": "csharp"
    }
    language = ext_map.get(path.suffix.lower(), "auto")
    code = path.read_text(encoding="utf-8")
    
    return review_code(code, language, context)


def format_report(review: dict, filepath: str = None) -> str:
    """Format the review result as a readable terminal report."""
    lines = []
    
    # Header
    lines.append("\n" + "═" * 60)
    if filepath:
        lines.append(f"  CODE REVIEW REPORT: {filepath}")
    else:
        lines.append("  CODE REVIEW REPORT")
    lines.append("═" * 60)
    
    # Overall score
    score = review.get("score", 0)
    bar = "█" * (score // 5) + "░" * (20 - score // 5)
    lines.append(f"\n  Overall Score: {score}/100  [{bar}]")
    lines.append(f"  Summary: {review.get('summary', '')}")
    
    # Sub-metrics
    metrics = review.get("metrics", {})
    if metrics:
        lines.append("\n  ── Sub-scores ──────────────────────────")
        for key, val in metrics.items():
            label = key.replace("_score", "").capitalize().ljust(20)
            mini_bar = "█" * (val // 10) + "░" * (10 - val // 10)
            lines.append(f"  {label} [{mini_bar}] {val}/100")
    
    # Issues
    issues = review.get("issues", [])
    if issues:
        lines.append(f"\n  ── Issues Found ({len(issues)}) ─────────────────")
        severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        for i, issue in enumerate(issues, 1):
            icon = severity_icons.get(issue.get("severity", "low"), "⚪")
            sev = issue.get("severity", "").upper().ljust(8)
            cat = f"[{issue.get('category', '')}]".ljust(14)
            line_ref = f"Line {issue['line']}" if issue.get("line") else "General"
            lines.append(f"\n  {i}. {icon} {sev} {cat} {line_ref}")
            lines.append(f"     Issue: {issue.get('description', '')}")
            lines.append(f"     Fix:   {issue.get('suggestion', '')}")
    else:
        lines.append("\n  ✅ No issues found!")
    
    # Strengths
    strengths = review.get("strengths", [])
    if strengths:
        lines.append(f"\n  ── Strengths ───────────────────────────")
        for s in strengths:
            lines.append(f"  ✓ {s}")
    
    lines.append("\n" + "═" * 60 + "\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered Code Review Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent/reviewer.py --file mycode.py
  python agent/reviewer.py --file app.js --context "Express.js REST API"
  python agent/reviewer.py --stdin --language python < mycode.py
  python agent/reviewer.py --file mycode.py --json
        """
    )
    parser.add_argument("--file", help="Path to code file to review")
    parser.add_argument("--stdin", action="store_true", help="Read code from stdin")
    parser.add_argument("--language", default="auto", help="Programming language")
    parser.add_argument("--context", default="", help="Context about what the code does")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output raw JSON")
    
    args = parser.parse_args()
    
    if not args.file and not args.stdin:
        parser.print_help()
        sys.exit(1)
    
    if args.file:
        review = review_file(args.file, args.context)
        filepath = args.file
    else:
        code = sys.stdin.read()
        review = review_code(code, args.language, args.context)
        filepath = None
    
    if args.json_output:
        print(json.dumps(review, indent=2))
    else:
        print(format_report(review, filepath))


if __name__ == "__main__":
    main()
