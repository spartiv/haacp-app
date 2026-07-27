import logging
from typing import Protocol

from app.models import MembershipRole

logger = logging.getLogger("app.email")


class EmailSender(Protocol):
    async def send_invite(
        self, *, to_email: str, organization_name: str, role: MembershipRole, token: str
    ) -> None: ...


class LoggingEmailSender:
    """Dev/test stub: logs the invite instead of sending real email.

    Swappable for a real provider (SES, SendGrid, ...) later without touching
    any calling code, since callers only depend on the EmailSender protocol.
    """

    async def send_invite(
        self, *, to_email: str, organization_name: str, role: MembershipRole, token: str
    ) -> None:
        logger.info(
            "Invite email (stub, not actually sent): to=%s organization=%r role=%s token=%s",
            to_email,
            organization_name,
            role.value,
            token,
        )


_default_email_sender = LoggingEmailSender()


def get_email_sender() -> EmailSender:
    return _default_email_sender
