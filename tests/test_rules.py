import unittest

from retention_checker.model import Log, LogGroup
from retention_checker.rules import (
    exit_code,
    rule_empty_group,
    rule_invalid_retention,
    rule_prod_min_retention,
    rule_unset_retention,
    run_all,
)


def group(name="g", prod=False, logs=()):
    return LogGroup(name=name, tags={"tier": "prod"} if prod else {"tier": "dev"}, logs=tuple(logs))


def log(name="l", days=180):
    return Log(name=name, retention_days=days, log_type="CUSTOM")


class TestLog001(unittest.TestCase):
    def test_fires_prod_at_minimum(self):
        out = rule_prod_min_retention((group(prod=True, logs=[log(days=30)]),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_quiet_dev_at_minimum(self):
        self.assertEqual(rule_prod_min_retention((group(prod=False, logs=[log(days=30)]),)), [])

    def test_quiet_prod_at_180(self):
        self.assertEqual(rule_prod_min_retention((group(prod=True, logs=[log(days=180)]),)), [])


class TestLog002(unittest.TestCase):
    def test_fires_off_ladder(self):
        out = rule_invalid_retention((group(logs=[log(days=45)]),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_fires_above_max(self):
        self.assertEqual(len(rule_invalid_retention((group(logs=[log(days=210)]),))), 1)

    def test_all_valid_rungs_quiet(self):
        for d in (30, 60, 90, 120, 150, 180):
            self.assertEqual(rule_invalid_retention((group(logs=[log(days=d)]),)), [])

    def test_unset_not_invalid(self):
        self.assertEqual(rule_invalid_retention((group(logs=[log(days=None)]),)), [])


class TestLog003(unittest.TestCase):
    def test_fires_unset(self):
        out = rule_unset_retention((group(logs=[log(days=None)]),))
        self.assertEqual(len(out), 1)
        self.assertIn("default", out[0].detail)

    def test_set_quiet(self):
        self.assertEqual(rule_unset_retention((group(logs=[log(days=60)]),)), [])


class TestLog004(unittest.TestCase):
    def test_fires_empty_group(self):
        out = rule_empty_group((group(),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "LOW")

    def test_nonempty_quiet(self):
        self.assertEqual(rule_empty_group((group(logs=[log()]),)), [])


class TestAggregation(unittest.TestCase):
    def test_exit_2_on_high(self):
        self.assertEqual(exit_code(run_all((group(prod=True, logs=[log(days=30)]),))), 2)

    def test_exit_1_medium_only(self):
        self.assertEqual(exit_code(run_all((group(logs=[log(days=45)]),))), 1)

    def test_exit_0_clean(self):
        self.assertEqual(exit_code(run_all((group(prod=True, logs=[log(days=180)]),))), 0)


if __name__ == "__main__":
    unittest.main()
