from app.models import MembershipRole


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send_invite(
        self, *, to_email: str, organization_name: str, role: MembershipRole, token: str
    ) -> None:
        self.sent.append(
            {
                "to_email": to_email,
                "organization_name": organization_name,
                "role": role.value,
                "token": token,
            }
        )
