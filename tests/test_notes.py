def test_create_and_list_notes(client, make_user):
    headers = make_user()
    r = client.post("/notes", json={"title": "Matematik", "content": "95"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["title"] == "Matematik"

    r = client.get("/notes", headers=headers)
    assert r.status_code == 200
    assert [n["title"] for n in r.json()] == ["Matematik"]


def test_notes_require_auth(client):
    assert client.get("/notes").status_code == 401
    assert client.post("/notes", json={"title": "x", "content": "y"}).status_code == 401


def test_cannot_access_other_users_note(client, make_user):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")

    note_id = client.post(
        "/notes", json={"title": "Gizli", "content": "alice'e ait"}, headers=alice
    ).json()["id"]

    assert client.get(f"/notes/{note_id}", headers=bob).status_code == 404
    assert (
        client.put(
            f"/notes/{note_id}", json={"title": "x", "content": "y"}, headers=bob
        ).status_code
        == 404
    )
    assert client.delete(f"/notes/{note_id}", headers=bob).status_code == 404
    assert client.get("/notes", headers=bob).json() == []

    # Sahibi hâlâ erişebilmeli
    assert client.get(f"/notes/{note_id}", headers=alice).status_code == 200


def test_update_and_delete(client, make_user):
    headers = make_user()
    note_id = client.post(
        "/notes", json={"title": "Eski", "content": "eski içerik"}, headers=headers
    ).json()["id"]

    r = client.put(
        f"/notes/{note_id}", json={"title": "Yeni", "content": "yeni içerik"}, headers=headers
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Yeni"

    assert client.delete(f"/notes/{note_id}", headers=headers).status_code == 204
    assert client.get(f"/notes/{note_id}", headers=headers).status_code == 404


def test_missing_field_returns_422(client, make_user):
    headers = make_user()
    r = client.post("/notes", json={"title": "Sadece başlık"}, headers=headers)
    assert r.status_code == 422


def test_pagination(client, make_user):
    headers = make_user()
    for i in range(5):
        client.post("/notes", json={"title": f"Not {i}", "content": "x"}, headers=headers)

    r = client.get("/notes?limit=2&offset=0", headers=headers)
    assert len(r.json()) == 2
    r = client.get("/notes?limit=2&offset=4", headers=headers)
    assert len(r.json()) == 1