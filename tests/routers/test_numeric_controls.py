"""Numeric checklist items: temperature readings judged against a safe range."""

from typing import Any

from httpx import AsyncClient

from tests.fakes import FakeEmailSender


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _owner(client: AsyncClient) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "owner@polton.ua",
            "password": "supersecret123",
            "full_name": "Olena Polishchuk",
            "organization_name": "Polton",
        },
    )
    body = response.json()
    return str(body["organization_id"]), str(body["tokens"]["access_token"])


async def _add(client: AsyncClient, org_id: str, token: str, **item: Any) -> Any:
    return await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json=item,
        headers=_auth(token),
    )


def _fridge() -> dict[str, Any]:
    return {
        "label": "Камера 1",
        "item_type": "numeric",
        "unit": "°C",
        "min_value": 0,
        "max_value": 4,
    }


async def test_create_numeric_item_returns_its_range(client: AsyncClient) -> None:
    org_id, token = await _owner(client)

    response = await _add(client, org_id, token, **_fridge())

    assert response.status_code == 201
    body = response.json()
    assert body["item_type"] == "numeric"
    assert body["unit"] == "°C"
    assert (body["min_value"], body["max_value"]) == (0.0, 4.0)

    plain = await _add(client, org_id, token, label="Вода в нормі")
    assert plain.json()["item_type"] == "bool"
    assert plain.json()["unit"] is None


async def test_numeric_item_config_is_validated(client: AsyncClient) -> None:
    org_id, token = await _owner(client)

    no_unit = await _add(client, org_id, token, **{**_fridge(), "unit": "  "})
    no_bounds = await _add(
        client, org_id, token, **{**_fridge(), "min_value": None, "max_value": None}
    )
    inverted = await _add(client, org_id, token, **{**_fridge(), "min_value": 5, "max_value": 1})
    bool_with_range = await _add(client, org_id, token, label="Так/Ні", unit="°C", max_value=4)
    too_precise = await _add(client, org_id, token, **{**_fridge(), "max_value": 4.555})

    for response in (no_unit, no_bounds, inverted, bool_with_range):
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_checklist_item_config"
    assert too_precise.status_code == 422

    # One open bound is fine: a freezer only has a maximum.
    freezer = await _add(
        client, org_id, token, label="Морозильник", item_type="numeric", unit="°C", max_value=-18
    )
    assert freezer.status_code == 201
    assert freezer.json()["min_value"] is None


async def test_reading_inside_range_passes_and_outside_needs_corrective_action(
    client: AsyncClient,
) -> None:
    org_id, token = await _owner(client)
    item_id = (await _add(client, org_id, token, **_fridge())).json()["id"]
    check = f"/api/v1/organizations/{org_id}/controls/daily/items/{item_id}/check"

    # Limits are inclusive.
    on_limit = await client.post(check, json={"value": 4}, headers=_auth(token))
    assert on_limit.status_code == 200
    item = on_limit.json()["items"][0]
    assert (item["status"], item["value"], item["unit"]) == ("pass", 4.0, "°C")

    # Out of range: server decides it's a deviation, even if the client says "pass".
    missing_action = await client.post(
        check, json={"value": 6.5, "status": "pass"}, headers=_auth(token)
    )
    assert missing_action.status_code == 422
    assert missing_action.json()["error"]["code"] == "corrective_action_required"

    too_cold = await client.post(
        check,
        json={"value": -1.2, "corrective_action": "Відрегульовано термостат"},
        headers=_auth(token),
    )
    assert too_cold.status_code == 200
    item = too_cold.json()["items"][0]
    assert (item["status"], item["value"]) == ("deviation", -1.2)
    assert too_cold.json()["has_deviation"] is True


async def test_value_rules_per_item_type(client: AsyncClient) -> None:
    org_id, token = await _owner(client)
    fridge = (await _add(client, org_id, token, **_fridge())).json()["id"]
    water = (await _add(client, org_id, token, label="Вода в нормі")).json()["id"]
    base = f"/api/v1/organizations/{org_id}/controls/daily/items"

    no_value = await client.post(
        f"{base}/{fridge}/check", json={"status": "pass"}, headers=_auth(token)
    )
    assert no_value.json()["error"]["code"] == "numeric_value_required"

    value_on_bool = await client.post(
        f"{base}/{water}/check", json={"status": "pass", "value": 3}, headers=_auth(token)
    )
    assert value_on_bool.json()["error"]["code"] == "numeric_value_not_applicable"

    no_status = await client.post(f"{base}/{water}/check", json={}, headers=_auth(token))
    assert no_status.json()["error"]["code"] == "invalid_check_status"


async def test_readings_are_in_the_audit_log_and_amendments_need_a_reason(
    client: AsyncClient,
) -> None:
    org_id, token = await _owner(client)
    item_id = (await _add(client, org_id, token, **_fridge())).json()["id"]
    base = f"/api/v1/organizations/{org_id}"
    check = f"{base}/controls/daily/items/{item_id}/check"

    first = await client.post(check, json={"value": 3.4}, headers=_auth(token))
    record_id = first.json()["record_id"]
    # Sending the same reading again is a no-op (no extra audit entry).
    await client.post(check, json={"value": 3.4}, headers=_auth(token))
    await client.post(f"{base}/control-records/{record_id}/submit", headers=_auth(token))

    no_reason = await client.post(check, json={"value": 3.1}, headers=_auth(token))
    assert no_reason.json()["error"]["code"] == "amendment_reason_required"
    amended = await client.post(
        check,
        json={"value": 3.1, "amendment_reason": "Термометр перевірено повторно"},
        headers=_auth(token),
    )
    assert amended.status_code == 200

    audit = await client.get(
        f"{base}/control-records/{record_id}/audit-events", headers=_auth(token)
    )
    events = audit.json()["items"]
    assert [e["event_type"] for e in events] == ["item_amended", "record_submitted", "item_checked"]
    assert [e["numeric_value"] for e in events] == [3.1, None, 3.4]
    assert events[0]["item_unit"] == "°C"


async def test_tightening_the_range_keeps_past_verdicts(client: AsyncClient) -> None:
    org_id, token = await _owner(client)
    item_id = (await _add(client, org_id, token, **_fridge())).json()["id"]
    base = f"/api/v1/organizations/{org_id}/controls/daily"

    await client.post(f"{base}/items/{item_id}/check", json={"value": 3.5}, headers=_auth(token))
    tightened = await client.patch(
        f"{base}/checklist-items/{item_id}", json={"max_value": 3}, headers=_auth(token)
    )
    assert tightened.status_code == 200
    assert (tightened.json()["min_value"], tightened.json()["max_value"]) == (0.0, 3.0)

    sheet = (await client.get(f"{base}/sheet", headers=_auth(token))).json()
    item = sheet["items"][0]
    # Judged against 0…4 at the time: still a pass, and the sheet shows those limits.
    assert (item["status"], item["max_value"]) == ("pass", 4.0)


async def test_update_rules(client: AsyncClient) -> None:
    org_id, token = await _owner(client)
    fridge = (await _add(client, org_id, token, **_fridge())).json()["id"]
    water = (await _add(client, org_id, token, label="Вода в нормі")).json()["id"]
    base = f"/api/v1/organizations/{org_id}/controls/daily/checklist-items"

    renamed = await client.patch(
        f"{base}/{fridge}", json={"label": "Камера 2"}, headers=_auth(token)
    )
    assert (renamed.json()["label"], renamed.json()["max_value"]) == ("Камера 2", 4.0)

    open_min = await client.patch(
        f"{base}/{fridge}", json={"min_value": None}, headers=_auth(token)
    )
    assert open_min.json()["min_value"] is None

    both_open = await client.patch(
        f"{base}/{fridge}", json={"max_value": None}, headers=_auth(token)
    )
    assert both_open.json()["error"]["code"] == "invalid_checklist_item_config"

    range_on_bool = await client.patch(f"{base}/{water}", json={"unit": "°C"}, headers=_auth(token))
    assert range_on_bool.json()["error"]["code"] == "invalid_checklist_item_config"


async def test_staff_cannot_configure_items(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    org_id, owner_token = await _owner(client)
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "cook@polton.ua", "role": "staff"},
        headers=_auth(owner_token),
    )
    accept = await client.post(
        f"/api/v1/invites/{fake_email_sender.sent[-1]['token']}/accept",
        json={"password": "brandnewpass123", "full_name": "Cook"},
    )
    staff_token = accept.json()["tokens"]["access_token"]

    response = await _add(client, org_id, staff_token, **_fridge())

    assert response.status_code == 403


async def test_legacy_full_sheet_endpoint_refuses_numeric_checklists(client: AsyncClient) -> None:
    org_id, token = await _owner(client)
    fridge = (await _add(client, org_id, token, **_fridge())).json()["id"]

    response = await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={"answers": [{"control_checklist_item_id": fridge, "answer": True}]},
        headers=_auth(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "numeric_items_not_supported"
