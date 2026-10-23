"""Tests for the cron-meta-guard plugin (stdlib unittest, runs without Hermes installed).

Run: python3 -m unittest tests.test_cron_meta_guard -v
"""
import importlib.util
import json
import os
import tempfile
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = os.path.join(ROOT, "plugins", "cron-meta-guard")

# Typical failure text: the agent answers the scheduler with an offer instead of the message.
META_TEXT = (
    "Ich stehe bereit, die Nachricht zu verfassen und zu liefern. Allerdings ist mir nicht klar, "
    "ob du m\u00f6chtest, dass ich sie jetzt sofort an den Nutzer schicke oder nur formuliere.\n\n"
    "Da dies ein Cron-Job ist, gehe ich davon aus, dass die Nachricht selbst die Deliverable ist:\n\n"
    "---\n\nKurzer Schluck-Check: heute schon genug getrunken? Glas Wasser jetzt zaehlt.\n\n---\n\n"
    "Falls du m\u00f6chtest, dass ich die Nachricht \u00fcber einen bestimmten Kanal "
    "verschicke, brauchte ich eine explizite Freigabe oder den genauen Kanal. Ansonsten ist sie oben fertig "
    "und wartet auf Delivery."
)

NUDGES = [
    "Kurzer Schluck-Check: heute schon genug getrunken? Glas Wasser jetzt zaehlt.",
    "Zeit f\u00fcr eine Bewegungspause: kurz aufstehen, strecken, drei Minuten laufen.",
    "Tablette-Check: schon genommen?",
    "Termin-Erinnerung in 30 Tagen, bitte Termin buchen.",
    "[SILENT]",
    "",
]

BRIEFINGS = [
    "Guten Morgen. Heute stehen drei Termine an, 10:00 Call, 14:00 Zahnarzt. "
    "Soll ich morgen frueher erinnern? Das kannst du mir im Chat sagen, ich passe es dann an.",
    "Tagesbriefing: Posteingang ruhig, 2 Mails mit Prio. Falls du moechtest, lege ich fuer Freitag "
    "einen Puffer im Kalender an. Sonst bleibt alles wie geplant.",
    "Wetter 14 Grad, Regen ab 16 Uhr. Die Reisekosten liegen bei 420 Euro, wenn du moechtest "
    "kann ich das noch aufteilen. Falls du moechtest Umbuchung, sag kurz Bescheid.",
    "Trinken-Nudge: Zeit fuer ein Glas Wasser. Falls du magst, nimm gleich zwei.",
]

ENV_KEYS = ("CRON_META_GUARD_LOG", "CRON_META_GUARD_STATE", "CRON_META_GUARD_ALERT",
            "CRON_META_GUARD_DISABLE", "CRON_META_GUARD_MAX_LEN",
            "CRON_META_GUARD_ALLOWLIST", "CRON_META_GUARD_ALLOWLIST_FILE")


def _load():
    spec = importlib.util.spec_from_file_location(
        "cron_meta_guard_under_test", os.path.join(PLUGIN_DIR, "__init__.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Base(unittest.TestCase):
    def setUp(self):
        self.m = _load()
        self.tmp = tempfile.mkdtemp()
        for k, f in (("CRON_META_GUARD_LOG", "g.log"), ("CRON_META_GUARD_STATE", "s.json"),
                     ("CRON_META_GUARD_ALERT", "a.log")):
            os.environ[k] = os.path.join(self.tmp, f)
        for k in ("CRON_META_GUARD_DISABLE", "CRON_META_GUARD_MAX_LEN",
                  "CRON_META_GUARD_ALLOWLIST", "CRON_META_GUARD_ALLOWLIST_FILE"):
            os.environ.pop(k, None)

    def tearDown(self):
        for k in ENV_KEYS:
            os.environ.pop(k, None)


class TestPatterns(Base):
    def test_meta_text_positive(self):
        got = self.m.find_meta_patterns(META_TEXT)
        for name in ("ich_stehe_bereit", "falls_du_moechtest", "explizite_freigabe", "ansonsten_oben_fertig"):
            self.assertIn(name, got)

    def test_nudges_negative(self):
        for t in NUDGES:
            self.assertEqual(self.m.find_meta_patterns(t), [], t)

    def test_soll_ich_cases(self):
        for t in ("Soll ich die Nachricht senden?", "Was soll ich tun?", "soll  ich das so lassen",
                  "Ich bin mir nicht sicher, ob du das lesen willst.",
                  "Falls du moechtest, schicke ich es.", "Ich stehe jetzt bereit."):
            self.assertTrue(self.m.find_meta_patterns(t), t)
        for t in ("Du sollst mich erinnern.", "Der Pilot soll Ichthyologie lernen.",
                  "Medikation: Das Rezept soll icheinreichen", "Trink bitte jetzt ein Glas Wasser."):
            self.assertEqual(self.m.find_meta_patterns(t), [], t)

    def test_long_reports_and_markers_ignored(self):
        self.assertEqual(self.m.find_meta_patterns("Bericht. " * 400 + " soll ich"), [])
        self.assertEqual(self.m.find_meta_patterns("[CRON_FAILURE]\nsoll ich"), [])
        self.assertEqual(self.m.find_meta_patterns(None), [])


class TestGating(Base):
    def test_single_pattern_in_running_text_is_clean(self):
        for t in BRIEFINGS:
            self.assertEqual(self.m.find_meta_patterns(t), [], t)

    def test_single_pattern_opening_is_positive(self):
        for t in ("Soll ich das jetzt senden?", "Falls du moechtest, schicke ich es an Telegram.",
                  "Ich stehe bereit. Heute 14 Uhr Zahnarzt.",
                  "Ich bin mir nicht sicher, ob du das lesen willst."):
            self.assertTrue(self.m.find_meta_patterns(t), t)

    def test_two_patterns_positive(self):
        t = ("Hier dein Briefing mit drei Punkten. Soll ich den Termin verschieben? "
             "Falls du moechtest, brauche ich eine explizite Freigabe.")
        self.assertGreaterEqual(len(self.m.find_meta_patterns(t)), 2)

    def test_meta_text_keeps_at_least_four_patterns(self):
        self.assertGreaterEqual(len(self.m.find_meta_patterns(META_TEXT)), 4)

    def test_briefing_flow_not_suppressed(self):
        m = self.m
        m._current_execution = lambda: types.SimpleNamespace(job_id="b1", job_name="Briefing", profile="assistant")
        m._hermes_home = lambda: "/nonexistent-home"
        m._job_is_no_agent = lambda home, jid: False
        for t in BRIEFINGS:
            self.assertIsNone(m._on_transform_llm_output(response_text=t), t)


class TestAllowlist(Base):
    def setUp(self):
        super().setUp()
        self.m._current_execution = lambda: types.SimpleNamespace(
            job_id="abc123", job_name="Morning-Briefing", profile="assistant")
        self.m._hermes_home = lambda: "/nonexistent-home"
        self.m._job_is_no_agent = lambda home, jid: False
        self.m._spawn = lambda *a: self.fail("must not trigger")
        os.environ["CRON_META_GUARD_ALLOWLIST_FILE"] = os.path.join(self.tmp, "none.json")

    def test_without_allowlist_job_is_checked(self):
        spawned = []
        self.m._spawn = lambda *a: spawned.append(a)
        self.assertEqual(self.m._on_transform_llm_output(response_text=META_TEXT), "[SILENT]")
        self.assertEqual(len(spawned), 1)

    def test_allowlist_env_name_id_profile_glob(self):
        for entry in ("abc123", "assistant:abc123", "morning-*", "Morning-Briefing"):
            os.environ["CRON_META_GUARD_ALLOWLIST"] = entry
            self.assertIsNone(self.m._on_transform_llm_output(response_text=META_TEXT), entry)

    def test_allowlist_file(self):
        p = os.path.join(self.tmp, "al.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"entries": ["abc123"]}, fh)
        os.environ["CRON_META_GUARD_ALLOWLIST_FILE"] = p
        self.assertIsNone(self.m._on_transform_llm_output(response_text=META_TEXT))

    def test_no_agent_script_job_is_skipped(self):
        self.m._job_is_no_agent = lambda home, jid: True
        self.assertIsNone(self.m._on_transform_llm_output(response_text=META_TEXT))

    def test_other_jobs_unaffected(self):
        os.environ["CRON_META_GUARD_ALLOWLIST"] = "another-job"
        spawned = []
        self.m._spawn = lambda *a: spawned.append(a)
        self.assertEqual(self.m._on_transform_llm_output(response_text=META_TEXT), "[SILENT]")

    def test_shipped_allowlist_is_valid_and_empty(self):
        with open(os.path.join(PLUGIN_DIR, "allowlist.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["entries"], [])


class TestFlow(Base):
    def setUp(self):
        super().setUp()
        m = self.m
        self.ex = types.SimpleNamespace(job_id="j1", job_name="Water-Nudge", profile="assistant")
        self.calls = []
        m._current_execution = lambda: self.ex
        m._hermes_home = lambda: "/nonexistent-home"
        m._job_is_no_agent = lambda home, jid: False
        m._is_running = lambda jid: False
        m._mark_error = lambda home, jid, msg: self.calls.append(("mark", jid, msg))
        m._trigger_retry = lambda home, jid, p: self.calls.append(("retry", jid, p))
        m._notify_operator = lambda name, jid, pats: self.calls.append(("notify", jid))
        os.environ["CRON_META_GUARD_ALLOWLIST_FILE"] = os.path.join(self.tmp, "none.json")
        # Run the follow-up synchronously and without waiting.
        m._spawn = lambda home, jid, name, pats, att: m._after_run(home, jid, name, pats, att, timeout_s=0, poll_s=0)

    def test_first_failure_silent_marked_retry(self):
        out = self.m._on_transform_llm_output(response_text=META_TEXT)
        self.assertEqual(out, "[SILENT]")
        kinds = [c[0] for c in self.calls]
        self.assertEqual(kinds, ["mark", "retry"])
        self.assertIn("NUR den Nachrichtentext", self.calls[1][2])
        self.assertNotIn("notify", kinds)

    def test_second_failure_operator_only_no_retry(self):
        self.m._on_transform_llm_output(response_text=META_TEXT)
        self.calls.clear()
        out = self.m._on_transform_llm_output(response_text="Soll ich das senden?")
        self.assertEqual(out, "[SILENT]")
        self.assertEqual([c[0] for c in self.calls], ["mark", "notify"])

    def test_third_run_no_retry_loop(self):
        for _ in range(2):
            self.m._on_transform_llm_output(response_text=META_TEXT)
        self.calls.clear()
        self.m._on_transform_llm_output(response_text=META_TEXT)
        self.assertNotIn("retry", [c[0] for c in self.calls])

    def test_clean_run_resets_counter(self):
        self.m._on_transform_llm_output(response_text=META_TEXT)
        self.assertIsNone(self.m._on_transform_llm_output(response_text=NUDGES[0]))
        self.calls.clear()
        self.m._on_transform_llm_output(response_text=META_TEXT)
        self.assertEqual([c[0] for c in self.calls], ["mark", "retry"])

    def test_normal_nudge_unchanged(self):
        for t in NUDGES:
            self.assertIsNone(self.m._on_transform_llm_output(response_text=t))
        self.assertEqual(self.calls, [])

    def test_no_cron_context_unchanged(self):
        self.m._current_execution = lambda: None
        self.assertIsNone(self.m._on_transform_llm_output(response_text=META_TEXT))
        self.assertEqual(self.calls, [])

    def test_kill_switch(self):
        os.environ["CRON_META_GUARD_DISABLE"] = "1"
        self.assertIsNone(self.m._on_transform_llm_output(response_text=META_TEXT))
        self.assertEqual(self.calls, [])

    def test_fail_open(self):
        def boom():
            raise RuntimeError("x")
        self.m._current_execution = boom
        self.assertIsNone(self.m._on_transform_llm_output(response_text=META_TEXT))

    def test_retry_failure_escalates(self):
        def bad(home, jid, p):
            raise RuntimeError("terminal")
        self.m._trigger_retry = bad
        self.m._on_transform_llm_output(response_text=META_TEXT)
        self.assertIn("notify", [c[0] for c in self.calls])

    def test_log_has_no_reply_text(self):
        self.m._on_transform_llm_output(response_text=META_TEXT)
        with open(os.environ["CRON_META_GUARD_LOG"], encoding="utf-8") as fh:
            raw = fh.read()
        self.assertNotIn("Schluck-Check", raw)
        self.assertTrue(all(json.loads(line) for line in raw.splitlines()))

    def test_alert_file_written_for_operator(self):
        m = _load()
        m._notify_operator("Water-Nudge", "j1", ["soll_ich"])
        with open(os.environ["CRON_META_GUARD_ALERT"], encoding="utf-8") as fh:
            self.assertIn("kein weiterer Retry", fh.read())

    def test_register(self):
        reg = []
        self.m.register(types.SimpleNamespace(register_hook=lambda n, f: reg.append(n)))
        self.assertEqual(reg, ["transform_llm_output"])


class TestRealCronStore(Base):
    """Real cron.jobs store in a temp dir. Skipped when the Hermes package is not importable."""

    def test_mark_and_retry_against_real_store(self):
        try:
            from cron import jobs
        except Exception:
            self.skipTest("hermes cron package not importable in this interpreter")
        home = tempfile.mkdtemp()
        with jobs.use_cron_store(home):
            job = jobs.create_job(prompt="Water nudge", schedule="0 11 * * 1-5", name="T")
        jid = job["id"]
        self.m._mark_error(home, jid, "cron-meta-guard: test")
        self.m._trigger_retry(home, jid, self.m.RETRY_PROMPT)
        with jobs.use_cron_store(home):
            j = jobs.get_job(jid)
        self.assertEqual(j["last_status"], "error")
        self.assertIn("cron-meta-guard", j["last_error"])
        self.assertIn("NUR den Nachrichtentext", j["manual_run_prompt"])


if __name__ == "__main__":
    unittest.main()
