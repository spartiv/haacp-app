from datetime import date, timedelta

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


async def test_owner_manages_daily_checklist_items(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Якість води в нормі"},
        headers=_auth_header(token),
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items/{item_id}",
        json={"label": "Якість води відповідає нормі"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["label"] == "Якість води відповідає нормі"

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        headers=_auth_header(token),
    )
    assert len(list_response.json()) == 1

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items/{item_id}",
        headers=_auth_header(token),
    )
    assert delete_response.status_code == 204

    empty_list_response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        headers=_auth_header(token),
    )
    assert empty_list_response.json() == []


UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


async def test_checklist_item_endpoints_404_for_unknown_id(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items/{UNKNOWN_ID}",
        json={"label": "X"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 404
    assert update_response.json()["error"]["code"] == "control_checklist_item_not_found"

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items/{UNKNOWN_ID}",
        headers=_auth_header(token),
    )
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "control_checklist_item_not_found"


async def test_staff_cannot_manage_checklist_items(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    staff_token = await _make_staff(client, fake_email_sender, org_id, owner_token)

    response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Should fail"},
        headers=_auth_header(staff_token),
    )

    assert response.status_code == 403


async def test_get_current_control_before_filled_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/daily/current", headers=_auth_header(token)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "control_record_not_filled"


async def test_staff_can_fill_and_refill_current_daily_control(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Персонал у спецодязі"},
        headers=_auth_header(owner_token),
    )
    item_id = item_response.json()["id"]
    staff_token = await _make_staff(client, fake_email_sender, org_id, owner_token)

    fill_response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": True}]},
        headers=_auth_header(staff_token),
    )
    assert fill_response.status_code == 200
    body = fill_response.json()
    assert body["has_deviation"] is False
    record_id = body["id"]

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/daily/current", headers=_auth_header(staff_token)
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == record_id

    refill_response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": False}]},
        headers=_auth_header(staff_token),
    )
    assert refill_response.status_code == 200
    assert refill_response.json()["id"] == record_id
    assert refill_response.json()["has_deviation"] is True

    history_response = await client.get(
        f"/api/v1/organizations/{org_id}/control-records/{record_id}/history",
        headers=_auth_header(staff_token),
    )
    assert history_response.status_code == 200
    assert len(history_response.json()) == 1


async def test_fill_current_control_with_explicit_past_date(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    fill_response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={
            "answers": [{"control_checklist_item_id": item_id, "answer": True}],
            "period_date": yesterday,
        },
        headers=_auth_header(token),
    )

    assert fill_response.status_code == 200
    assert fill_response.json()["period_date"] == yesterday

    today_response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/daily/current", headers=_auth_header(token)
    )
    assert today_response.status_code == 404


async def test_fill_current_control_rejects_future_date(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={
            "answers": [{"control_checklist_item_id": item_id, "answer": True}],
            "period_date": tomorrow,
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "future_period_date"


async def test_control_record_note_round_trips_through_put_and_patch(
    client: AsyncClient,
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]

    fill_response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={
            "answers": [{"control_checklist_item_id": item_id, "answer": True}],
            "note": "Freezer 1 door left open briefly",
        },
        headers=_auth_header(token),
    )
    assert fill_response.status_code == 200
    body = fill_response.json()
    assert body["note"] == "Freezer 1 door left open briefly"
    record_id = body["id"]

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/daily/current", headers=_auth_header(token)
    )
    assert get_response.json()["note"] == "Freezer 1 door left open briefly"

    edit_response = await client.patch(
        f"/api/v1/organizations/{org_id}/control-records/{record_id}",
        json={
            "answers": [{"control_checklist_item_id": item_id, "answer": True}],
            "note": "Resolved, no product affected",
        },
        headers=_auth_header(token),
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["note"] == "Resolved, no product affected"

    unchanged_edit_response = await client.patch(
        f"/api/v1/organizations/{org_id}/control-records/{record_id}",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": True}]},
        headers=_auth_header(token),
    )
    assert unchanged_edit_response.status_code == 200
    assert unchanged_edit_response.json()["note"] == "Resolved, no product affected"


async def test_fill_current_control_rejects_checklist_mismatch(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )

    response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={"answers": []},
        headers=_auth_header(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "checklist_mismatch"


async def test_edit_control_record_rejects_checklist_mismatch(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    fill_response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": True}]},
        headers=_auth_header(token),
    )
    record_id = fill_response.json()["id"]

    response = await client.patch(
        f"/api/v1/organizations/{org_id}/control-records/{record_id}",
        json={"answers": []},
        headers=_auth_header(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "checklist_mismatch"


async def test_list_and_delete_control_records(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/monthly/checklist-items",
        json={"label": "Дератизація проведена"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    fill_response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/monthly/current",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": True}]},
        headers=_auth_header(token),
    )
    record_id = fill_response.json()["id"]

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/monthly/records", headers=_auth_header(token)
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    # PUT /current auto-submits, and submitted records are part of the audit trail.
    submitted_delete = await client.delete(
        f"/api/v1/organizations/{org_id}/control-records/{record_id}", headers=_auth_header(token)
    )
    assert submitted_delete.status_code == 409
    assert submitted_delete.json()["error"]["code"] == "control_record_submitted"

    # A draft (started item by item, not submitted) can still be deleted.
    last_month = (date.today().replace(day=1) - timedelta(days=1)).isoformat()
    draft = await client.post(
        f"/api/v1/organizations/{org_id}/controls/monthly/items/{item_id}/check",
        json={"status": "pass", "period_date": last_month},
        headers=_auth_header(token),
    )
    draft_id = draft.json()["record_id"]
    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/control-records/{draft_id}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 204

    missing_get = await client.get(
        f"/api/v1/organizations/{org_id}/control-records/{draft_id}", headers=_auth_header(token)
    )
    assert missing_get.status_code == 404
    assert missing_get.json()["error"]["code"] == "control_record_not_found"


async def test_edit_control_record_by_id(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    fill_response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": True}]},
        headers=_auth_header(token),
    )
    record_id = fill_response.json()["id"]

    edit_response = await client.patch(
        f"/api/v1/organizations/{org_id}/control-records/{record_id}",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": False}]},
        headers=_auth_header(token),
    )

    assert edit_response.status_code == 200
    assert edit_response.json()["has_deviation"] is True

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/control-records/{record_id}",
        headers=_auth_header(token),
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == record_id


async def test_control_record_endpoints_404_for_unknown_id(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/control-records/{UNKNOWN_ID}",
        headers=_auth_header(token),
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "control_record_not_found"

    edit_response = await client.patch(
        f"/api/v1/organizations/{org_id}/control-records/{UNKNOWN_ID}",
        json={"answers": []},
        headers=_auth_header(token),
    )
    assert edit_response.status_code == 404
    assert edit_response.json()["error"]["code"] == "control_record_not_found"

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/control-records/{UNKNOWN_ID}",
        headers=_auth_header(token),
    )
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "control_record_not_found"

    history_response = await client.get(
        f"/api/v1/organizations/{org_id}/control-records/{UNKNOWN_ID}/history",
        headers=_auth_header(token),
    )
    assert history_response.status_code == 404
    assert history_response.json()["error"]["code"] == "control_record_not_found"


async def test_outsider_cannot_access_controls(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    outsider = await _signup(client, email="outsider@other.ua", organization_name="Other Business")
    outsider_token = outsider["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        headers=_auth_header(outsider_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
