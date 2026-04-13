# example_bad_code.py — Intentionally flawed code for demo purposes
# This file demonstrates what the Code Review Agent catches

import sqlite3
import hashlib
import pickle
import os

# BAD: Hardcoded credentials
DB_PASSWORD = "admin123"
SECRET_KEY = "supersecretkey"

def get_user(username):
    # BAD: SQL injection vulnerability
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()
    # BAD: Connection never closed

def hash_password(password):
    # BAD: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()

def load_config(filename):
    # BAD: Arbitrary pickle deserialization — remote code execution risk
    with open(filename, "rb") as f:
        return pickle.load(f)

def process_items(items):
    result = []
    # BAD: O(n²) — appending in a loop instead of list comprehension
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == items[j] and i != j:
                result.append(items[i])
    return result

def read_file(path):
    # BAD: No path traversal protection
    with open(path, "r") as f:
        return f.read()

def divide(a, b):
    # BAD: No zero-division guard
    return a / b

class UserManager:
    def __init__(self):
        self.users = {}

    def add_user(self, name, data):
        # BAD: No input validation
        self.users[name] = data

    def get_all(self):
        # BAD: Returns mutable internal state
        return self.users
