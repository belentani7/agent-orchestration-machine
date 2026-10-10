from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.message import EmailMessage
from enum import StrEnum
from pathlib import Path
import smtplib
import ssl
from typing import Protocol
from uuid import uuid4


class ContactBasis(StrEnum):
    OPT_IN = "opt_in"
    EXISTING_RELATIONSHIP = "existing_relationship"
    DOCUMENTED_LEGITIMATE_INTEREST = "documented_legitimate_interest"


class MessageStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class OutreachBlocked(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class Account:
    tenant_id: str
    name: str
    domain: str
    segment: str
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class Contact:
    tenant_id: str
    account_id: str
    email: str
    full_name: str
    role: str
    source: str
    contact_basis: ContactBasis
    contact_basis_recorded_at: datetime
    id: str = field(default_factory=lambda: str(uuid4()))
    do_not_contact: bool = False
    bounced: bool = False

    @property
    def eligible(self) -> bool:
        return bool(self.email and self.source and self.contact_basis_recorded_at) and not self.do_not_contact and not self.bounced


@dataclass(slots=True)
class Proposal:
    tenant_id: str
    account_id: str
    subject: str
    body: str
    value_proposition: str
    id: str = field(default_factory=lambda: str(uuid4()))
    approved_by: str | None = None
    approved_at: datetime | None = None

    @property
    def approved(self) -> bool:
        return bool(self.approved_by and self.approved_at)


@dataclass(slots=True)
class OutreachMessage:
    tenant_id: str
    contact_id: str
    proposal_id: str
    channel: str
    recipient: str
    subject: str
    body: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: MessageStatus = MessageStatus.DRAFT
    provider_message_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    sent_at: datetime | None = None


class DeliveryGateway(Protocol):
    def deliver(self, message: OutreachMessage) -> str: ...


class SmtpDeliveryGateway:
    """Adaptador real de entrega. Los secretos se reciben desde el entorno de ejecución."""

    def __init__(self, host: str, port: int, username: str, password: str, sender: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender

    def deliver(self, message: OutreachMessage) -> str:
        email = EmailMessage()
        email["From"] = self._sender
        email["To"] = message.recipient
        email["Subject"] = message.subject
        email["Message-ID"] = f"<{message.id}@orchestration-machine.local>"
        email.set_content(message.body)
        context = ssl.create_default_context()
        with smtplib.SMTP(self._host, self._port, timeout=30) as client:
            client.starttls(context=context)
            client.login(self._username, self._password)
            client.send_message(email)
        return str(email["Message-ID"])


class FileDeliveryGateway:
    """Entrega de ensayo: escribe mensajes RFC-822, sin comunicación externa."""

    def __init__(self, outbox_directory: Path) -> None:
        self._directory = outbox_directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def deliver(self, message: OutreachMessage) -> str:
        filename = self._directory / f"{message.id}.eml"
        content = f"To: {message.recipient}\nSubject: {message.subject}\n\n{message.body}\n"
        filename.write_text(content, encoding="utf-8")
        return f"file://{filename}"


class InMemoryOutreachRepository:
    def __init__(self) -> None:
        self.contacts: dict[str, Contact] = {}
        self.proposals: dict[str, Proposal] = {}
        self.messages: dict[str, OutreachMessage] = {}
        self.events: list[dict[str, str]] = []

    def record(self, event: str, tenant_id: str, resource_id: str, detail: str) -> None:
        self.events.append({
            "event": event,
            "tenant_id": tenant_id,
            "resource_id": resource_id,
            "detail": detail,
            "occurred_at": datetime.now(UTC).isoformat(),
        })


class CommercialOperations:
    """Caso de uso comercial que centraliza admisión, aprobación, cuota y entrega."""

    def __init__(self, repository: InMemoryOutreachRepository, daily_limit: int = 50) -> None:
        if daily_limit < 1:
            raise ValueError("La cuota diaria debe ser positiva")
        self._repository = repository
        self._daily_limit = daily_limit

    def accept_contact(self, contact: Contact) -> Contact:
        if not contact.tenant_id or not contact.account_id or not contact.email or "@" not in contact.email:
            raise ValueError("El contacto requiere tenant, cuenta y correo válido")
        if not contact.source.strip():
            raise ValueError("El contacto requiere un origen documentado")
        if contact.contact_basis_recorded_at.tzinfo is None:
            raise ValueError("La fecha de base de contacto debe incluir zona horaria")
        self._repository.contacts[contact.id] = contact
        self._repository.record("contact.accepted", contact.tenant_id, contact.id, contact.contact_basis.value)
        return contact

    def suppress_contact(self, contact_id: str, reason: str) -> Contact:
        contact = self._repository.contacts[contact_id]
        contact.do_not_contact = True
        self._repository.record("contact.suppressed", contact.tenant_id, contact.id, reason)
        return contact

    def create_proposal(self, tenant_id: str, account_id: str, recipient_name: str, value_proposition: str) -> Proposal:
        if not value_proposition.strip():
            raise ValueError("La proposición de valor es obligatoria")
        subject = f"Propuesta para {recipient_name}"
        body = (
            f"Hola {recipient_name},\n\n"
            f"Hemos preparado una propuesta centrada en: {value_proposition.strip()}.\n\n"
            "Si consideras que es relevante, podemos compartir el alcance y los siguientes pasos. "
            "Si prefieres no recibir más comunicaciones, indícalo y respetaremos tu decisión.\n\n"
            "Saludos,\nEquipo comercial"
        )
        proposal = Proposal(tenant_id, account_id, subject, body, value_proposition)
        self._repository.proposals[proposal.id] = proposal
        self._repository.record("proposal.created", tenant_id, proposal.id, account_id)
        return proposal

    def approve_proposal(self, proposal_id: str, approver_id: str) -> Proposal:
        if not approver_id.strip():
            raise ValueError("El aprobador es obligatorio")
        proposal = self._repository.proposals[proposal_id]
        proposal.approved_by = approver_id
        proposal.approved_at = datetime.now(UTC)
        self._repository.record("proposal.approved", proposal.tenant_id, proposal.id, approver_id)
        return proposal

    def prepare_message(self, contact_id: str, proposal_id: str, channel: str = "email") -> OutreachMessage:
        contact = self._repository.contacts[contact_id]
        proposal = self._repository.proposals[proposal_id]
        if contact.tenant_id != proposal.tenant_id or contact.account_id != proposal.account_id:
            raise OutreachBlocked("El contacto y la propuesta deben pertenecer a la misma cuenta y tenant")
        if not contact.eligible:
            raise OutreachBlocked("Contacto suprimido, rebotado o sin requisitos de contacto")
        if not proposal.approved:
            raise OutreachBlocked("La propuesta requiere aprobación antes de programarse")
        message = OutreachMessage(
            tenant_id=contact.tenant_id,
            contact_id=contact.id,
            proposal_id=proposal.id,
            channel=channel,
            recipient=contact.email,
            subject=proposal.subject,
            body=proposal.body,
            status=MessageStatus.READY,
        )
        self._repository.messages[message.id] = message
        self._repository.record("outreach.ready", message.tenant_id, message.id, channel)
        return message

    def deliver_ready(self, message_id: str, gateway: DeliveryGateway) -> OutreachMessage:
        message = self._repository.messages[message_id]
        contact = self._repository.contacts[message.contact_id]
        proposal = self._repository.proposals[message.proposal_id]
        try:
            self._assert_deliverable(message, contact, proposal)
            message.provider_message_id = gateway.deliver(message)
            message.status = MessageStatus.SENT
            message.sent_at = datetime.now(UTC)
            self._repository.record("outreach.sent", message.tenant_id, message.id, message.provider_message_id)
        except Exception as error:
            message.status = MessageStatus.SUPPRESSED if isinstance(error, OutreachBlocked) else MessageStatus.FAILED
            message.error = str(error)
            self._repository.record("outreach.blocked", message.tenant_id, message.id, type(error).__name__)
        return message

    def _assert_deliverable(self, message: OutreachMessage, contact: Contact, proposal: Proposal) -> None:
        if message.status != MessageStatus.READY:
            raise OutreachBlocked("El mensaje no está listo para entrega")
        if not contact.eligible:
            raise OutreachBlocked("El contacto ya no es elegible")
        if not proposal.approved:
            raise OutreachBlocked("La propuesta dejó de estar aprobada")
        sent_today = sum(
            1 for item in self._repository.messages.values()
            if item.tenant_id == message.tenant_id and item.channel == message.channel and item.status == MessageStatus.SENT
            and item.sent_at is not None and item.sent_at.date() == datetime.now(UTC).date()
        )
        if sent_today >= self._daily_limit:
            raise OutreachBlocked("Se alcanzó la cuota diaria del tenant y canal")
