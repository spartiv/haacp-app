"""Team list and "performed by" attribution on shared kitchen devices."""

from typing import Any

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, MembershipStatus
from tests.fakes import FakeEmailSender


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client: AsyncClient, email: str, name: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "supersecret123",
            "full_name": name,
            "organization_name": f"Org of {name}",
        },
    )
    return dict(response.json())


async def _invite_staff(
    client: AsyncClient, sender: FakeEmailSender, org_id: str, owner_token: str, name: str
) -> dict[str, Any]:
    email = f"{name.lower().replace(' ', '.')}@polton.ua"
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": email, "role": "staff"},
        headers=_auth(owner_token),
    )
    accept = await client.post(
        f"/api/v1/invites/{sender.sent[-1]['token']}/accept",
        json={"password": "brandnewpass123", "full_name": name},
    )
    return dict(accept.json())


async def _team(client: AsyncClient, sender: FakeEmailSender) -> dict[str, Any]:
    owner = await _signup(client, "owner@polton.ua", "Olena Owner")
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    cook = await _invite_staff(client, sender, org_id, owner_token, "Marko Cook")
    return {
        "org_id": org_id,
        "base": f"/api/v1/organizations/{org_id}",
        "owner_token": owner_token,
        "owner_id": owner["user"]["id"],
        "cook_token": cook["tokens"]["access_token"],
        "cook_id": cook["user"]["id"],
    }


async def test_members_lists_the_team_active_first(
    client: AsyncClient, fake_email_sender: FakeEmailSender, db_session: AsyncSession
) -> None:
    team = await _team(client, fake_email_sender)
    await db_session.execute(
        update(Membership)
        .where(Membership.user_id == team["owner_id"])
        .values(status=MembershipStatus.REMOVED)
    )
    await db_session.flush()

    response = await client.get(f"{team['base']}/members", headers=_auth(team["cook_token"]))

    assert response.status_code == 200
    members = response.json()
    assert [(m["full_name"], m["role"], m["status"]) for m in members] == [
        ("Marko Cook", "staff", "active"),
        ("Olena Owner", "owner", "removed"),
    ]


async def test_outsiders_cannot_list_members(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    team = await _team(client, fake_email_sender)
    outsider = await _signup(client, "other@cafe.ua", "Other Owner")

    response = await client.get(
        f"{team['base']}/members", headers=_auth(outsider["tokens"]["access_token"])
    )

    assert response.status_code == 403


async def test_check_records_account_and_performer_separately(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    team = await _team(client, fake_email_sender)
    item = await client.post(
        f"{team['base']}/controls/daily/checklist-items",
        json={"label": "Water OK"},
        headers=_auth(team["owner_token"]),
    )
    check = f"{team['base']}/controls/daily/items/{item.json()['id']}/check"

    # The shared device is signed in as the owner; the cook did the check.
    response = await client.post(
        check,
        json={"status": "pass", "performed_by_user_id": team["cook_id"]},
        headers=_auth(team["owner_token"]),
    )

    sheet_item = response.json()["items"][0]
    assert sheet_item["checked_by"]["full_name"] == "Olena Owner"
    assert sheet_item["performed_by"]["full_name"] == "Marko Cook"

    # Changing only the performer is a real change, logged in the audit trail.
    await client.post(check, json={"status": "pass"}, headers=_auth(team["owner_token"]))
    record_id = response.json()["record_id"]
    audit = await client.get(
        f"{team['base']}/control-records/{record_id}/audit-events",
        headers=_auth(team["owner_token"]),
    )
    events = audit.json()["items"]
    assert [e["performed_by"]["full_name"] for e in events] == ["Olena Owner", "Marko Cook"]
    assert {e["actor"]["full_name"] for e in events} == {"Olena Owner"}


async def test_performer_must_be_an_active_member(
    client: AsyncClient, fake_email_sender: FakeEmailSender, db_session: AsyncSession
) -> None:
    team = await _team(client, fake_email_sender)
    outsider = await _signup(client, "other@cafe.ua", "Other Owner")
    item = await client.post(
        f"{team['base']}/controls/daily/checklist-items",
        json={"label": "Water OK"},
        headers=_auth(team["owner_token"]),
    )
    check = f"{team['base']}/controls/daily/items/{item.json()['id']}/check"

    stranger = await client.post(
        check,
        json={"status": "pass", "performed_by_user_id": outsider["user"]["id"]},
        headers=_auth(team["owner_token"]),
    )
    assert stranger.status_code == 422
    assert stranger.json()["error"]["code"] == "invalid_performer"

    await db_session.execute(
        update(Membership)
        .where(Membership.user_id == team["cook_id"])
        .values(status=MembershipStatus.REMOVED)
    )
    await db_session.flush()
    removed = await client.post(
        check,
        json={"status": "pass", "performed_by_user_id": team["cook_id"]},
        headers=_auth(team["owner_token"]),
    )
    assert removed.json()["error"]["code"] == "invalid_performer"


async def test_event_entries_and_batches_record_the_performer(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    team = await _team(client, fake_email_sender)
    headers = _auth(team["owner_token"])
    types = (await client.get(f"{team['base']}/event-log-types", headers=headers)).json()
    glass = next(t for t in types if t["key"] == "glass")

    chosen = await client.post(
        f"{team['base']}/event-log-types/{glass['id']}/entries",
        json={
            "entry_date": "2026-10-01",
            "payload": {"details": "Склянка"},
            "performed_by_user_id": team["cook_id"],
        },
        headers=headers,
    )
    default = await client.post(
        f"{team['base']}/event-log-types/{glass['id']}/entries",
        json={"entry_date": "2026-10-01", "payload": {"details": "Тарілка"}},
        headers=headers,
    )
    assert (chosen.json()["responsible_user_id"], chosen.json()["performed_by_user_id"]) == (
        team["owner_id"],
        team["cook_id"],
    )
    assert default.json()["performed_by_user_id"] == team["owner_id"]

    product = await client.post(f"{team['base']}/products", json={"name": "Борщ"}, headers=headers)
    batch = await client.post(
        f"{team['base']}/products/{product.json()['id']}/batches",
        json={
            "number": "B-1",
            "production_date": "2026-10-01",
            "answers": [],
            "performed_by_user_id": team["cook_id"],
        },
        headers=headers,
    )
    assert batch.status_code == 201
    assert (batch.json()["signatory_user_id"], batch.json()["performed_by_user_id"]) == (
        team["owner_id"],
        team["cook_id"],
    )
