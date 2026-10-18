from httpx import AsyncClient

from tests.fakes import FakeEmailSender

STEP_KEYS = [
    "daily_checklist",
    "monthly_checklist",
    "equipment",
    "chemicals",
    "medical_checks",
    "products",
    "team",
    "first_daily_submitted",
]


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


async def _progress(client: AsyncClient, org_id: str, token: str) -> dict:
    response = await client.get(
        f"/api/v1/organizations/{org_id}/setup-progress", headers=_auth_header(token)
    )
    assert response.status_code == 200
    return response.json()


def _done(progress: dict) -> dict[str, bool]:
    return {step["key"]: step["done"] for step in progress["steps"]}


async def test_fresh_organization_has_nothing_done(client: AsyncClient) -> None:
    owner = await _signup(client)

    progress = await _progress(client, owner["organization_id"], owner["tokens"]["access_token"])

    assert progress["completed"] == 0
    assert progress["total"] == len(STEP_KEYS)
    assert [step["key"] for step in progress["steps"]] == STEP_KEYS
    assert all(step["label"] for step in progress["steps"])
    team = next(step for step in progress["steps"] if step["key"] == "team")
    assert team == {**team, "done": False, "count": 1}  # the owner alone isn't a team


async def test_steps_follow_existing_data(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    headers = _auth_header(owner["tokens"]["access_token"])
    base = f"/api/v1/organizations/{org_id}"

    item = await client.post(
        f"{base}/controls/daily/checklist-items", json={"label": "Q1"}, headers=headers
    )
    item_id = item.json()["id"]
    await client.post(
        f"{base}/controls/monthly/checklist-items", json={"label": "M1"}, headers=headers
    )
    await client.post(
        f"{base}/medical-checks",
        json={"employee_name": "Іваненко", "next_check_date": "2027-01-01"},
        headers=headers,
    )
    await client.post(f"{base}/products", json={"name": "Борщ"}, headers=headers)
    await client.post(
        f"{base}/invites", json={"email": "cook@polton.ua", "role": "staff"}, headers=headers
    )
    await client.post(
        f"/api/v1/invites/{fake_email_sender.sent[0]['token']}/accept",
        json={"password": "brandnewpass123", "full_name": "Cook"},
    )

    # A draft sheet doesn't count as the first submission yet.
    sheet = await client.post(
        f"{base}/controls/daily/items/{item_id}/check", json={"status": "pass"}, headers=headers
    )
    assert (
        _done(await _progress(client, org_id, owner["tokens"]["access_token"]))[
            "first_daily_submitted"
        ]
        is False
    )

    submit = await client.post(
        f"{base}/control-records/{sheet.json()['record_id']}/submit", headers=headers
    )
    assert submit.status_code == 200

    progress = await _progress(client, org_id, owner["tokens"]["access_token"])
    assert _done(progress) == {
        "daily_checklist": True,
        "monthly_checklist": True,
        "equipment": False,
        "chemicals": False,
        "medical_checks": True,
        "products": True,
        "team": True,
        "first_daily_submitted": True,
    }
    assert progress["completed"] == 6


async def test_deleted_rows_do_not_count(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    headers = _auth_header(owner["tokens"]["access_token"])
    base = f"/api/v1/organizations/{org_id}"
    created = await client.post(f"{base}/products", json={"name": "Борщ"}, headers=headers)
    await client.delete(f"{base}/products/{created.json()['id']}", headers=headers)

    progress = await _progress(client, org_id, owner["tokens"]["access_token"])

    assert _done(progress)["products"] is False


async def test_outsider_cannot_read_setup_progress(client: AsyncClient) -> None:
    owner = await _signup(client)
    outsider = await _signup(client, email="outsider@other.ua", organization_name="Other")

    response = await client.get(
        f"/api/v1/organizations/{owner['organization_id']}/setup-progress",
        headers=_auth_header(outsider["tokens"]["access_token"]),
    )

    assert response.status_code == 403
