# example_good_code.py — Well-written code for comparison
# Shows what high-scoring code looks like

import os
import hashlib
import secrets
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional


DATABASE_URL = os.environ.get("DATABASE_URL", "users.db")
BASE_DIR = Path(__file__).parent.resolve()


@contextmanager
def get_db_connection():
    """Context manager for safe database connections."""
    conn = sqlite3.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def get_user(username: str) -> Optional[tuple]:
    """
    Fetch a user by username using parameterized queries.

    Args:
        username: The username to look up.

    Returns:
        User row tuple or None if not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a random salt (PBKDF2).

    Args:
        password: Plain text password.

    Returns:
        Hex-encoded hash string.
    """
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}:{dk.hex()}"


def safe_read_file(filename: str) -> str:
    """
    Read a file safely, preventing path traversal attacks.

    Args:
        filename: Relative filename to read from BASE_DIR.

    Returns:
        File contents as string.

    Raises:
        ValueError: If the resolved path escapes the base directory.
        FileNotFoundError: If the file does not exist.
    """
    target = (BASE_DIR / filename).resolve()
    if not str(target).startswith(str(BASE_DIR)):
        raise ValueError(f"Path traversal detected: {filename}")
    return target.read_text(encoding="utf-8")


def find_duplicates(items: list) -> list:
    """
    Find duplicate values in a list efficiently.

    Args:
        items: Input list.

    Returns:
        List of values that appear more than once.

    Time complexity: O(n)
    """
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)


def divide(a: float, b: float) -> float:
    """
    Safely divide two numbers.

    Args:
        a: Numerator.
        b: Denominator.

    Returns:
        Result of a / b.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b
