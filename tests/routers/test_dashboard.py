from httpx import AsyncClient


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


async def test_dashboard_for_fresh_organization(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/dashboard", headers=_auth_header(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["daily_control"] == {"filled": False, "has_deviation": None}
    assert body["monthly_control"] == {"filled": False, "has_deviation": None}
    assert body["batches_this_month"] == 0
    assert len(body["attention_items"]) == 2
    assert all(item["severity"] == "critical" for item in body["attention_items"])


async def test_dashboard_reflects_filled_daily_control(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/controls/daily/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    await client.put(
        f"/api/v1/organizations/{org_id}/controls/daily/current",
        json={"answers": [{"control_checklist_item_id": item_id, "answer": True}]},
        headers=_auth_header(token),
    )

    response = await client.get(
        f"/api/v1/organizations/{org_id}/dashboard", headers=_auth_header(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["daily_control"] == {"filled": True, "has_deviation": False}
    labels = [item["label"] for item in body["attention_items"]]
    assert "Щоденний контроль на сьогодні не заповнено" not in labels


async def test_outsider_cannot_access_dashboard(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    outsider = await _signup(client, email="outsider@other.ua", organization_name="Other Business")
    outsider_token = outsider["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/dashboard", headers=_auth_header(outsider_token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


async def test_draft_daily_control_is_not_filled(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    base = f"/api/v1/organizations/{org_id}"
    first = await client.post(
        f"{base}/controls/daily/checklist-items", json={"label": "Q1"}, headers=_auth_header(token)
    )
    await client.post(
        f"{base}/controls/daily/checklist-items", json={"label": "Q2"}, headers=_auth_header(token)
    )
    await client.post(
        f"{base}/controls/daily/items/{first.json()['id']}/check",
        json={"status": "deviation", "corrective_action": "Викликано майстра"},
        headers=_auth_header(token),
    )

    response = await client.get(f"{base}/dashboard", headers=_auth_header(token))

    body = response.json()
    # Half-done draft: not filled, but its deviation is already visible.
    assert body["daily_control"] == {"filled": False, "has_deviation": True}
    labels = [item["label"] for item in body["attention_items"]]
    assert "Щоденний контроль на сьогодні розпочато, але не подано" in labels
    assert "Щоденний контроль на сьогодні не заповнено" not in labels
