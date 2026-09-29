from httpx import AsyncClient


async def test_register_creates_user(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register", json={"email": "alice@example.com", "password": "hunter2pass"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "password" not in body


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {"email": "bob@example.com", "password": "hunter2pass"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_returns_token_and_me_uses_it(client: AsyncClient) -> None:
    await client.post(
        "/auth/register", json={"email": "carol@example.com", "password": "hunter2pass"}
    )

    login_response = await client.post(
        "/auth/login", json={"email": "carol@example.com", "password": "hunter2pass"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "carol@example.com"


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/auth/register", json={"email": "dave@example.com", "password": "hunter2pass"}
    )

    response = await client.post(
        "/auth/login", json={"email": "dave@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401
