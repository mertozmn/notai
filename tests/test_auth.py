def test_register_and_login(client):
    r = client.post(
        "/auth/register", json={"email": "a@example.com", "password": "password123"}
    )
    assert r.status_code == 201
    assert r.json()["email"] == "a@example.com"
    assert "password" not in r.json()
    assert "password_hash" not in r.json()

    r = client.post(
        "/auth/login", data={"username": "a@example.com", "password": "password123"}
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_duplicate_email_returns_409(client):
    body = {"email": "a@example.com", "password": "password123"}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409


def test_wrong_password_returns_401(client):
    client.post(
        "/auth/register", json={"email": "a@example.com", "password": "password123"}
    )
    r = client.post(
        "/auth/login", data={"username": "a@example.com", "password": "yanlis-parola"}
    )
    assert r.status_code == 401


def test_short_password_returns_422(client):
    r = client.post(
        "/auth/register", json={"email": "a@example.com", "password": "kisa"}
    )
    assert r.status_code == 422


def test_me_requires_token(client):
    assert client.get("/me").status_code == 401


def test_fake_token_returns_401(client):
    r = client.get("/me", headers={"Authorization": "Bearer sahte.token.degeri"})
    assert r.status_code == 401