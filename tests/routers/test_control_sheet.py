from datetime import date, timedelta
from typing import Any

from httpx import AsyncClient

from tests.fakes import FakeEmailSender

UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client: AsyncClient, email: str = "owner@polton.ua") -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "supersecret123",
            "full_name": "Olena Polishchuk",
            "organization_name": "Polton",
        },
    )
    return dict(response.json())


async def _add_items(client: AsyncClient, org_id: str, token: str, labels: list[str]) -> list[str]:
    ids = []
    for label in labels:
        response = await client.post(
            f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
            json={"label": label},
            headers=_auth(token),
        )
        ids.append(response.json()["id"])
    return ids


async def _make_staff(
    client: AsyncClient, fake_email_sender: FakeEmailSender, org_id: str, owner_token: str
) -> str:
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth(owner_token),
    )
    token = fake_email_sender.sent[-1]["token"]
    accept = await client.post(
        f"/api/v1/invites/{token}/accept",
        json={"password": "brandnewpass123", "full_name": "New Staffer"},
    )
    return str(accept.json()["tokens"]["access_token"])


async def test_full_daily_sheet_workflow(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    staff_token = await _make_staff(client, fake_email_sender, org_id, owner_token)
    water, pests = await _add_items(client, org_id, owner_token, ["Water OK", "No pests"])
    base = f"/api/v1/organizations/{org_id}"

    # Empty sheet: 200, everything pending, no record yet.
    empty = await client.get(f"{base}/controls/daily/sheet", headers=_auth(staff_token))
    assert empty.status_code == 200
    assert empty.json()["record_id"] is None
    assert [i["status"] for i in empty.json()["items"]] == ["pending", "pending"]

    # Deviation without a corrective action is rejected.
    rejected = await client.post(
        f"{base}/controls/daily/items/{water}/check",
        json={"status": "deviation"},
        headers=_auth(staff_token),
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "corrective_action_required"

    # Staff checks one item as a deviation, with a corrective action.
    checked = await client.post(
        f"{base}/controls/daily/items/{water}/check",
        json={"status": "deviation", "corrective_action": "Flushed line, re-tested: OK"},
        headers=_auth(staff_token),
    )
    assert checked.status_code == 200
    sheet = checked.json()
    record_id = sheet["record_id"]
    assert sheet["status"] == "draft"
    assert sheet["has_deviation"] is True
    assert sheet["items"][0]["checked_by"]["full_name"] == "New Staffer"

    # Submitting with an item still pending lists what's missing.
    incomplete = await client.post(
        f"{base}/control-records/{record_id}/submit", headers=_auth(staff_token)
    )
    assert incomplete.status_code == 409
    assert incomplete.json()["error"]["code"] == "control_record_incomplete"
    assert incomplete.json()["error"]["details"] == [
        {"control_checklist_item_id": pests, "label": "No pests"}
    ]

    await client.post(
        f"{base}/controls/daily/items/{pests}/check",
        json={"status": "pass"},
        headers=_auth(staff_token),
    )
    submitted = await client.post(
        f"{base}/control-records/{record_id}/submit", headers=_auth(staff_token)
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted"
    assert submitted.json()["submitted_by"]["full_name"] == "New Staffer"

    # After submission, changes need a reason.
    no_reason = await client.post(
        f"{base}/controls/daily/items/{pests}/check",
        json={"status": "deviation", "corrective_action": "Called pest control"},
        headers=_auth(owner_token),
    )
    assert no_reason.status_code == 422
    assert no_reason.json()["error"]["code"] == "amendment_reason_required"

    amended = await client.post(
        f"{base}/controls/daily/items/{pests}/check",
        json={
            "status": "deviation",
            "corrective_action": "Called pest control",
            "amendment_reason": "Droppings found later in dry store",
        },
        headers=_auth(owner_token),
    )
    assert amended.status_code == 200

    # The audit log has every step, newest first, with names and server timestamps.
    log = await client.get(
        f"{base}/control-records/{record_id}/audit-events", headers=_auth(staff_token)
    )
    assert log.status_code == 200
    events = log.json()["items"]
    assert [(e["event_type"], e["item_label"], e["new_status"]) for e in events] == [
        ("item_amended", "No pests", "deviation"),
        ("record_submitted", None, None),
        ("item_checked", "No pests", "pass"),
        ("item_checked", "Water OK", "deviation"),
    ]
    assert events[0]["actor"]["full_name"] == "Olena Polishchuk"
    assert events[0]["previous_status"] == "pass"
    assert events[0]["amendment_reason"] == "Droppings found later in dry store"
    assert events[3]["corrective_action"] == "Flushed line, re-tested: OK"
    assert log.json()["next_cursor"] is None

    # Submitting twice is rejected.
    again = await client.post(
        f"{base}/control-records/{record_id}/submit", headers=_auth(owner_token)
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "control_record_already_submitted"


async def test_audit_events_pagination_over_http(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_ids = await _add_items(client, org_id, token, ["Q1", "Q2", "Q3"])
    base = f"/api/v1/organizations/{org_id}"
    for item_id in item_ids:
        response = await client.post(
            f"{base}/controls/daily/items/{item_id}/check",
            json={"status": "pass"},
            headers=_auth(token),
        )
    record_id = response.json()["record_id"]

    first = await client.get(
        f"{base}/control-records/{record_id}/audit-events",
        params={"limit": 2},
        headers=_auth(token),
    )
    assert [e["item_label"] for e in first.json()["items"]] == ["Q3", "Q2"]
    second = await client.get(
        f"{base}/control-records/{record_id}/audit-events",
        params={"limit": 2, "cursor": first.json()["next_cursor"]},
        headers=_auth(token),
    )
    assert [e["item_label"] for e in second.json()["items"]] == ["Q1"]
    assert second.json()["next_cursor"] is None

    bad_cursor = await client.get(
        f"{base}/control-records/{record_id}/audit-events",
        params={"cursor": "not-a-number"},
        headers=_auth(token),
    )
    assert bad_cursor.status_code == 422
    assert bad_cursor.json()["error"]["code"] == "invalid_cursor"


async def test_sheet_for_a_specific_date_and_future_date(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    [item_id] = await _add_items(client, org_id, token, ["Q1"])
    base = f"/api/v1/organizations/{org_id}"
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    await client.post(
        f"{base}/controls/daily/items/{item_id}/check",
        json={"status": "pass", "period_date": yesterday},
        headers=_auth(token),
    )
    past = await client.get(
        f"{base}/controls/daily/sheet", params={"date": yesterday}, headers=_auth(token)
    )
    assert past.json()["period_date"] == yesterday
    assert past.json()["items"][0]["status"] == "pass"

    future = await client.get(
        f"{base}/controls/daily/sheet",
        params={"date": (date.today() + timedelta(days=3)).isoformat()},
        headers=_auth(token),
    )
    assert future.status_code == 422
    assert future.json()["error"]["code"] == "future_period_date"


async def test_sheet_endpoints_are_scoped_to_members(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    [item_id] = await _add_items(client, org_id, token, ["Q1"])
    outsider = await _signup(client, email="other@elsewhere.ua")
    outsider_token = outsider["tokens"]["access_token"]
    base = f"/api/v1/organizations/{org_id}"

    sheet = await client.get(f"{base}/controls/daily/sheet", headers=_auth(outsider_token))
    check = await client.post(
        f"{base}/controls/daily/items/{item_id}/check",
        json={"status": "pass"},
        headers=_auth(outsider_token),
    )
    assert sheet.status_code == 403
    assert check.status_code == 403

    # A record id from another organization looks like it doesn't exist.
    outsider_base = f"/api/v1/organizations/{outsider['organization_id']}"
    owner_check = await client.post(
        f"{base}/controls/daily/items/{item_id}/check",
        json={"status": "pass"},
        headers=_auth(token),
    )
    record_id = owner_check.json()["record_id"]
    foreign = await client.get(
        f"{outsider_base}/control-records/{record_id}/audit-events", headers=_auth(outsider_token)
    )
    assert foreign.status_code == 404
    assert foreign.json()["error"]["code"] == "control_record_not_found"

    unknown_item = await client.post(
        f"{base}/controls/daily/items/{UNKNOWN_ID}/check",
        json={"status": "pass"},
        headers=_auth(token),
    )
    assert unknown_item.status_code == 404
    assert unknown_item.json()["error"]["code"] == "control_checklist_item_not_found"

    invalid_status = await client.post(
        f"{base}/controls/daily/items/{item_id}/check",
        json={"status": "pending"},
        headers=_auth(token),
    )
    assert invalid_status.status_code == 422
    assert invalid_status.json()["error"]["code"] == "validation_error"
