"""SQLite persistence (single local file)."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, date

_DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "progress.db")


def db_path() -> str:
    return os.environ.get("DC_TRAINER_DB", _DEFAULT_DB)

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, gen_id TEXT, topic TEXT, difficulty INT, seed INT,
    score REAL, max_score REAL, correct_parts INT, total_parts INT, hints INT, duration REAL, mode TEXT);
CREATE TABLE IF NOT EXISTS part_results (attempt_id INT, part_key TEXT, correct INT, tag TEXT);
CREATE TABLE IF NOT EXISTS mastery (
    topic TEXT PRIMARY KEY, value REAL DEFAULT 0, attempts INT DEFAULT 0, last_ts TEXT,
    next_review TEXT, interval REAL DEFAULT 0.5, manual_unlock INT DEFAULT 0, best_diff INT DEFAULT 0, learned INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY, ease REAL DEFAULT 2.3, interval REAL DEFAULT 0, due TEXT, reps INT DEFAULT 0,
    lapses INT DEFAULT 0, last_score REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS mistakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, gen_id TEXT, topic TEXT, difficulty INT, seed INT,
    part_key TEXT, tag TEXT, diagnosis TEXT, user_answer TEXT, correct_answer TEXT, resolved INT DEFAULT 0,
    due TEXT, streak INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS xp_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, day TEXT, amount INT, reason TEXT);
CREATE TABLE IF NOT EXISTS achievements (id TEXT PRIMARY KEY, ts TEXT);
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, theory REAL, practical REAL, total REAL,
    max_total REAL, duration REAL, details TEXT);
CREATE TABLE IF NOT EXISTS bosses (boss_id TEXT, ts TEXT, score REAL, max_score REAL, won INT, duration REAL);
CREATE TABLE IF NOT EXISTS activity (day TEXT PRIMARY KEY, problems INT DEFAULT 0, cards INT DEFAULT 0, seconds REAL DEFAULT 0);
"""


def now() -> datetime:
    return datetime.now()


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def today() -> str:
    return date.today().isoformat()


@contextmanager
def conn():
    os.makedirs(os.path.dirname(db_path()), exist_ok=True)
    c = sqlite3.connect(db_path(), timeout=10)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(SCHEMA)


# ------------------------------------------------------------------ settings
def get_setting(key, default=None):
    with conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return json.loads(r["value"]) if r else default


def set_setting(key, value):
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value)))


# ------------------------------------------------------------------ mastery
def mastery_all() -> dict:
    with conn() as c:
        rows = c.execute("SELECT * FROM mastery").fetchall()
    return {r["topic"]: dict(r) for r in rows}


def mastery_get(topic) -> dict:
    with conn() as c:
        r = c.execute("SELECT * FROM mastery WHERE topic=?", (topic,)).fetchone()
    return dict(r) if r else dict(topic=topic, value=0.0, attempts=0, last_ts=None, next_review=None, interval=0.5,
                                  manual_unlock=0, best_diff=0, learned=0)


def mastery_put(m: dict):
    with conn() as c:
        c.execute("""INSERT INTO mastery(topic,value,attempts,last_ts,next_review,interval,manual_unlock,best_diff,learned)
                     VALUES(:topic,:value,:attempts,:last_ts,:next_review,:interval,:manual_unlock,:best_diff,:learned)
                     ON CONFLICT(topic) DO UPDATE SET value=excluded.value, attempts=excluded.attempts, last_ts=excluded.last_ts,
                     next_review=excluded.next_review, interval=excluded.interval, manual_unlock=excluded.manual_unlock,
                     best_diff=excluded.best_diff, learned=excluded.learned""", m)


# ------------------------------------------------------------------ attempts
def log_attempt(gen_id, topic, difficulty, seed, score, max_score, results, hints, duration, mode) -> int:
    with conn() as c:
        cur = c.execute("""INSERT INTO attempts(ts,gen_id,topic,difficulty,seed,score,max_score,correct_parts,total_parts,hints,duration,mode)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (iso(now()), gen_id, topic, difficulty, seed, score, max_score,
                         sum(1 for r in results.values() if r["correct"]), len(results), hints, duration, mode))
        aid = cur.lastrowid
        c.executemany("INSERT INTO part_results(attempt_id,part_key,correct,tag) VALUES(?,?,?,?)",
                      [(aid, k, int(r["correct"]), r.get("tag")) for k, r in results.items()])
        c.execute("INSERT INTO activity(day,problems,seconds) VALUES(?,1,?) ON CONFLICT(day) DO UPDATE SET problems=problems+1, seconds=seconds+excluded.seconds",
                  (today(), float(duration or 0)))
    return aid


def attempts(limit=None, topic=None):
    q = "SELECT * FROM attempts"
    args = []
    if topic:
        q += " WHERE topic=?"
        args.append(topic)
    q += " ORDER BY id DESC"
    if limit:
        q += f" LIMIT {int(limit)}"
    with conn() as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def count(table, where="1=1", args=()):
    with conn() as c:
        return c.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE {where}", args).fetchone()["n"]


def scalar(sql, args=()):
    with conn() as c:
        r = c.execute(sql, args).fetchone()
    return r[0] if r else None


def rows(sql, args=()):
    with conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


# ------------------------------------------------------------------ cards (SRS)
def card_get(card_id):
    with conn() as c:
        r = c.execute("SELECT * FROM cards WHERE card_id=?", (card_id,)).fetchone()
    return dict(r) if r else dict(card_id=card_id, ease=2.3, interval=0.0, due=None, reps=0, lapses=0, last_score=0.0)


def card_put(cd):
    with conn() as c:
        c.execute("""INSERT INTO cards(card_id,ease,interval,due,reps,lapses,last_score) VALUES(:card_id,:ease,:interval,:due,:reps,:lapses,:last_score)
                     ON CONFLICT(card_id) DO UPDATE SET ease=excluded.ease, interval=excluded.interval, due=excluded.due, reps=excluded.reps,
                     lapses=excluded.lapses, last_score=excluded.last_score""", cd)
        c.execute("INSERT INTO activity(day,cards) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET cards=cards+1", (today(),))


def cards_all() -> dict:
    with conn() as c:
        return {r["card_id"]: dict(r) for r in c.execute("SELECT * FROM cards").fetchall()}


# ------------------------------------------------------------------ mistakes
def add_mistake(gen_id, topic, difficulty, seed, part_key, tag, diagnosis, user_answer, correct_answer):
    with conn() as c:
        c.execute("""INSERT INTO mistakes(ts,gen_id,topic,difficulty,seed,part_key,tag,diagnosis,user_answer,correct_answer,due)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (iso(now()), gen_id, topic, difficulty, seed, part_key, tag, diagnosis, str(user_answer), str(correct_answer), iso(now())))


def open_mistakes():
    return rows("SELECT * FROM mistakes WHERE resolved=0 ORDER BY id DESC")


def update_mistake(mid, **kw):
    sets = ", ".join(f"{k}=?" for k in kw)
    with conn() as c:
        c.execute(f"UPDATE mistakes SET {sets} WHERE id=?", (*kw.values(), mid))


# ------------------------------------------------------------------ xp / achievements / exams
def add_xp(amount, reason):
    with conn() as c:
        c.execute("INSERT INTO xp_log(ts,day,amount,reason) VALUES(?,?,?,?)", (iso(now()), today(), int(amount), reason))


def total_xp() -> int:
    return int(scalar("SELECT COALESCE(SUM(amount),0) FROM xp_log") or 0)


def xp_by_day() -> dict:
    return {r["day"]: r["s"] for r in rows("SELECT day, SUM(amount) AS s FROM xp_log GROUP BY day")}


def unlock_achievement(aid) -> bool:
    with conn() as c:
        r = c.execute("SELECT 1 FROM achievements WHERE id=?", (aid,)).fetchone()
        if r:
            return False
        c.execute("INSERT INTO achievements(id,ts) VALUES(?,?)", (aid, iso(now())))
    return True


def achievements() -> dict:
    return {r["id"]: r["ts"] for r in rows("SELECT * FROM achievements")}


def log_exam(kind, theory, practical, total, max_total, duration, details):
    with conn() as c:
        c.execute("INSERT INTO exams(ts,kind,theory,practical,total,max_total,duration,details) VALUES(?,?,?,?,?,?,?,?)",
                  (iso(now()), kind, theory, practical, total, max_total, duration, json.dumps(details)))


def log_boss(boss_id, score, max_score, won, duration):
    with conn() as c:
        c.execute("INSERT INTO bosses(boss_id,ts,score,max_score,won,duration) VALUES(?,?,?,?,?,?)",
                  (boss_id, iso(now()), score, max_score, int(won), duration))


def reset_all():
    if os.path.exists(db_path()):
        os.remove(db_path())
    init()


def parse(ts):
    return datetime.fromisoformat(ts) if ts else None


def plus_days(days: float) -> str:
    return iso(now() + timedelta(days=days))
