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


async def test_chemical_crud_and_attachment(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/chemicals",
        json={"name": "Деохлор (дезінфектант)", "category": "disinfecting"},
        headers=_auth_header(token),
    )
    assert create_response.status_code == 201
    chemical_id = create_response.json()["id"]

    upload_response = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("sds.pdf", b"data", "application/pdf")},
        headers=_auth_header(token),
    )
    attachment_id = upload_response.json()["id"]
    attach_response = await client.post(
        f"/api/v1/organizations/{org_id}/chemicals/{chemical_id}/attachment",
        json={"attachment_id": attachment_id},
        headers=_auth_header(token),
    )
    assert attach_response.status_code == 200
    assert attach_response.json()["attachment_id"] == attachment_id

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/chemicals/{chemical_id}",
        json={"category": "cleaning"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["category"] == "cleaning"

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/chemicals", headers=_auth_header(token)
    )
    assert len(list_response.json()) == 1

    detach_response = await client.delete(
        f"/api/v1/organizations/{org_id}/chemicals/{chemical_id}/attachment",
        headers=_auth_header(token),
    )
    assert detach_response.status_code == 200
    assert detach_response.json()["attachment_id"] is None

    attach_unknown_response = await client.post(
        f"/api/v1/organizations/{org_id}/chemicals/{chemical_id}/attachment",
        json={"attachment_id": "00000000-0000-0000-0000-000000000000"},
        headers=_auth_header(token),
    )
    assert attach_unknown_response.status_code == 404
    assert attach_unknown_response.json()["error"]["code"] == "attachment_not_found"

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/chemicals/{chemical_id}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 204


async def test_waste_type_crud(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/waste-types",
        json={
            "name": "Пакувальні відходи (пластик)",
            "disposal_method": "Сортування, вивіз ліцензованим перевізником",
        },
        headers=_auth_header(token),
    )
    assert create_response.status_code == 201
    waste_type_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/waste-types/{waste_type_id}",
        json={"disposal_method": "Компостування"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["disposal_method"] == "Компостування"

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/waste-types", headers=_auth_header(token)
    )
    assert len(list_response.json()) == 1

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/waste-types/{waste_type_id}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 204

    missing_update = await client.patch(
        f"/api/v1/organizations/{org_id}/waste-types/{waste_type_id}",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    assert missing_update.status_code == 404
    assert missing_update.json()["error"]["code"] == "waste_type_not_found"


async def test_medical_check_crud(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/medical-checks",
        json={"employee_name": "Марія Гриценко", "next_check_date": "2026-07-30"},
        headers=_auth_header(token),
    )
    assert create_response.status_code == 201
    medical_check_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/medical-checks/{medical_check_id}",
        json={"next_check_date": "2026-08-15"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["next_check_date"] == "2026-08-15"

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/medical-checks", headers=_auth_header(token)
    )
    assert len(list_response.json()) == 1

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/medical-checks/{medical_check_id}",
        headers=_auth_header(token),
    )
    assert delete_response.status_code == 204


async def test_allergens_are_preseeded_and_toggleable(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/allergens", headers=_auth_header(token)
    )
    assert list_response.status_code == 200
    allergens = list_response.json()
    assert len(allergens) == 14
    assert all(a["present"] is False for a in allergens)
    milk = next(a for a in allergens if a["name"] == "Молоко")

    toggle_response = await client.patch(
        f"/api/v1/organizations/{org_id}/allergens/{milk['allergen_id']}",
        json={"present": True},
        headers=_auth_header(token),
    )
    assert toggle_response.status_code == 200
    assert toggle_response.json()["present"] is True

    relist_response = await client.get(
        f"/api/v1/organizations/{org_id}/allergens", headers=_auth_header(token)
    )
    milk_after = next(a for a in relist_response.json() if a["name"] == "Молоко")
    assert milk_after["present"] is True


async def test_allergen_toggle_unknown_id_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.patch(
        f"/api/v1/organizations/{org_id}/allergens/00000000-0000-0000-0000-000000000000",
        json={"present": True},
        headers=_auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "allergen_not_found"


async def test_outsider_cannot_access_directories(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    outsider = await _signup(client, email="outsider@other.ua", organization_name="Other Business")
    outsider_token = outsider["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/chemicals", headers=_auth_header(outsider_token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


async def test_chemical_endpoints_404_for_unknown_id(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/chemicals/{UNKNOWN_ID}",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 404
    assert update_response.json()["error"]["code"] == "chemical_not_found"

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/chemicals/{UNKNOWN_ID}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "chemical_not_found"

    attach_response = await client.post(
        f"/api/v1/organizations/{org_id}/chemicals/{UNKNOWN_ID}/attachment",
        json={"attachment_id": UNKNOWN_ID},
        headers=_auth_header(token),
    )
    assert attach_response.status_code == 404
    assert attach_response.json()["error"]["code"] == "chemical_not_found"

    detach_response = await client.delete(
        f"/api/v1/organizations/{org_id}/chemicals/{UNKNOWN_ID}/attachment",
        headers=_auth_header(token),
    )
    assert detach_response.status_code == 404
    assert detach_response.json()["error"]["code"] == "chemical_not_found"


async def test_waste_type_delete_404_for_unknown_id(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.delete(
        f"/api/v1/organizations/{org_id}/waste-types/{UNKNOWN_ID}", headers=_auth_header(token)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "waste_type_not_found"


async def test_medical_check_endpoints_404_for_unknown_id(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/medical-checks/{UNKNOWN_ID}",
        json={"employee_name": "X"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 404
    assert update_response.json()["error"]["code"] == "medical_check_not_found"

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/medical-checks/{UNKNOWN_ID}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "medical_check_not_found"
