from httpx import AsyncClient

from app.core.config import get_settings


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


async def test_upload_then_download_roundtrips(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    upload_response = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("passport.pdf", b"%PDF-1.4 fake", "application/pdf")},
        headers=_auth_header(token),
    )
    assert upload_response.status_code == 201
    body = upload_response.json()
    assert body["filename"] == "passport.pdf"
    assert body["size_bytes"] == len(b"%PDF-1.4 fake")

    download_response = await client.get(
        f"/api/v1/organizations/{org_id}/attachments/{body['id']}", headers=_auth_header(token)
    )
    assert download_response.status_code == 200
    assert download_response.content == b"%PDF-1.4 fake"
    assert download_response.headers["content-type"] == "application/pdf"
    assert "passport.pdf" in download_response.headers["content-disposition"]


async def test_upload_rejects_unsupported_content_type(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("virus.exe", b"MZ", "application/x-msdownload")},
        headers=_auth_header(token),
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_content_type"


async def test_upload_rejects_oversized_file(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    oversized = b"x" * (get_settings().attachment_max_size_bytes + 1)

    response = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("huge.pdf", oversized, "application/pdf")},
        headers=_auth_header(token),
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "attachment_too_large"


async def test_download_unknown_attachment_returns_404(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    response = await client.get(
        f"/api/v1/organizations/{org_id}/attachments/00000000-0000-0000-0000-000000000000",
        headers=_auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "attachment_not_found"


async def test_outsider_cannot_upload_or_download(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]
    upload_response = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("doc.pdf", b"data", "application/pdf")},
        headers=_auth_header(token),
    )
    attachment_id = upload_response.json()["id"]
    outsider = await _signup(client, email="outsider@other.ua", organization_name="Other Business")
    outsider_token = outsider["tokens"]["access_token"]

    upload_attempt = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("doc.pdf", b"data", "application/pdf")},
        headers=_auth_header(outsider_token),
    )
    assert upload_attempt.status_code == 403

    download_attempt = await client.get(
        f"/api/v1/organizations/{org_id}/attachments/{attachment_id}",
        headers=_auth_header(outsider_token),
    )
    assert download_attempt.status_code == 403


async def test_download_keeps_ukrainian_filename(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    token = owner["tokens"]["access_token"]

    upload_response = await client.post(
        f"/api/v1/organizations/{org_id}/attachments",
        files={"file": ("Паспорт камери.pdf", b"%PDF-1.4 fake", "application/pdf")},
        headers=_auth_header(token),
    )
    assert upload_response.status_code == 201

    download_response = await client.get(
        f"/api/v1/organizations/{org_id}/attachments/{upload_response.json()['id']}",
        headers=_auth_header(token),
    )
    assert download_response.status_code == 200
    disposition = download_response.headers["content-disposition"]
    # ASCII fallback for old clients, exact UTF-8 name for everyone else.
    assert 'filename="_______ ______.pdf"' in disposition
    assert "filename*=UTF-8''%D0%9F%D0%B0%D1%81%D0%BF%D0%BE%D1%80%D1%82%20" in disposition
