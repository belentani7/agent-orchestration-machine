import unittest

from machine.bootstrap import build_machine
from machine.domain.models import TaskRequest, TaskStatus, TenantContext
from machine.infrastructure.repositories import TenantIsolationViolation
from machine.security.policy import AuthorizationDenied, CapabilityPolicy


class MachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator, self.audit, self.repository = build_machine()
        self.context = TenantContext("tenant-a", "actor-a")

    def test_successful_inference_is_audited(self) -> None:
        task = self.orchestrator.submit(
            self.context,
            TaskRequest("text.infer", {"prompt": "hola"}, 0.01),
        )
        self.assertEqual(TaskStatus.SUCCEEDED, task.status)
        self.assertEqual("local-primary", task.result["outputs"][0]["provider"])
        self.assertEqual(
            ["task.created", "task.planned", "task.running", "step.succeeded", "task.succeeded"],
            [event["name"] for event in self.audit.records_for("tenant-a", task.id)],
        )

    def test_unauthorized_capability_fails_without_execution(self) -> None:
        task = self.orchestrator.submit(self.context, TaskRequest("files.delete", {}, 0.01))
        self.assertEqual(TaskStatus.FAILED, task.status)
        self.assertIn("Capacidad denegada", task.error)

    def test_tenant_repository_rejects_cross_tenant_reads(self) -> None:
        task = self.orchestrator.submit(self.context, TaskRequest("health.check", {}, 0.01))
        with self.assertRaises(TenantIsolationViolation):
            self.repository.get("tenant-b", task.id)

    def test_invalid_tenant_or_actor_is_rejected_before_persistence(self) -> None:
        invalid_principals = (
            TenantContext("", "actor-a"),
            TenantContext("   ", "actor-a"),
            TenantContext("tenant-a", ""),
            TenantContext("tenant-a", "   "),
        )
        for principal in invalid_principals:
            with self.subTest(principal=principal):
                with self.assertRaises(AuthorizationDenied):
                    self.orchestrator.submit(
                        principal, TaskRequest("health.check", {}, 0.01)
                    )
        # Invalid principals must not create any persisted tasks.
        self.assertEqual({}, self.repository._tasks)

    def test_budget_policy_rejects_excess(self) -> None:
        with self.assertRaises(AuthorizationDenied):
            self.orchestrator.submit(self.context, TaskRequest("health.check", {}, 0.50))

    def test_budget_policy_rejects_non_finite_requests(self) -> None:
        for budget in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(budget=budget):
                with self.assertRaises(AuthorizationDenied):
                    self.orchestrator.submit(self.context, TaskRequest("health.check", {}, budget))

    def test_budget_policy_rejects_non_finite_limits(self) -> None:
        for limit in (float("nan"), float("inf"), float("-inf"), 0.0, -0.01):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    CapabilityPolicy(frozenset({"health.check"}), limit)


if __name__ == "__main__":
    unittest.main()
