from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from machine.commercial import (
    Account,
    CommercialOperations,
    Contact,
    ContactBasis,
    FileDeliveryGateway,
    InMemoryOutreachRepository,
    MessageStatus,
    OutreachBlocked,
)


class CommercialOperationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryOutreachRepository()
        self.operations = CommercialOperations(self.repository, daily_limit=1)
        self.account = Account("tenant-a", "Cuenta A", "cuenta-a.test", "software")
        self.contact = self.operations.accept_contact(Contact(
            tenant_id="tenant-a",
            account_id=self.account.id,
            email="contacto@cuenta-a.test",
            full_name="Ana Cliente",
            role="Dirección",
            source="importación autorizada",
            contact_basis=ContactBasis.OPT_IN,
            contact_basis_recorded_at=datetime.now(UTC),
        ))

    def _approved_proposal(self):
        proposal = self.operations.create_proposal("tenant-a", self.account.id, "Ana", "reducir trabajo operativo")
        return self.operations.approve_proposal(proposal.id, "manager-a")

    def test_approved_eligible_contact_is_delivered_to_file_outbox(self) -> None:
        proposal = self._approved_proposal()
        message = self.operations.prepare_message(self.contact.id, proposal.id)
        with TemporaryDirectory() as directory:
            delivered = self.operations.deliver_ready(message.id, FileDeliveryGateway(Path(directory)))
            self.assertEqual(MessageStatus.SENT, delivered.status)
            self.assertTrue(Path(delivered.provider_message_id.removeprefix("file://")).exists())

    def test_suppression_blocks_delivery(self) -> None:
        proposal = self._approved_proposal()
        message = self.operations.prepare_message(self.contact.id, proposal.id)
        self.operations.suppress_contact(self.contact.id, "baja solicitada")
        delivered = self.operations.deliver_ready(message.id, FileDeliveryGateway(Path("/tmp/outbox-test")))
        self.assertEqual(MessageStatus.SUPPRESSED, delivered.status)

    def test_unapproved_proposal_is_not_queued(self) -> None:
        proposal = self.operations.create_proposal("tenant-a", self.account.id, "Ana", "reducir trabajo operativo")
        with self.assertRaises(OutreachBlocked):
            self.operations.prepare_message(self.contact.id, proposal.id)

    def test_daily_limit_blocks_second_delivery(self) -> None:
        first = self._approved_proposal()
        first_message = self.operations.prepare_message(self.contact.id, first.id)
        with TemporaryDirectory() as directory:
            self.operations.deliver_ready(first_message.id, FileDeliveryGateway(Path(directory)))
            second = self._approved_proposal()
            second_message = self.operations.prepare_message(self.contact.id, second.id)
            delivered = self.operations.deliver_ready(second_message.id, FileDeliveryGateway(Path(directory)))
        self.assertEqual(MessageStatus.SUPPRESSED, delivered.status)


if __name__ == "__main__":
    unittest.main()
