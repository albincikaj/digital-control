"""Password gate for deployed instances.

The password itself is never stored: only a salted PBKDF2-SHA256 hash, read from
  1. Streamlit secrets:   [auth] password_hash = "pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>"
  2. or the environment:  DC_TRAINER_PASSWORD_HASH=...
Generate the value with:  .venv/bin/python set_password.py
If neither is configured the app stays open (local use) and shows a warning.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets as _secrets
import time

import streamlit as st

ITERATIONS = 200_000
_GLOBAL_FAILS: list = []  # timestamps of failed logins across ALL sessions (process-wide)
_WINDOW, _MAX_FAILS = 600, 20  # max 20 failures per 10 minutes, then lock


def _locked() -> bool:
    now = time.time()
    _GLOBAL_FAILS[:] = [t for t in _GLOBAL_FAILS if now - t < _WINDOW]
    return len(_GLOBAL_FAILS) >= _MAX_FAILS


def make_hash(password: str, iterations: int = ITERATIONS) -> str:
    salt = _secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify(password: str, stored: str) -> bool:
    try:
        algo, it, salt_hex, hash_hex = stored.strip().split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(it))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def configured_hash() -> str | None:
    try:
        h = st.secrets.get("auth", {}).get("password_hash")
        if h:
            return str(h)
    except Exception:  # no secrets file at all
        pass
    return os.environ.get("DC_TRAINER_PASSWORD_HASH") or None


def require_login() -> bool:
    """Render the login screen if needed. Returns True when the user may see the app."""
    stored = configured_hash()
    ss = st.session_state
    if stored is None:
        ss["_auth_open"] = True
        return True
    ss["_auth_open"] = False
    if ss.get("_auth_ok"):
        return True

    st.markdown("## 🎛️ Digital Control Trainer")
    st.caption("Private study app — please log in.")
    fails = ss.get("_auth_fails", 0)
    with st.form("login", clear_on_submit=True):
        pw = st.text_input("Password", type="password")
        ok = st.form_submit_button("Log in", type="primary")
    if ok and _locked():
        st.error("Too many failed attempts — login is locked for a few minutes.")
        return False
    if ok:
        if fails:
            time.sleep(min(2 ** fails, 30))  # slow down guessing
        if verify(pw or "", stored):
            ss["_auth_ok"] = True
            ss["_auth_fails"] = 0
            st.rerun()
        else:
            ss["_auth_fails"] = fails + 1
            _GLOBAL_FAILS.append(time.time())
            st.error("Wrong password.")
    return False


def sidebar_controls():
    ss = st.session_state
    if ss.get("_auth_open"):
        st.warning("🔓 No password set — anyone with the link can use this app. Run `set_password.py` (see README).", icon="⚠️")
    elif ss.get("_auth_ok"):
        if st.button("🔒 Log out", width="stretch"):
            ss["_auth_ok"] = False
            st.rerun()
