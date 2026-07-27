import logging

import pytest

from app.models import MembershipRole
from app.services.email_sender import LoggingEmailSender, get_email_sender


async def test_logging_email_sender_logs_the_invite(caplog: pytest.LogCaptureFixture) -> None:
    sender = LoggingEmailSender()

    with caplog.at_level(logging.INFO, logger="app.email"):
        await sender.send_invite(
            to_email="staffer@polton.ua",
            organization_name="Polton",
            role=MembershipRole.STAFF,
            token="some-token",
        )

    assert "staffer@polton.ua" in caplog.text
    assert "some-token" in caplog.text


def test_get_email_sender_returns_a_singleton() -> None:
    assert get_email_sender() is get_email_sender()
