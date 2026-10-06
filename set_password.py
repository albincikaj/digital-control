"""Create the login password hash.

Usage:  .venv/bin/python set_password.py
Prints the snippet for Streamlit Cloud (App → Settings → Secrets) and writes .streamlit/secrets.toml for local use.
The plain password is never written anywhere.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dctrainer.auth import make_hash  # noqa: E402

pw = getpass.getpass("New password: ")
if len(pw) < 10:
    sys.exit("Use at least 10 characters.")
if getpass.getpass("Repeat password: ") != pw:
    sys.exit("Passwords do not match.")
h = make_hash(pw)
snippet = f'[auth]\npassword_hash = "{h}"\n'
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "secrets.toml")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    f.write(snippet)
os.chmod(path, 0o600)
print(f"\nWrote {path} (local use; it is git-ignored).")
print("\nFor Streamlit Community Cloud paste this into  App → ⋮ → Settings → Secrets :\n")
print(snippet)
