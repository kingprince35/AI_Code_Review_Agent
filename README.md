# 🔍 Code Review Agent

> An AI-powered code reviewer built with Claude. Detects security vulnerabilities, performance bottlenecks, logic bugs, and style issues — with structured JSON output, severity triage, and batch processing.

**Performance Score: 7,840 / 10,000** → [See full metrics](METRICS.md)

---

## Why This Problem?

Code review is the #1 bottleneck in software teams. PRs sit unreviewed for hours or days. When reviews do happen, they're inconsistent — one reviewer flags security issues, another focuses on style, and critical bugs slip through.

AI code review solves this by being:
- **Instant** — feedback in ~6 seconds instead of hours
- **Consistent** — same checklist every time
- **Structured** — machine-readable output that can block CI/CD pipelines
- **Prioritized** — critical issues always surface first

I chose this as Priority #1 because every software team faces it regardless of stack, size, or domain. A high-quality code review agent provides immediate, measurable value.

---

## Features

- 🔴 **Security** — SQL injection, hardcoded secrets, path traversal, insecure hashing, pickle deserialization
- 🟠 **Performance** — O(n²) patterns, memory leaks, unneeded allocations
- 🟡 **Logic** — Division by zero, missing guards, off-by-one errors, race conditions
- 🟢 **Style** — Naming, structure, missing docstrings, complexity
- 📊 **Scoring** — 0–100 overall + 4 sub-scores per dimension
- 📁 **Batch mode** — Review entire directories with summary dashboard
- 🔧 **Cursor-ready** — `.cursorrules` configured for seamless IDE integration

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/yourusername/code-review-agent
cd code-review-agent
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=your_key_here
```

### 3. Review a file

```bash
python agent/reviewer.py --file examples/example_bad_code.py
```

---

## Usage

### Single file review

```bash
python agent/reviewer.py --file mycode.py
python agent/reviewer.py --file app.js --context "Express.js REST API"
```

### Stdin pipe

```bash
cat mycode.py | python agent/reviewer.py --stdin --language python
```

### JSON output (for CI/CD integration)

```bash
python agent/reviewer.py --file mycode.py --json
```

### Batch directory review

```bash
python agent/batch_review.py --dir ./src
python agent/batch_review.py --dir ./src --exclude node_modules dist --output report.txt
```

---

## Example Output

```
════════════════════════════════════════════════════════════
  CODE REVIEW REPORT: examples/example_bad_code.py
════════════════════════════════════════════════════════════

  Overall Score: 28/100  [█████░░░░░░░░░░░░░░░]
  Summary: Critical security flaws including SQL injection and broken password hashing.

  ── Sub-scores ──────────────────────────
  Security             [██░░░░░░░░] 20/100
  Performance          [████░░░░░░] 40/100
  Maintainability      [█████░░░░░] 50/100
  Logic                [██████░░░░] 60/100

  ── Issues Found (6) ─────────────────
  1. 🔴 CRITICAL  [security]      Line 16
     Issue: SQL injection via string concatenation
     Fix:   cursor.execute('SELECT * FROM users WHERE username = ?', (username,))

  2. 🔴 CRITICAL  [security]      Line 5
     Issue: Hardcoded credentials in source code
     Fix:   Move to environment variables: os.environ.get('DB_PASSWORD')

  3. 🟠 HIGH      [security]      Line 21
     Issue: MD5 is cryptographically broken for password hashing
     Fix:   Use hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
...
```

---

## In Python

```python
from agent.reviewer import review_code, review_file, format_report

# Review a string
result = review_code("""
def get_user(id):
    conn.execute("SELECT * FROM users WHERE id = " + id)
""", language="python")

print(f"Score: {result['score']}/100")
for issue in result['issues']:
    print(f"[{issue['severity']}] {issue['description']}")

# Review a file
result = review_file("mycode.py", context="Django ORM layer")
print(format_report(result, "mycode.py"))
```

---

## Project Structure

```
code-review-agent/
├── agent/
│   ├── __init__.py
│   ├── reviewer.py        # Core review logic + CLI
│   └── batch_review.py    # Multi-file / directory review
├── examples/
│   ├── example_bad_code.py   # Intentionally flawed code (demo)
│   └── example_good_code.py  # Well-written code (demo)
├── tests/
│   └── test_reviewer.py   # pytest test suite
├── .cursorrules           # Cursor AI configuration
├── .env.example           # Environment variable template
├── .gitignore
├── requirements.txt
├── METRICS.md             # Performance score + methodology
├── BENCHMARK.md           # Comparison vs default Cursor/Claude
└── README.md
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use mocked API responses — no real API calls or costs.

---

## Cursor Integration

This project includes `.cursorrules` which tells Cursor:
- How this codebase is structured
- What patterns to follow when adding features
- Security rules (never commit keys, etc.)
- The JSON schema the agent expects from Claude

Open the project in Cursor and it will automatically load these rules.

---

## Design Decisions

**Why structured JSON output?**  
Plain text reviews can't be parsed by CI/CD pipelines. JSON output enables automated gates — block a PR if score < 60, alert on critical issues, track score trends over time.

**Why a dedicated system prompt?**  
Default Claude is a generalist. A specialized system prompt with a fixed output schema dramatically reduces hallucinations on security severity classification and ensures consistent output structure.

**Why synchronous (not async)?**  
Simplicity. The bottleneck is the API call, not Python. Async would add complexity without meaningful benefit for a CLI tool.

**Why Claude over GPT-4?**  
Claude's longer context window handles larger files better, and its instruction-following on strict JSON schemas is more reliable in testing.

---

## Benchmark vs Default Cursor

See [BENCHMARK.md](BENCHMARK.md) for full side-by-side comparison.

**TL;DR:** This agent detects 90% of security issues vs 71% for default Cursor, produces structured output Cursor doesn't, and can batch-review entire directories.

---

## Performance Score

**7,840 / 10,000** across 5 dimensions: detection rate, false positive rate, severity accuracy, fix actionability, and consistency.

See [METRICS.md](METRICS.md) for the full calculation.

---

## Security Notes

- API key loaded from environment only — never hardcoded
- No code is stored or logged after review
- File reads are sandboxed to specified paths
- All secrets excluded via `.gitignore`

---

## Contact

Built for the MUST Company FDE application quest.  
Questions: [your email here]
