from __future__ import annotations

from app.game.chat import MAX_CHAT_LEN, ChatError, sanitize_chat_message
from app.game.rooms import manager


def test_sanitize_chat_message():
    assert sanitize_chat_message("  hello\nthere\t ") == "hello there"
    try:
        sanitize_chat_message("")
        raise AssertionError("expected ChatError")
    except ChatError:
        pass



def _lobby(client, names=("alice", "bob")):
    host = names[0]
    room = client.post("/rooms", json={"name": host, "difficulty": 1}).json()
    code = room["join_code"]
    for name in names[1:]:
        client.post(f"/rooms/{code}/join", json={"name": name})
    return code


def _start(client, names=("alice", "bob")):
    code = _lobby(client, names)
    host = names[0]
    started = client.post(f"/rooms/{code}/start", json={"name": host})
    assert started.status_code == 200
    return code, manager.get_by_code(code)


def test_valid_chat_broadcasts_to_room(client):
    code = _lobby(client)
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as alice:
        assert alice.receive_json()["type"] == "state"
        with client.websocket_connect(f"/ws/rooms/{code}?name=bob") as bob:
            assert alice.receive_json()["type"] == "state"
            assert bob.receive_json()["type"] == "state"
            alice.send_json({"type": "chat", "message": "  hello team  "})
            for sock in (alice, bob):
                payload = sock.receive_json()
                assert payload["type"] == "chat"
                assert payload["username"] == "alice"
                assert payload["message"] == "hello team"
                assert "timestamp" in payload


def test_chat_uses_socket_identity_not_payload_username(client):
    code = _lobby(client, names=("alice",))
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
        ws.receive_json()
        ws.send_json(
            {"type": "chat", "username": "eve", "message": "spoofed"}
        )
        payload = ws.receive_json()
        assert payload["type"] == "chat"
        assert payload["username"] == "alice"
        assert payload["message"] == "spoofed"


def test_empty_and_overlong_chat_rejected(client):
    code = _lobby(client, names=("alice",))
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
        ws.receive_json()
        ws.send_json({"type": "chat", "message": "   "})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert "empty" in error["message"].lower()

        ws.send_json({"type": "chat", "message": "x" * (MAX_CHAT_LEN + 1)})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert "200" in error["message"]


def test_chat_does_not_change_board(client):
    code, room = _start(client, names=("alice",))
    before = [row[:] for row in room.grid]
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
            ws.receive_json()
            ws.send_json({"type": "chat", "message": "nice move"})
            payload = ws.receive_json()
            assert payload["type"] == "chat"
            live = manager.get_by_code(code)
            assert live.grid == before
            assert live.status == "playing"


def test_chat_rate_limit(client):
    code = _lobby(client, names=("alice",))
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
        ws.receive_json()
        for i in range(5):
            ws.send_json({"type": "chat", "message": f"msg {i}"})
            assert ws.receive_json()["type"] == "chat"
        ws.send_json({"type": "chat", "message": "too many"})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert "quickly" in error["message"].lower()


def test_room_chat_is_isolated(client):
    code_a = _lobby(client, names=("alice",))
    code_b = _lobby(client, names=("bob",))
    with client.websocket_connect(f"/ws/rooms/{code_a}?name=alice") as alice:
        alice.receive_json()
        with client.websocket_connect(f"/ws/rooms/{code_b}?name=bob") as bob:
            bob.receive_json()
            alice.send_json({"type": "chat", "message": "only in a"})
            payload = alice.receive_json()
            assert payload["message"] == "only in a"
            bob.send_json({"type": "chat", "message": "only in b"})
            payload = bob.receive_json()
            assert payload["message"] == "only in b"


def test_chat_closed_after_give_up(client):
    code, _room = _start(client, names=("alice",))
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
        ws.receive_json()
        ws.send_json({"type": "give_up"})
        assert ws.receive_json()["type"] == "state"
        ws.send_json({"type": "chat", "message": "still here?"})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert "closed" in error["message"].lower()
