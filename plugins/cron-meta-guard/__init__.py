"""cron-meta-guard: verhindert, dass Meta-Antworten eines Cron-Laufs beim Nutzer landen.

TECHNIK (kein Upstream-Patch)
* transform_llm_output (Hermes-Hook, feuert im Agent pro Turn): Laeuft der Agent in einem
  Cron-Lauf (ctx.current_cron_execution()) und der finale Text enthaelt Meta-Muster, ersetzt
  der Hook ihn durch "[SILENT]". Der Scheduler stellt dann nicht zu (Output bleibt lokal
  gespeichert). Mid-Run darf der Hook den Job-Status nicht anfassen, der Scheduler schreibt
  ihn danach mit mark_job_run.
* Ein Daemon-Thread wartet, bis der Lauf beendet ist, und dann
  1. markiert den Job per cron.jobs.update_job als last_status=error (Cockpit-Cron-Monitor),
  2. Versuch 1: cron.jobs.trigger_job(job, extra_prompt="... Gib NUR den Nachrichtentext aus ...")
  3. Versuch 2 (Retry scheitert ebenfalls): keine Zustellung an den Nutzer, Meldung nur an
     den Betreiber (Alert-Datei), kein weiterer Retry.
* Zustand (Versuchszaehler pro Job) in JSON-Datei; ein sauberer Lauf setzt ihn zurueck.

REGELN
* no_agent-Jobs laufen nie durch den LLM-Hook, werden also nie beruehrt.
* Texte ueber max_len Zeichen (Standard 1500) gelten als Bericht, nicht als Meta-Antwort.
* Kurze Texte werden nur gewertet, wenn sie mit Rueckfrage/Meta-Einleitung beginnen ODER
  mindestens 2 verschiedene Muster enthalten (ein einzelnes "soll ich" im Fliesstext ist sauber).
* Allowlist (allowlist.json, CRON_META_GUARD_ALLOWLIST): gelistete Jobs und no_agent-Skript-Jobs
  werden gar nicht geprueft.
* Log (JSONL) enthaelt nie den Antworttext, nur Job, Muster, Versuch, Aktion.
* Fail-open: jeder Fehler im Guard laesst die Originalantwort unveraendert durch.
* Kill-Switch: CRON_META_GUARD_DISABLE=1.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

SILENT = "[SILENT]"
RETRY_PROMPT = (
    "WICHTIG: Gib NUR den Nachrichtentext aus, genau so, wie er beim Nutzer ankommen soll. "
    "Keine Rueckfrage, kein Angebot, keine Meta-Anmerkung, keine Bitte um Freigabe, "
    "keine Aussagen ueber deinen Zustand."
)
MAX_ATTEMPTS = 2
STATE_TTL_S = 6 * 3600
DEFAULT_MAX_LEN = 1500

# (Name, Regex). Umlaute und ae/oe/ue-Schreibweisen werden beide erkannt.
PATTERNS: List[tuple] = [
    ("ich_stehe_bereit", r"\bich\s+stehe\s+(?:\w+\s+)?bereit\b"),
    ("falls_du_moechtest", r"\bfalls\s+du\s+(?:m(?:ö|oe|o)chtest|willst|magst)\b"),
    ("explizite_freigabe", r"\bexplizite[rn]?\s+freigabe\b"),
    ("ansonsten_oben_fertig", r"\bansonsten\s+ist\s+(?:sie|es|er)\s+oben\s+fertig\b"),
    ("ich_bin_mir_nicht_sicher", r"\bich\s+bin\s+mir\s+nicht\s+sicher,?\s+ob\s+du\b"),
    ("soll_ich", r"\bsoll\s+ich\b"),
]
_COMPILED = [(n, re.compile(p, re.IGNORECASE)) for n, p in PATTERNS]

_HERE = os.path.dirname(os.path.abspath(__file__))
_LOG_DIR = os.path.join(os.path.expanduser(os.environ.get("HERMES_HOME") or "~/.hermes"), "logs")
_DEFAULT_LOG = os.path.join(_LOG_DIR, "cron_meta_guard.log")
_DEFAULT_STATE = os.path.join(_LOG_DIR, "cron_meta_guard_state.json")
_DEFAULT_ALERT = os.path.join(_LOG_DIR, "cron_meta_guard_alerts.log")
_lock = threading.Lock()


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _path(env: str, default: str) -> str:
    return os.environ.get(env) or default


# Opening-Muster: der Text BEGINNT mit einer Rueckfrage oder Meta-Einleitung.
OPENING_PATTERNS: List[str] = [
    r"^[\W_]*ich\s+stehe\s+(?:\w+\s+)?bereit\b",
    r"^[\W_]*soll\s+ich\b",
    r"^[\W_]*falls\s+du\s+(?:m(?:ö|oe|o)chtest|willst|magst)\b",
    r"^[\W_]*ich\s+bin\s+mir\s+nicht\s+sicher\b",
    r"^[\W_]*(?:kurze\s+)?r(?:ü|ue|u)ckfrage\b",
    r"^[\W_]*bevor\s+ich\b",
    r"^[\W_]*(?:allerdings\s+)?ist\s+mir\s+nicht\s+klar\b",
    r"^[\W_]*ich\s+(?:brauche|ben(?:ö|oe|o)tige)\s+(?:noch\s+)?(?:eine?n?\s+)?(?:explizite[rn]?\s+)?(?:freigabe|best(?:ä|ae|a)tigung)\b",
]
_OPENING = [re.compile(p, re.IGNORECASE) for p in OPENING_PATTERNS]
MIN_DISTINCT = 2


def _starts_with_meta(t: str) -> bool:
    head = t.lstrip()
    if any(rx.search(head) for rx in _OPENING):
        return True
    # Erster Satz ist eine Rueckfrage, die ein Meta-Muster enthaelt.
    m = re.match(r"[^.!?\n]*\?", head)
    return bool(m and any(rx.search(m.group(0)) for _, rx in _COMPILED))


def find_meta_patterns(text: Any, max_len: Optional[int] = None) -> List[str]:
    """Namen der gefundenen Meta-Muster ([] = sauber).

    Wertung nur, wenn der Text kurz ist UND (a) mit Rueckfrage/Meta-Einleitung beginnt ODER
    (b) mindestens MIN_DISTINCT verschiedene Muster enthaelt. Ein einzelnes "soll ich" bzw.
    "falls du moechtest" im Fliesstext eines Briefings ist sauber."""
    if not isinstance(text, str):
        return []
    t = text.strip()
    if not t or t.startswith("[CRON_FAILURE]"):
        return []
    limit = max_len if max_len is not None else int(os.environ.get("CRON_META_GUARD_MAX_LEN", DEFAULT_MAX_LEN))
    if len(t) > limit:
        return []
    found = [name for name, rx in _COMPILED if rx.search(t)]
    if not found:
        return []
    if len(found) >= MIN_DISTINCT or _starts_with_meta(t):
        return found
    return []


# ---------- Allowlist ----------
_ALLOWLIST_FILE = os.path.join(_HERE, "allowlist.json")


def _load_allowlist() -> List[str]:
    """Jobs, die der Guard gar nicht prueft. Quellen: allowlist.json im Plugin-Ordner und
    CRON_META_GUARD_ALLOWLIST (Komma-Liste aus job_id, 'profil:job_id' oder Job-Name, Glob erlaubt)."""
    entries: List[str] = []
    try:
        with open(os.environ.get("CRON_META_GUARD_ALLOWLIST_FILE", _ALLOWLIST_FILE), encoding="utf-8") as fh:
            data = json.load(fh)
        entries += [str(x) for x in (data.get("entries") or []) if str(x).strip()]
    except Exception:
        pass
    entries += [x.strip() for x in os.environ.get("CRON_META_GUARD_ALLOWLIST", "").split(",") if x.strip()]
    return entries


def _job_is_no_agent(home: str, job_id: str) -> bool:
    from cron import jobs
    with jobs.use_cron_store(home):
        job = jobs.get_job(job_id)
    return bool(job and job.get("no_agent"))


def is_allowlisted(ex: Any) -> bool:
    """True = Job wird nicht geprueft (Allowlist-Eintrag oder Skript-Job ohne Modell)."""
    import fnmatch
    names = {str(ex.job_id), f"{ex.profile}:{ex.job_id}", str(ex.job_name)}
    for entry in _load_allowlist():
        if any(fnmatch.fnmatchcase(n.lower(), entry.lower()) for n in names):
            return True
    try:
        return _job_is_no_agent(_hermes_home(), str(ex.job_id))
    except Exception:
        return False  # unbekannt: pruefen


def _log(event: Dict[str, Any]) -> None:
    try:
        p = _path("CRON_META_GUARD_LOG", _DEFAULT_LOG)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **event},
                                ensure_ascii=False) + "\n")
    except Exception as exc:  # pragma: no cover
        logger.warning("cron-meta-guard: Log nicht schreibbar: %s", exc)


# ---------- Zustand ----------
def _load_state() -> Dict[str, Any]:
    try:
        with open(_path("CRON_META_GUARD_STATE", _DEFAULT_STATE), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(state: Dict[str, Any]) -> None:
    p = _path("CRON_META_GUARD_STATE", _DEFAULT_STATE)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    os.replace(tmp, p)


def _bump_attempt(job_key: str, now: Optional[float] = None) -> int:
    now = now if now is not None else time.time()
    with _lock:
        state = _load_state()
        entry = state.get(job_key) or {}
        if now - float(entry.get("ts", 0)) > STATE_TTL_S:
            entry = {}
        n = int(entry.get("n", 0)) + 1
        state[job_key] = {"n": n, "ts": now}
        _save_state(state)
        return n


def _reset_attempts(job_key: str) -> None:
    with _lock:
        state = _load_state()
        if job_key in state:
            state.pop(job_key)
            _save_state(state)


# ---------- Adapter (in Tests ersetzbar) ----------
def _current_execution() -> Any:
    from cron.execution_identity import current_cron_execution
    return current_cron_execution()


def _hermes_home() -> str:
    from hermes_constants import get_hermes_home
    return str(get_hermes_home())


def _is_running(job_id: str) -> bool:
    from cron.scheduler import is_job_running
    return bool(is_job_running(job_id))


def _mark_error(home: str, job_id: str, message: str) -> None:
    from cron import jobs
    with jobs.use_cron_store(home):
        jobs.update_job(job_id, {"last_status": "error", "last_error": message})


def _trigger_retry(home: str, job_id: str, prompt: str) -> None:
    from cron import jobs
    with jobs.use_cron_store(home):
        if jobs.trigger_job(job_id, extra_prompt=prompt) is None:
            raise RuntimeError("Job nicht gefunden")


def _notify_operator(job_name: str, job_id: str, patterns: List[str]) -> None:
    """Nur der Betreiber, nie der Endnutzer: Eintrag in die Alert-Datei (best effort)."""
    line = (f"cron-meta-guard: Job '{job_name}' ({job_id}) lieferte nach Retry erneut eine "
            f"Meta-Antwort ({', '.join(patterns)}). Nicht zugestellt, kein weiterer Retry.")
    try:
        p = _path("CRON_META_GUARD_ALERT", _DEFAULT_ALERT)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + " " + line + "\n")
    except Exception as exc:
        logger.warning("cron-meta-guard: Alert-Datei nicht schreibbar: %s", exc)


# ---------- Nachlauf nach dem Run ----------
def _wait_until_finished(job_id: str, timeout_s: float, poll_s: float) -> None:
    deadline = time.time() + timeout_s
    time.sleep(poll_s)  # Hook feuert VOR Lieferung/mark_job_run: Lauf ist beim ersten Check noch aktiv
    while time.time() < deadline:
        try:
            if not _is_running(job_id):
                break
        except Exception:
            break
        time.sleep(poll_s)
    time.sleep(poll_s)  # mark_job_run abwarten


def _after_run(home: str, job_id: str, job_name: str, patterns: List[str], attempt: int,
               timeout_s: float = 900.0, poll_s: float = 2.0) -> Dict[str, Any]:
    """Statusmarkierung, Retry bzw. Eskalation. Gibt die Aktion zurueck (fuer Tests/Log)."""
    _wait_until_finished(job_id, timeout_s, poll_s)
    msg = (f"cron-meta-guard: Meta-Antwort unterdrueckt ({', '.join(patterns)}), "
           f"Versuch {attempt}/{MAX_ATTEMPTS}")
    result: Dict[str, Any] = {"job": job_id, "attempt": attempt, "patterns": patterns}
    try:
        _mark_error(home, job_id, msg)
        result["marked"] = True
    except Exception as exc:
        result["marked"] = False
        result["mark_error"] = str(exc)[:200]
    if attempt < MAX_ATTEMPTS:
        try:
            _trigger_retry(home, job_id, RETRY_PROMPT)
            result["action"] = "retry_triggered"
        except Exception as exc:
            result["action"] = "retry_failed"
            result["retry_error"] = str(exc)[:200]
            _notify_operator(job_name, job_id, patterns)
    else:
        result["action"] = "escalated_to_operator"
        _notify_operator(job_name, job_id, patterns)
    _log(result)
    return result


def _spawn(*args: Any) -> None:
    threading.Thread(target=_safe_after_run, args=args, daemon=True, name="cron-meta-guard").start()


def _safe_after_run(*args: Any) -> None:
    try:
        _after_run(*args)
    except Exception as exc:  # pragma: no cover
        logger.warning("cron-meta-guard: Nachlauf-Fehler: %s", exc)


# ---------- Hook ----------
def _on_transform_llm_output(response_text: str = "", **_: Any) -> Optional[str]:
    try:
        if _env_flag("CRON_META_GUARD_DISABLE"):
            return None
        ex = _current_execution()
        if ex is None:
            return None
        if is_allowlisted(ex):
            return None
        key = f"{ex.profile}:{ex.job_id}"
        patterns = find_meta_patterns(response_text)
        if not patterns:
            if isinstance(response_text, str) and response_text.strip():
                _reset_attempts(key)
            return None
        attempt = _bump_attempt(key)
        _log({"job": ex.job_id, "name": ex.job_name, "profile": ex.profile, "attempt": attempt,
              "patterns": patterns, "action": "suppressed"})
        _spawn(_hermes_home(), ex.job_id, ex.job_name, patterns, min(attempt, MAX_ATTEMPTS))
        return SILENT
    except Exception as exc:
        logger.warning("cron-meta-guard: fail-open: %s", exc)
        return None


def register(ctx) -> None:
    ctx.register_hook("transform_llm_output", _on_transform_llm_output)
