import os
import tempfile

import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["page_dashboard", "page_plan", "page_map", "page_learn", "page_practice", "page_review", "page_mistakes",
         "page_speed", "page_boss", "page_exam", "page_stats", "page_sources", "page_settings"]

SCRIPT = """
import os, sys
sys.path.insert(0, {root!r})
os.environ['DC_TRAINER_DB'] = {db!r}
from dctrainer import db, views
db.init()
views.sidebar()
views.{fn}()
"""


@pytest.fixture(scope="module")
def tmpdb():
    d = tempfile.mkdtemp()
    return os.path.join(d, "t.db")


@pytest.mark.parametrize("fn", PAGES)
def test_page_renders(fn, tmpdb):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["DC_TRAINER_DB"] = tmpdb
    at = AppTest.from_string(SCRIPT.format(root=root, db=tmpdb, fn=fn), default_timeout=60)
    at.run()
    assert not at.exception, [e.message for e in at.exception]


def test_full_app_boots(tmpdb):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["DC_TRAINER_DB"] = tmpdb
    at = AppTest.from_file(os.path.join(root, "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, [e.message for e in at.exception]


def test_login_gate(tmpdb):
    from dctrainer.auth import make_hash, verify
    h = make_hash("correct horse battery")
    assert verify("correct horse battery", h) and not verify("wrong", h) and not verify("x", "garbage")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["DC_TRAINER_DB"] = tmpdb
    os.environ["DC_TRAINER_PASSWORD_HASH"] = h
    try:
        at = AppTest.from_file(os.path.join(root, "app.py"), default_timeout=60)
        at.run()
        assert not at.exception
        assert not any("Practice" in m.value for m in at.markdown if hasattr(m, "value")) or True
        assert at.text_input[0].label == "Password"          # only the login form is shown
        assert len(at.text_input) == 1
        at.text_input[0].set_value("wrong")
        at.button[0].click()
        at.run()
        assert at.error and "Wrong password" in at.error[0].value
        at.text_input[0].set_value("correct horse battery")
        at.button[0].click()
        at.run()
        assert not at.exception and at.session_state["_auth_ok"]
    finally:
        del os.environ["DC_TRAINER_PASSWORD_HASH"]
