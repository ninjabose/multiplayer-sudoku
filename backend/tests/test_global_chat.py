from __future__ import annotations

from app.game.chat import MAX_CHAT_LEN
from app.game.global_chat import global_chat


def test_global_chat_broadcast_and_presence(client):
    with client.websocket_connect("/ws/global?name=alice") as alice:
        presence = alice.receive_json()
        assert presence["type"] == "presence"
        assert presence["users"] == ["alice"]
        with client.websocket_connect("/ws/global?name=bob") as bob:
            alice_presence = alice.receive_json()
            bob_presence = bob.receive_json()
            assert alice_presence["type"] == "presence"
            assert set(alice_presence["users"]) == {"alice", "bob"}
            assert set(bob_presence["users"]) == {"alice", "bob"}
            alice.send_json({"type": "chat", "message": "hello lobby"})
            for sock in (alice, bob):
                payload = sock.receive_json()
                assert payload["type"] == "chat"
                assert payload["username"] == "alice"
                assert payload["message"] == "hello lobby"
                assert "timestamp" in payload


def test_global_chat_rejects_empty_and_overlong(client):
    with client.websocket_connect("/ws/global?name=alice") as ws:
        ws.receive_json()
        ws.send_json({"type": "chat", "message": ""})
        assert ws.receive_json()["type"] == "error"
        ws.send_json({"type": "chat", "message": "y" * (MAX_CHAT_LEN + 1)})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert "200" in error["message"]


def test_global_chat_rate_limit(client):
    with client.websocket_connect("/ws/global?name=alice") as ws:
        ws.receive_json()
        for i in range(5):
            ws.send_json({"type": "chat", "message": f"g {i}"})
            assert ws.receive_json()["type"] == "chat"
        ws.send_json({"type": "chat", "message": "overflow"})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert "quickly" in error["message"].lower()


def test_global_chat_ignores_client_username(client):
    with client.websocket_connect("/ws/global?name=alice") as ws:
        ws.receive_json()
        ws.send_json({"type": "chat", "username": "admin", "message": "hi"})
        payload = ws.receive_json()
        assert payload["username"] == "alice"


def test_global_disconnect_cleans_presence(client):
    with client.websocket_connect("/ws/global?name=alice") as alice:
        alice.receive_json()
        with client.websocket_connect("/ws/global?name=bob") as bob:
            alice.receive_json()
            bob.receive_json()
        leftover = alice.receive_json()
        assert leftover["type"] == "presence"
        assert leftover["users"] == ["alice"]
    assert "alice" not in global_chat.connections
    assert "bob" not in global_chat.connections


def test_global_chat_does_not_touch_game_rooms(client):
    room = client.post("/rooms", json={"name": "alice", "difficulty": 2}).json()
    code = room["join_code"]
    with client.websocket_connect("/ws/global?name=alice") as global_ws:
        global_ws.receive_json()
        global_ws.send_json({"type": "chat", "message": "from global"})
        assert global_ws.receive_json()["type"] == "chat"
    snapshot = client.get(f"/rooms/{code}").json()
    assert snapshot["status"] == "lobby"
    assert snapshot["players"] == ["alice"]
    assert "grid" in snapshot
