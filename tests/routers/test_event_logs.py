from httpx import AsyncClient

from tests.fakes import FakeEmailSender


async def _signup(client: AsyncClient, **overrides: str) -> dict:
    payload = {
        "email": "owner@polton.ua",
        "password": "supersecret123",
        "full_name": "Olena Polishchuk",
        "organization_name": "Polton",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/auth/signup", json=payload)
    return response.json()


def _auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def _make_staff(
    client: AsyncClient, fake_email_sender: FakeEmailSender, org_id: str, owner_token: str
) -> str:
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(owner_token),
    )
    token = fake_email_sender.sent[-1]["token"]
    accept = await client.post(
        f"/api/v1/invites/{token}/accept",
        json={"password": "brandnewpass123", "full_name": "New Staffer"},
    )
    return accept.json()["tokens"]["access_token"]


async def test_list_event_log_types_returns_all_9(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/event-log-types", headers=_auth_header(token)
    )

    assert response.status_code == 200
    log_types = response.json()
    assert len(log_types) == 9
    assert log_types[0]["log_schema"] == "standard"
    water = next(t for t in log_types if t["key"] == "water")
    assert water["log_schema"] == "water"


async def test_staff_can_record_and_list_water_entries(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    staff_token = await _make_staff(client, fake_email_sender, org_id, owner_token)
    log_types_response = await client.get(
        f"/api/v1/organizations/{org_id}/event-log-types", headers=_auth_header(owner_token)
    )
    water_type_id = next(t["id"] for t in log_types_response.json() if t["key"] == "water")

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/event-log-types/{water_type_id}/entries",
        json={
            "entry_date": "2026-07-05",
            "payload": {"params": ["pH", "Мікробіологія"], "result": "ok"},
        },
        headers=_auth_header(staff_token),
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["has_deviation"] is False
    assert body["responsible_user_id"]

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/event-log-types/{water_type_id}/entries",
        headers=_auth_header(staff_token),
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_record_entry_rejects_invalid_payload(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    log_types_response = await client.get(
        f"/api/v1/organizations/{org_id}/event-log-types", headers=_auth_header(token)
    )
    pests_type_id = next(t["id"] for t in log_types_response.json() if t["key"] == "pests")

    response = await client.post(
        f"/api/v1/organizations/{org_id}/event-log-types/{pests_type_id}/entries",
        json={"entry_date": "2026-07-08", "payload": {"detected": "maybe", "actions": ""}},
        headers=_auth_header(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_event_payload"


async def test_record_entry_for_unknown_log_type_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.post(
        f"/api/v1/organizations/{org_id}/event-log-types/"
        "00000000-0000-0000-0000-000000000000/entries",
        json={"entry_date": "2026-07-08", "payload": {}},
        headers=_auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "event_log_type_not_found"


async def test_delete_event_entry(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    log_types_response = await client.get(
        f"/api/v1/organizations/{org_id}/event-log-types", headers=_auth_header(token)
    )
    glass_type_id = next(t["id"] for t in log_types_response.json() if t["key"] == "glass")
    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/event-log-types/{glass_type_id}/entries",
        json={"entry_date": "2026-06-28", "payload": {"details": "Розбита лампа"}},
        headers=_auth_header(token),
    )
    entry_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/event-entries/{entry_id}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 204

    missing_delete = await client.delete(
        f"/api/v1/organizations/{org_id}/event-entries/{entry_id}", headers=_auth_header(token)
    )
    assert missing_delete.status_code == 404
    assert missing_delete.json()["error"]["code"] == "event_entry_not_found"


async def test_outsider_cannot_access_event_logs(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    outsider = await _signup(client, email="outsider@other.ua", organization_name="Other Business")
    outsider_token = outsider["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/event-log-types", headers=_auth_header(outsider_token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
