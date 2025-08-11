import time, threading
import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(parent_dir))
from src.network.multiplayer_modes.NMOVV2.NMOVV2_Server import NMOVV2Server
from src.network.multiplayer_modes.NMOVV3.NMOVV3_Server import NMOVV3Server
from src.network.multiplayer_modes.NMOVV4.NMOVV4_Server import NMOVV4Server
from src.network.multiplayer_modes.NMTVV2.NMTVV2_Server import NMTVV2Server

def mode_selector(mode, arena_ID, PINFS, p1, p2, p3, p4):
    if mode == 'OVV2' or mode == 'SPFM':
        return NMOVV2Server(Arena_ID=arena_ID, PINFS=PINFS, P1_CONN=p1, P2_CONN=p2)
    if mode == 'OVV3':
        return NMOVV3Server(Arena_ID=arena_ID, PINFS=PINFS, P1_CONN=p1, P2_CONN=p2, P3_CONN=p3)
    if mode == 'OVV4':
        return NMOVV4Server(Arena_ID=arena_ID, PINFS=PINFS, P1_CONN=p1, P2_CONN=p2, P3_CONN=p3, P4_CONN=p4)
    if mode == 'TVV2':
        return NMTVV2Server(Arena_ID=arena_ID, PINFS=PINFS, P1_CONN=p1, P2_CONN=p2, P3_CONN=p3, P4_CONN=p4)

def start_match(server, mode, arena_ID, p1, p2, p3=None, p4=None):

    players = [p1, p2]
    if p3:
        players.append(p3)
    if p4:
        players.append(p4)

    PINFS = {}
    for player in players:
        PINFS[str(player.player_number)] = {
            "id": player.id,
            "name": player.name,
            "hashtag": player.hashtag,
            "operator": player.player_operator
        }
    print(f"[SERVER] PINFS {PINFS} in Arena Number {arena_ID}")
    game = mode_selector(mode, arena_ID, PINFS, p1, p2, p3, p4)
    physics_rate = 1.0 / 60.0  # 60 Hz physics
    network_rate = 1.0 / 60.0  # 30 Hz network updates
    physics_accum = 0.0
    network_accum = 0.0
    prev_time = time.perf_counter()
    match_crashed = False
    try:
        while True:
            now = time.perf_counter()
            delta = now - prev_time
            prev_time = now
            physics_accum += delta
            network_accum += delta

            disconnected = [p for p in players if not p.is_alive()]
            if disconnected:
                for p in disconnected:
                    print(f"[GAME LOOP] Player {p.name} disconnected!")
                    match_crashed = True
                    return
                
            for p in players:
                latest = p.get_snapshot()
                if p.player_number == 1:
                    game.P1_CONN.snapshot = latest
                elif p.player_number == 2:
                    game.P2_CONN.snapshot = latest
                elif p.player_number == 3:
                    game.P3_CONN.snapshot = latest
                elif p.player_number == 4:
                    game.P4_CONN.snapshot = latest

            physics_updates = 0
            while physics_accum >= physics_rate and physics_updates < 1:
                game.update()
                physics_updates += 1
                physics_accum -= physics_rate

            if game.match_over:
                return

            if network_accum >= network_rate:
                state = {
                    "type": "state",
                    "players": [
                        {
                            **p.get_snapshot(),
                            "player_number": p.player_number,
                            **getattr(game, f"P{p.player_number}_ADDITIONAL_INFO", {})
                        }
                        for p in players
                    ],
                    "game_stats": game.snapshot
                }
                for p in players:
                    p.send(state)
                network_accum = 0.0

            frame_time = time.perf_counter() - now
            sleep_time = max(0, (1/60) - frame_time)
            if sleep_time > 0.001:
                time.sleep(sleep_time)
    except Exception as e:
        print(f"[ERROR] Match crashed: {e}")
    finally:
        print(f"[GAME LOOP] Match ended: {game.str_match_end}")
        for p in players:
            if p.is_alive():
                if match_crashed:
                    p.send_forced_exit_match()
                else:
                    p.send_match_over(game.winner)
                threading.Thread(
                    target=server.handle_player_requests,
                    args=(p,),
                    daemon=True
                ).start()
