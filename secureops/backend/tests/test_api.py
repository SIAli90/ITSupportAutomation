

def test_health_is_public(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_endpoints_require_authentication(client):
    for endpoint in ("/api/assets", "/api/incidents", "/api/audit", "/api/dashboard", "/api/auth/me"):
        assert client.get(endpoint).status_code == 401


def test_login_rejects_wrong_credentials(client):
    assert client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"}).status_code == 401


def test_user_details_do_not_leak_password_hash(client, token):
    response = client.get("/api/auth/me", headers=token())
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert "password_hash" not in response.text


def test_analyst_can_create_assets_and_incidents(client, token):
    auth = token("analyst@example.com", "long-password-for-analyst")
    asset = client.post("/api/assets", headers=auth, json={"tag": "lt-010", "name": "Reception laptop", "kind": "laptop", "location": "Luton"})
    assert asset.status_code == 201, asset.text
    assert asset.json()["tag"] == "LT-010"
    incident = client.post("/api/incidents", headers=auth, json={"title": "Suspicious sign-in", "description": "Several unexpected failed sign-ins observed", "severity": "critical", "asset_id": asset.json()["id"]})
    assert incident.status_code == 201, incident.text
    dash = client.get("/api/dashboard", headers=auth).json()
    assert dash["total_assets"] == 1
    assert dash["critical_incidents"] == 1
    changed = client.patch(f"/api/incidents/{incident.json()['id']}", headers=auth, json={"status": "resolved"})
    assert changed.status_code == 200
    assert client.get("/api/dashboard", headers=auth).json()["critical_incidents"] == 0
    events = client.get("/api/audit", headers=auth).json()
    assert len(events) == 3
    assert events[0]["action"] == "updated"
    assert all("password" not in e["details"] for e in events)


def test_viewer_is_read_only_and_cannot_list_users(client, token):
    auth = token("viewer@example.com", "long-password-for-viewer")
    assert client.get("/api/assets", headers=auth).status_code == 200
    assert client.get("/api/users", headers=auth).status_code == 403
    assert client.post("/api/assets", headers=auth, json={"tag": "LAB01", "name": "Laptop", "kind": "laptop"}).status_code == 403
    assert client.post("/api/incidents", headers=auth, json={"title": "Incident one", "description": "sufficient description"}).status_code == 403


def test_validation_duplicates_and_unknown_asset(client, token):
    auth = token()
    payload = {"tag": "lab01", "name": "Asset A", "kind": "server"}
    assert client.post("/api/assets", headers=auth, json=payload).status_code == 201
    assert client.post("/api/assets", headers=auth, json=payload).status_code == 409
    assert client.post("/api/incidents", headers=auth, json={"title": "Invalid asset", "description": "Cannot assign unknown asset", "asset_id": 9999}).status_code == 422
    assert client.patch("/api/assets/999", headers=auth, json={"status": "retired"}).status_code == 404
    assert client.post("/api/assets", headers=auth, json={"tag": "bad space", "name": "Something", "kind": "server"}).status_code == 422


def test_admin_user_creation_and_least_privilege(client, token):
    admin = token()
    new = client.post("/api/users", headers=admin, json={"email": "NEW@EXAMPLE.COM", "full_name": "New Team Member", "role": "viewer", "password": "another-long-password"})
    assert new.status_code == 201, new.text
    assert new.json()["email"] == "new@example.com"
    assert "password" not in new.text
    assert client.post("/api/users", headers=admin, json={"email": "new@example.com", "full_name": "Other User", "role": "viewer", "password": "another-long-password"}).status_code == 409
    user_auth = token("new@example.com", "another-long-password")
    assert client.get("/api/dashboard", headers=user_auth).status_code == 200
    assert client.get("/api/users", headers=user_auth).status_code == 403


def test_limit_validation(client, token):
    assert client.get("/api/assets?limit=1000", headers=token()).status_code == 422


def test_tampered_and_invalid_tokens_are_rejected(client, token):
    good = token()["Authorization"].split(" ", 1)[1]
    bad = good[:-8] + "xxxxxxxx"
    assert client.get("/api/dashboard", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    assert client.get("/api/dashboard", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_update_asset_and_filter_search(client, token):
    auth = token()
    r = client.post("/api/assets", headers=auth, json={"tag": "PC-002", "name": "Accounting computer", "kind": "desktop"})
    assert r.status_code == 201
    asset_id = r.json()["id"]
    updated = client.patch(f"/api/assets/{asset_id}", headers=auth, json={"status": "maintenance", "location": "Floor 2"})
    assert updated.status_code == 200
    assert updated.json()["location"] == "Floor 2"
    assert len(client.get("/api/assets?search=accounting", headers=auth).json()) == 1
    assert len(client.get("/api/assets?search=nonexistent", headers=auth).json()) == 0
    assert client.get("/api/audit", headers=auth).json()[0]["details"] == '{"status": "maintenance", "location": "Floor 2"}'
