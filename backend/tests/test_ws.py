from __future__ import annotations

from app.game.rooms import manager


def _create_and_start(client, names=("alice", "bob"), difficulty=1):
    host = names[0]
    room = client.post("/rooms", json={"name": host, "difficulty": difficulty}).json()
    code = room["join_code"]
    for name in names[1:]:
        client.post(f"/rooms/{code}/join", json={"name": name})
    started = client.post(f"/rooms/{code}/start", json={"name": host})
    assert started.status_code == 200, started.text
    return code, manager.get_by_code(code)


def test_set_cell_broadcasts_to_other_players(client):
    code, room = _create_and_start(client)
    empty = next(
        (r, c)
        for r in range(9)
        for c in range(9)
        if room.puzzle[r][c] == 0
    )

    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as alice:
        alice.receive_json()
        with client.websocket_connect(f"/ws/rooms/{code}?name=bob") as bob:
            alice.receive_json()
            bob.receive_json()
            alice.send_json(
                {"type": "set_cell", "row": empty[0], "col": empty[1], "value": 9}
            )
            alice_state = alice.receive_json()
            bob_state = bob.receive_json()
            assert alice_state["grid"][empty[0]][empty[1]] == 9
            assert bob_state["grid"][empty[0]][empty[1]] == 9


def test_cannot_overwrite_clue(client):
    code, room = _create_and_start(client, names=("alice",))
    clue = next(
        (r, c)
        for r in range(9)
        for c in range(9)
        if room.puzzle[r][c] != 0
    )
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
        ws.receive_json()
        ws.send_json(
            {"type": "set_cell", "row": clue[0], "col": clue[1], "value": 1}
        )
        error = ws.receive_json()
        assert error["type"] == "error"


def test_solving_splits_points(client):
    code, room = _create_and_start(client, difficulty=1)
    empties = [
        (r, c)
        for r in range(9)
        for c in range(9)
        if room.puzzle[r][c] == 0
    ]
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as alice:
        alice.receive_json()
        with client.websocket_connect(f"/ws/rooms/{code}?name=bob") as bob:
            alice.receive_json()
            bob.receive_json()
            for r, c in empties:
                alice.send_json(
                    {
                        "type": "set_cell",
                        "row": r,
                        "col": c,
                        "value": room.solution[r][c],
                    }
                )
                state = alice.receive_json()
                bob.receive_json()
            assert state["status"] == "solved"

    board = client.get("/leaderboard").json()
    by_name = {row["name"]: row for row in board}
    assert by_name["alice"]["points"] == 10
    assert by_name["bob"]["points"] == 10
    assert by_name["alice"]["games_played"] == 1
    assert by_name["bob"]["games_played"] == 1


def test_give_up_reveals_solution_and_awards_zero(client):
    code, room = _create_and_start(client, difficulty=5)
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as alice:
        alice.receive_json()
        with client.websocket_connect(f"/ws/rooms/{code}?name=bob") as bob:
            alice.receive_json()
            bob.receive_json()
            alice.send_json({"type": "give_up"})
            state = alice.receive_json()
            other = bob.receive_json()
            assert state["status"] == "given_up"
            assert state["solution"] == room.solution
            assert other["status"] == "given_up"

    board = client.get("/leaderboard").json()
    by_name = {row["name"]: row for row in board}
    assert by_name["alice"]["points"] == 0
    assert by_name["bob"]["points"] == 0
    assert by_name["alice"]["games_played"] == 1
    assert by_name["bob"]["games_played"] == 1


def test_wrong_complete_grid_does_not_solve(client):
    code, room = _create_and_start(client, names=("alice",), difficulty=1)
    empties = [
        (r, c)
        for r in range(9)
        for c in range(9)
        if room.puzzle[r][c] == 0
    ]
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
        ws.receive_json()
        for r, c in empties:
            wrong = room.solution[r][c] % 9 + 1
            ws.send_json({"type": "set_cell", "row": r, "col": c, "value": wrong})
            state = ws.receive_json()
        assert state["status"] == "playing"


def test_unknown_player_cannot_connect(client):
    code, _room = _create_and_start(client, names=("alice",))
    with client.websocket_connect(f"/ws/rooms/{code}?name=eve") as ws:
        error = ws.receive_json()
        assert error["type"] == "error"


def test_last_player_leave_abandons_game(client):
    code, _room = _create_and_start(client, names=("alice",), difficulty=3)
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as ws:
        ws.receive_json()
        ws.send_json({"type": "leave"})

    board = client.get("/leaderboard").json()
    by_name = {row["name"]: row for row in board}
    assert by_name["alice"]["points"] == 0
    assert by_name["alice"]["games_played"] == 1
    assert manager.get_by_code(code) is None or manager.get_by_code(code).status == "abandoned"


def test_leaver_gets_zero_others_can_still_score(client):
    code, room = _create_and_start(client, names=("alice", "bob"), difficulty=1)
    with client.websocket_connect(f"/ws/rooms/{code}?name=alice") as alice:
        alice.receive_json()
        with client.websocket_connect(f"/ws/rooms/{code}?name=bob") as bob:
            alice.receive_json()
            bob.receive_json()
            bob.send_json({"type": "leave"})
            state = alice.receive_json()
            assert "bob" not in state["players"]

        empties = [
            (r, c)
            for r in range(9)
            for c in range(9)
            if room.puzzle[r][c] == 0
        ]
        for r, c in empties:
            alice.send_json(
                {"type": "set_cell", "row": r, "col": c, "value": room.solution[r][c]}
            )
            state = alice.receive_json()
        assert state["status"] == "solved"

    board = client.get("/leaderboard").json()
    by_name = {row["name"]: row for row in board}
    assert by_name["bob"]["points"] == 0
    assert by_name["bob"]["games_played"] == 1
    assert by_name["alice"]["points"] == 20
    assert by_name["alice"]["games_played"] == 1
