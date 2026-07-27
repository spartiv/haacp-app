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


async def test_owner_creates_updates_and_deletes_equipment(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/equipment",
        json={
            "type": "production",
            "name": "Пастеризатор ВП-500",
            "frequency": "Щомісяця",
            "amount": 1,
            "affects_product_safety": True,
        },
        headers=_auth_header(token),
    )
    assert create_response.status_code == 201
    equipment_id = create_response.json()["id"]

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/equipment/{equipment_id}", headers=_auth_header(token)
    )
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Пастеризатор ВП-500"

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/equipment/{equipment_id}",
        json={"amount": 2},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == 2

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/equipment/{equipment_id}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/equipment/{equipment_id}", headers=_auth_header(token)
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "equipment_not_found"


async def test_staff_cannot_create_equipment_but_can_list(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    staff_token = await _make_staff(client, fake_email_sender, org_id, owner_token)

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/equipment",
        json={"type": "other", "name": "X", "frequency": "Щомісяця"},
        headers=_auth_header(staff_token),
    )
    assert create_response.status_code == 403

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/equipment", headers=_auth_header(staff_token)
    )
    assert list_response.status_code == 200


async def test_attach_and_detach_equipment_document(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/equipment",
        json={"type": "production", "name": "X", "frequency": "Щомісяця"},
        headers=_auth_header(token),
    )
    equipment_id = create_response.json()["id"]
    upload_response = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("passport.pdf", b"data", "application/pdf")},
        headers=_auth_header(token),
    )
    attachment_id = upload_response.json()["id"]

    attach_response = await client.post(
        f"/api/v1/organizations/{org_id}/equipment/{equipment_id}/attachment",
        json={"attachment_id": attachment_id},
        headers=_auth_header(token),
    )
    assert attach_response.status_code == 200
    assert attach_response.json()["attachment_id"] == attachment_id

    detach_response = await client.delete(
        f"/api/v1/organizations/{org_id}/equipment/{equipment_id}/attachment",
        headers=_auth_header(token),
    )
    assert detach_response.status_code == 200
    assert detach_response.json()["attachment_id"] is None


async def test_attach_unknown_attachment_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/equipment",
        json={"type": "production", "name": "X", "frequency": "Щомісяця"},
        headers=_auth_header(token),
    )
    equipment_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/organizations/{org_id}/equipment/{equipment_id}/attachment",
        json={"attachment_id": "00000000-0000-0000-0000-000000000000"},
        headers=_auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "attachment_not_found"


async def test_update_unknown_equipment_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.patch(
        f"/api/v1/organizations/{org_id}/equipment/00000000-0000-0000-0000-000000000000",
        json={"amount": 3},
        headers=_auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "equipment_not_found"


UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


async def test_equipment_endpoints_404_for_unknown_id(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/equipment/{UNKNOWN_ID}", headers=_auth_header(token)
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "equipment_not_found"

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/equipment/{UNKNOWN_ID}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "equipment_not_found"

    attach_response = await client.post(
        f"/api/v1/organizations/{org_id}/equipment/{UNKNOWN_ID}/attachment",
        json={"attachment_id": UNKNOWN_ID},
        headers=_auth_header(token),
    )
    assert attach_response.status_code == 404
    assert attach_response.json()["error"]["code"] == "equipment_not_found"

    detach_response = await client.delete(
        f"/api/v1/organizations/{org_id}/equipment/{UNKNOWN_ID}/attachment",
        headers=_auth_header(token),
    )
    assert detach_response.status_code == 404
    assert detach_response.json()["error"]["code"] == "equipment_not_found"
