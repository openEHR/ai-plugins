"""Unit tests for the screener skill's pure helpers (no network)."""
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent.parent / "plugins" / "openehr-specs" / "skills" / "screener"
          / "scripts" / "screener.py")
spec = importlib.util.spec_from_file_location("screener", SCRIPT)
screener = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screener)

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
NEEDS = {"fix": 1, "minor": 2, "major": 3}
WAIT = {"minor": 7}


def days_ago(n):
    return NOW - timedelta(days=n)


def ready(level, approvals, changes=(), draft=False, conflicting=False, checks="SUCCESS"):
    return screener.readiness(level, list(approvals), list(changes), draft, conflicting, checks, NOW, NEEDS, WAIT)


class ReadinessTest(unittest.TestCase):
    def test_fix_needs_one_approval(self):
        self.assertEqual(ready("fix", [])[0], "OPEN")
        self.assertEqual(ready("fix", [days_ago(0)])[0], "READY")

    def test_minor_needs_two_approvals_and_a_week(self):
        self.assertEqual(ready("minor", [days_ago(30)])[0], "OPEN")
        self.assertEqual(ready("minor", [days_ago(30), days_ago(3)])[0], "WAIT")
        self.assertEqual(ready("minor", [days_ago(30), days_ago(8)])[0], "READY")

    def test_week_counts_from_the_approval_that_completes_the_set(self):
        # three approvals: the second one, not the latest, starts the week
        state, reason = ready("minor", [days_ago(20), days_ago(9), days_ago(1)])
        self.assertEqual(state, "READY")
        self.assertIn(str(days_ago(9).date()), reason)

    def test_change_request_needs_three_and_no_week(self):
        self.assertEqual(ready("major", [days_ago(1), days_ago(1)])[0], "OPEN")
        self.assertEqual(ready("major", [days_ago(0)] * 3)[0], "READY")

    def test_blockers_win_over_approvals(self):
        full = [days_ago(10), days_ago(9)]
        self.assertEqual(ready("minor", full, changes=["x"]), ("OPEN", "changes requested by x"))
        self.assertEqual(ready("minor", full, draft=True), ("OPEN", "draft"))
        self.assertEqual(ready("minor", full, conflicting=True), ("OPEN", "merge conflict"))
        self.assertEqual(ready("minor", full, checks="FAILURE"), ("OPEN", "checks failing"))
        self.assertEqual(ready("minor", full, checks="PENDING"), ("OPEN", "checks still running"))

    def test_no_label_is_never_ready(self):
        state, reason = ready(None, [days_ago(1)] * 3)
        self.assertEqual(state, "OPEN")
        self.assertIn("no level label", reason)

    def test_no_checks_configured_does_not_block(self):
        self.assertEqual(ready("fix", [days_ago(0)], checks=None)[0], "READY")


class HelpersTest(unittest.TestCase):
    def test_ticket_keys(self):
        self.assertEqual(screener.ticket_keys("SPECPR-12/SPECAM-3: x", "fixes SPECPR-12, see SEC-39 and SPEC-7"),
                         ["SPECPR-12", "SPECAM-3", "SPEC-7"])
        self.assertEqual(screener.ticket_keys(None, ""), [])

    def test_level_of(self):
        self.assertEqual(screener.level_of(["Minor", "docs"], NEEDS), "minor")
        self.assertIsNone(screener.level_of(["docs"], NEEDS))
        self.assertIsNone(screener.level_of(["fix", "minor"], NEEDS))

    def test_asks_something(self):
        self.assertTrue(screener.asks_something("@x is this still relevant"))
        self.assertTrue(screener.asks_something("@x"))
        self.assertFalse(screener.asks_something("I agree with what @x wrote in the earlier ticket."))

    def test_norm(self):
        self.assertEqual(screener.norm("  Diego  Boscá "), "diego bosca")
        self.assertEqual(screener.norm(None), "")


if __name__ == "__main__":
    unittest.main()
