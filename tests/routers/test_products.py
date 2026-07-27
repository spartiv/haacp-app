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


async def test_owner_creates_product_and_checklist(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "Масло вершкове 82%"},
        headers=_auth_header(token),
    )
    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Температура пастеризації в нормі"},
        headers=_auth_header(token),
    )
    assert item_response.status_code == 201
    assert item_response.json()["position"] == 0

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        headers=_auth_header(token),
    )
    assert len(list_response.json()) == 1


async def test_staff_cannot_create_product_but_can_view(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    staff_token = await _make_staff(client, fake_email_sender, org_id, owner_token)

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "Should fail"},
        headers=_auth_header(staff_token),
    )
    assert create_response.status_code == 403

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/products", headers=_auth_header(staff_token)
    )
    assert list_response.status_code == 200


async def test_staff_can_record_batch_and_deviation_flag_is_set(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]
    staff_token = await _make_staff(client, fake_email_sender, org_id, owner_token)

    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "Сир Полтон"},
        headers=_auth_header(owner_token),
    )
    product_id = product_response.json()["id"]
    item1 = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Дозрівання за графіком"},
        headers=_auth_header(owner_token),
    )
    item2 = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Цвіль на поверхні"},
        headers=_auth_header(owner_token),
    )

    batch_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/batches",
        json={
            "number": "PLT-2026-07-20",
            "name": None,
            "production_date": "2026-07-20",
            "answers": [
                {"checklist_item_id": item1.json()["id"], "answer": True},
                {"checklist_item_id": item2.json()["id"], "answer": False},
            ],
            "deviation_note": "Виявлено цвіль на 2 головках",
            "corrective_action": "Партію вилучено з дозрівальної камери",
        },
        headers=_auth_header(staff_token),
    )

    assert batch_response.status_code == 201
    body = batch_response.json()
    assert body["has_deviation"] is True
    assert body["signatory_user_id"]
    assert len(body["answers"]) == 2


async def test_record_batch_rejects_checklist_mismatch(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]
    await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )

    response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/batches",
        json={
            "number": "B-001",
            "production_date": "2026-07-20",
            "answers": [],
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "checklist_mismatch"


async def test_edit_batch_and_view_history(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]
    item = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    batch_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/batches",
        json={
            "number": "B-001",
            "production_date": "2026-07-20",
            "answers": [{"checklist_item_id": item.json()["id"], "answer": True}],
        },
        headers=_auth_header(token),
    )
    batch_id = batch_response.json()["id"]

    edit_response = await client.patch(
        f"/api/v1/organizations/{org_id}/batches/{batch_id}",
        json={"number": "B-001-FIXED"},
        headers=_auth_header(token),
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["number"] == "B-001-FIXED"

    history_response = await client.get(
        f"/api/v1/organizations/{org_id}/batches/{batch_id}/history",
        headers=_auth_header(token),
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["snapshot"]["number"] == "B-001"


async def test_delete_batch_then_get_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]
    item = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    batch_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/batches",
        json={
            "number": "B-001",
            "production_date": "2026-07-20",
            "answers": [{"checklist_item_id": item.json()["id"], "answer": True}],
        },
        headers=_auth_header(token),
    )
    batch_id = batch_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/batches/{batch_id}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/batches/{batch_id}", headers=_auth_header(token)
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "batch_not_found"


async def test_user_outside_organization_cannot_access_products(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    outsider = await _signup(client, email="outsider@other.ua", organization_name="Other Business")
    outsider_token = outsider["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/products", headers=_auth_header(outsider_token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


async def test_get_single_product_success_and_not_found(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "Масло вершкове 82%"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]

    ok_response = await client.get(
        f"/api/v1/organizations/{org_id}/products/{product_id}", headers=_auth_header(token)
    )
    assert ok_response.status_code == 200
    assert ok_response.json()["name"] == "Масло вершкове 82%"

    missing_response = await client.get(
        f"/api/v1/organizations/{org_id}/products/00000000-0000-0000-0000-000000000000",
        headers=_auth_header(token),
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "product_not_found"


async def test_delete_product_then_get_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/products/{product_id}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/products/{product_id}", headers=_auth_header(token)
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "product_not_found"


async def test_delete_unknown_product_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.delete(
        f"/api/v1/organizations/{org_id}/products/00000000-0000-0000-0000-000000000000",
        headers=_auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_not_found"


async def test_update_and_remove_checklist_item(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Original label"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items/{item_id}",
        json={"label": "Updated label"},
        headers=_auth_header(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["label"] == "Updated label"

    missing_update = await client.patch(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items/"
        "00000000-0000-0000-0000-000000000000",
        json={"label": "Nope"},
        headers=_auth_header(token),
    )
    assert missing_update.status_code == 404
    assert missing_update.json()["error"]["code"] == "checklist_item_not_found"

    remove_response = await client.delete(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items/{item_id}",
        headers=_auth_header(token),
    )
    assert remove_response.status_code == 204

    missing_remove = await client.delete(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items/{item_id}",
        headers=_auth_header(token),
    )
    assert missing_remove.status_code == 404
    assert missing_remove.json()["error"]["code"] == "checklist_item_not_found"


async def test_list_batches_for_product_and_get_single_batch(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    batch_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/batches",
        json={
            "number": "B-001",
            "production_date": "2026-07-20",
            "answers": [{"checklist_item_id": item_id, "answer": True}],
        },
        headers=_auth_header(token),
    )
    batch_id = batch_response.json()["id"]

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/products/{product_id}/batches",
        headers=_auth_header(token),
    )
    assert list_response.status_code == 200
    assert [b["id"] for b in list_response.json()] == [batch_id]

    get_response = await client.get(
        f"/api/v1/organizations/{org_id}/batches/{batch_id}", headers=_auth_header(token)
    )
    assert get_response.status_code == 200
    assert get_response.json()["number"] == "B-001"


UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


async def test_checklist_item_endpoints_404_for_unknown_product(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    list_response = await client.get(
        f"/api/v1/organizations/{org_id}/products/{UNKNOWN_ID}/checklist-items",
        headers=_auth_header(token),
    )
    assert list_response.status_code == 404
    assert list_response.json()["error"]["code"] == "product_not_found"

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{UNKNOWN_ID}/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    assert create_response.status_code == 404
    assert create_response.json()["error"]["code"] == "product_not_found"


async def test_batch_endpoints_404_for_unknown_batch(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    edit_response = await client.patch(
        f"/api/v1/organizations/{org_id}/batches/{UNKNOWN_ID}",
        json={"number": "X"},
        headers=_auth_header(token),
    )
    assert edit_response.status_code == 404
    assert edit_response.json()["error"]["code"] == "batch_not_found"

    delete_response = await client.delete(
        f"/api/v1/organizations/{org_id}/batches/{UNKNOWN_ID}", headers=_auth_header(token)
    )
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "batch_not_found"

    history_response = await client.get(
        f"/api/v1/organizations/{org_id}/batches/{UNKNOWN_ID}/history",
        headers=_auth_header(token),
    )
    assert history_response.status_code == 404
    assert history_response.json()["error"]["code"] == "batch_not_found"


async def test_edit_batch_rejects_checklist_mismatch(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    product_response = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "X"},
        headers=_auth_header(token),
    )
    product_id = product_response.json()["id"]
    item_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/checklist-items",
        json={"label": "Q1"},
        headers=_auth_header(token),
    )
    item_id = item_response.json()["id"]
    batch_response = await client.post(
        f"/api/v1/organizations/{org_id}/products/{product_id}/batches",
        json={
            "number": "B-001",
            "production_date": "2026-07-20",
            "answers": [{"checklist_item_id": item_id, "answer": True}],
        },
        headers=_auth_header(token),
    )
    batch_id = batch_response.json()["id"]

    response = await client.patch(
        f"/api/v1/organizations/{org_id}/batches/{batch_id}",
        json={"answers": []},
        headers=_auth_header(token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "checklist_mismatch"
