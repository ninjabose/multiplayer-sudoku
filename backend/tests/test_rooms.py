from __future__ import annotations


def _create(client, name="alice", difficulty=1):
    response = client.post("/rooms", json={"name": name, "difficulty": difficulty})
    assert response.status_code == 200, response.text
    return response.json()


def test_create_room(client):
    data = _create(client)
    assert data["host"] == "alice"
    assert data["status"] == "lobby"
    assert data["players"] == ["alice"]
    assert data["difficulty"] == 1
    assert data["pot_points"] == 20
    assert len(data["join_code"]) == 6


def test_join_room(client):
    room = _create(client)
    response = client.post(
        f"/rooms/{room['join_code']}/join", json={"name": "bob"}
    )
    assert response.status_code == 200
    assert response.json()["players"] == ["alice", "bob"]


def test_fifth_player_cannot_join(client):
    room = _create(client)
    for name in ("bob", "cara", "dan"):
        assert client.post(
            f"/rooms/{room['join_code']}/join", json={"name": name}
        ).status_code == 200
    response = client.post(
        f"/rooms/{room['join_code']}/join", json={"name": "erin"}
    )
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


def test_duplicate_name_cannot_join(client):
    room = _create(client)
    response = client.post(
        f"/rooms/{room['join_code']}/join", json={"name": "alice"}
    )
    assert response.status_code == 400


def test_only_host_can_start(client):
    room = _create(client)
    client.post(f"/rooms/{room['join_code']}/join", json={"name": "bob"})
    response = client.post(
        f"/rooms/{room['join_code']}/start", json={"name": "bob"}
    )
    assert response.status_code == 400


def test_start_generates_a_puzzle(client):
    room = _create(client, difficulty=2)
    response = client.post(
        f"/rooms/{room['join_code']}/start", json={"name": "alice"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "playing"
    assert data["puzzle"] is not None
    assert data["grid"] == data["puzzle"]
    assert "solution" not in data
    assert sum(cell == 0 for row in data["puzzle"] for cell in row) == 81 - 38


def test_cannot_join_after_start(client):
    room = _create(client)
    client.post(f"/rooms/{room['join_code']}/start", json={"name": "alice"})
    response = client.post(
        f"/rooms/{room['join_code']}/join", json={"name": "bob"}
    )
    assert response.status_code == 400


def test_unknown_room_is_404(client):
    response = client.get("/rooms/ZZZZZZ")
    assert response.status_code == 404


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
