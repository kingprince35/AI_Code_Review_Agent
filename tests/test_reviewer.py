"""
Tests for Code Review Agent
Run with: pytest tests/ -v
"""

import json
import pytest
from unittest.mock import MagicMock, patch


MOCK_REVIEW_RESPONSE = {
    "summary": "Code has critical SQL injection and weak hashing issues.",
    "score": 28,
    "issues": [
        {
            "severity": "critical",
            "category": "security",
            "line": 16,
            "description": "SQL injection via string concatenation",
            "suggestion": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE username = ?', (username,))"
        },
        {
            "severity": "high",
            "category": "security",
            "line": 21,
            "description": "MD5 is cryptographically broken for password hashing",
            "suggestion": "Use hashlib.pbkdf2_hmac or bcrypt"
        }
    ],
    "strengths": ["Consistent naming convention"],
    "metrics": {
        "security_score": 10,
        "performance_score": 40,
        "maintainability_score": 50,
        "logic_score": 60
    }
}


def make_mock_response(data: dict):
    """Build a mock Anthropic API response."""
    mock_content = MagicMock()
    mock_content.text = json.dumps(data)
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


@patch("agent.reviewer.client")
def test_review_code_returns_dict(mock_client):
    """review_code() should return a dict with expected keys."""
    from agent.reviewer import review_code
    mock_client.messages.create.return_value = make_mock_response(MOCK_REVIEW_RESPONSE)

    result = review_code("def foo(): pass", language="python")

    assert isinstance(result, dict)
    assert "score" in result
    assert "issues" in result
    assert "summary" in result
    assert "metrics" in result


@patch("agent.reviewer.client")
def test_review_code_score_range(mock_client):
    """Score should be between 0 and 100."""
    from agent.reviewer import review_code
    mock_client.messages.create.return_value = make_mock_response(MOCK_REVIEW_RESPONSE)

    result = review_code("x = 1")
    assert 0 <= result["score"] <= 100


@patch("agent.reviewer.client")
def test_review_detects_critical_issues(mock_client):
    """Should correctly parse critical severity issues."""
    from agent.reviewer import review_code
    mock_client.messages.create.return_value = make_mock_response(MOCK_REVIEW_RESPONSE)

    result = review_code("SELECT * FROM users WHERE id = '" + "x" + "'")
    critical = [i for i in result["issues"] if i["severity"] == "critical"]
    assert len(critical) >= 1


@patch("agent.reviewer.client")
def test_format_report_contains_score(mock_client):
    """format_report() output should include the score."""
    from agent.reviewer import review_code, format_report
    mock_client.messages.create.return_value = make_mock_response(MOCK_REVIEW_RESPONSE)

    result = review_code("bad code")
    report = format_report(result, "test.py")

    assert "28" in report  # score is 28
    assert "test.py" in report


def test_review_file_not_found():
    """review_file() should raise FileNotFoundError for missing files."""
    from agent.reviewer import review_file
    with pytest.raises(FileNotFoundError):
        review_file("/nonexistent/path/code.py")


@patch("agent.reviewer.client")
def test_review_strips_markdown_fences(mock_client):
    """Should handle Claude responses wrapped in markdown code fences."""
    from agent.reviewer import review_code
    # Simulate Claude wrapping JSON in ```json ... ```
    raw_with_fences = "```json\n" + json.dumps(MOCK_REVIEW_RESPONSE) + "\n```"
    mock_content = MagicMock()
    mock_content.text = raw_with_fences
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response

    result = review_code("code here")
    assert result["score"] == 28


@patch("agent.reviewer.client")
def test_metrics_keys_present(mock_client):
    """All four metric keys should be present in the response."""
    from agent.reviewer import review_code
    mock_client.messages.create.return_value = make_mock_response(MOCK_REVIEW_RESPONSE)

    result = review_code("code")
    metrics = result.get("metrics", {})

    for key in ["security_score", "performance_score", "maintainability_score", "logic_score"]:
        assert key in metrics, f"Missing metric: {key}"
