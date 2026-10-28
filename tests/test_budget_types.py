"""Reject malformed budget values before any task can be created."""

import unittest

from machine.security.policy import AuthorizationDenied, CapabilityPolicy


class BudgetTypeTests(unittest.TestCase):
    def test_policy_rejects_boolean_and_non_numeric_limits(self) -> None:
        for value in (True, False, None, "0.05", 10**1000):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(ValueError):
                    CapabilityPolicy(frozenset({"health.check"}), value)

    def test_request_rejects_boolean_and_non_numeric_budgets(self) -> None:
        policy = CapabilityPolicy(frozenset({"health.check"}), 2.0)
        for value in (True, False, None, "0.01", 10**1000):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(AuthorizationDenied):
                    policy.assert_budget_allowed(value)

    def test_valid_int_and_float_budgets_remain_supported(self) -> None:
        policy = CapabilityPolicy(frozenset({"health.check"}), 2)
        for value in (1, 0.5, 2.0):
            with self.subTest(value=value):
                policy.assert_budget_allowed(value)


if __name__ == "__main__":
    unittest.main()
