import threading, time, random

from collections import deque
from game_loop import start_match

class Matchmaker:
    def __init__(self, server):
        self.server = server
        self.OVV2_queue = deque()
        self.OVV2_LOCK = threading.Lock()

        self.OVV3_queue = deque()
        self.OVV3_LOCK = threading.Lock()
        
        self.OVV4_queue = deque()
        self.OVV4_LOCK = threading.Lock()

        self.TVV2_queue = deque()
        self.TVV2_LOCK = threading.Lock()

        self.SPFM_queue = deque()
        self.SPFM_LOCK = threading.Lock()
        self.SPFM_waiting = []

    def run_queue_cleanup(self):
        print("[MATCHMAKER - CLEANUP] Running...")
        while True:
            time.sleep(10)
            self.cleanup_queues()

    def cleanup_queues(self):
        
        total_removed = 0
        
        # Cleanup OVV2 queue
        with self.OVV2_LOCK:
            original_length = len(self.OVV2_queue)
            self.OVV2_queue = deque([player for player in self.OVV2_queue if player.in_queue])
            removed_ovv2 = original_length - len(self.OVV2_queue)
            total_removed += removed_ovv2
            if removed_ovv2 > 0:
                print(f"[MATCHMAKER] Removed {removed_ovv2} players from OVV2 queue")
        
        # Cleanup OVV3 queue
        with self.OVV3_LOCK:
            original_length = len(self.OVV3_queue)
            self.OVV3_queue = deque([player for player in self.OVV3_queue if player.in_queue])
            removed_ovv3 = original_length - len(self.OVV3_queue)
            total_removed += removed_ovv3
            if removed_ovv3 > 0:
                print(f"[MATCHMAKER] Removed {removed_ovv3} players from OVV3 queue")
        
        # Cleanup OVV4 queue
        with self.OVV4_LOCK:
            original_length = len(self.OVV4_queue)
            self.OVV4_queue = deque([player for player in self.OVV4_queue if player.in_queue])
            removed_ovv4 = original_length - len(self.OVV4_queue)
            total_removed += removed_ovv4
            if removed_ovv4 > 0:
                print(f"[MATCHMAKER] Removed {removed_ovv4} players from OVV4 queue")
        
        # Cleanup TVV2 queue
        with self.TVV2_LOCK:
            original_length = len(self.TVV2_queue)
            self.TVV2_queue = deque([player for player in self.TVV2_queue if player.in_queue])
            removed_tvv2 = original_length - len(self.TVV2_queue)
            total_removed += removed_tvv2
            if removed_tvv2 > 0:
                print(f"[MATCHMAKER] Removed {removed_tvv2} players from TVV2 queue")

        # Cleanup SPF Match queue
        with self.SPFM_LOCK:
            original_length = len(self.SPFM_queue)
            
            self.SPFM_queue = deque([
                pair for pair in self.SPFM_queue 
                if isinstance(pair, tuple) and len(pair) == 2 and pair[0].in_queue and pair[1].in_queue
            ])
            
            self.SPFM_waiting = [player for player in self.SPFM_waiting if player.in_queue]
            
            removed_spfm = original_length - len(self.SPFM_queue)
            total_removed += removed_spfm
            if removed_spfm > 0:
                print(f"[MATCHMAKER] Removed {removed_spfm} pairs from SPF Match queue")

    def revive_conn(self, conn, queue_type: str):
        conn_back = conn if conn.is_alive() else None
        if conn_back:
            if queue_type == "TVV2":
                self.TVV2_queue.appendleft(conn_back)
            elif queue_type == "OVV2":
                self.OVV2_queue.appendleft(conn_back)
            elif queue_type == "OVV3":
                self.OVV3_queue.appendleft(conn_back)
            elif queue_type == "OVV4":
                self.OVV4_queue.appendleft(conn_back)
            else:
                print("[SERVER - MATCHMAKE] ---> IMPOSSIBLE MODE")
            conn_back.in_queue = True

    def synchronize_operators(self, mode, players):
        print(f"[MATCHMAKER] Synchronizing operators for {len(players)} players")

        random_arena_id = random.randrange(1, 5, 1)

        print(f"[MATCHMAKER] ARENA SELECTED --> {random_arena_id}")

        operators = {}
        for player in players:
            operators[str(player.player_number)] = {
                "id": player.id,
                "name": player.name,
                "hashtag": player.hashtag,
                "operator": player.player_operator,
                "player_number": player.player_number
            }
        
        opponent_ready_state = {
            "type": "opp_ready",
            "operators": operators
        }

        for player in players:
            player.send(opponent_ready_state)

        operator_sync = {
            "type": "operator_sync",
            "AID": random_arena_id,
            "operators": operators
        }
        
        for player in players:
            player.send(operator_sync)
        
        confirmed_players = set()
        start_time = time.time()
        
        while len(confirmed_players) < len(players):
            if time.time() - start_time > 15:
                print("[MATCHMAKER] Operator sync timed out")
                for player in players:
                    if player.is_alive():
                        if mode != "SPFM":
                            self.revive_conn(player, mode)
                return
            
            for player in players:
                if player.id in confirmed_players:
                    continue
                    
                confirmation = player.get_operator_confirmation()
                if confirmation:
                    print(f"[SERVER] Player {player.id}/{player.name}/{player.hashtag} --> PN: {player.player_number} has confirmed the operators sync data")
                    confirmed_players.add(player.id)
            
            time.sleep(0.1)
        
        all_confirmed = {
            "type": "all_operators_confirmed",
            "operators": {}
        }
        
        for player in players:
            player.send(all_confirmed)

        if mode == 'SPFM':
            for player in players:
                player.invitation_pair_id = None
        
        print(f"[MATCH FOUND] Starting match with {len(players)} players in mode {mode} in Arena {random_arena_id}")
        threading.Thread(
            target=start_match,
            args=(self.server, mode, random_arena_id, ) + tuple(players),
            daemon=True
        ).start()

    def run_SPFM(self):
        print("[MATCHMAKER - SPFM] Running...")
        while True:
            time.sleep(1)

            if len(self.SPFM_queue) >= 1:
                with self.SPFM_LOCK:
                    player_pair = self.SPFM_queue.popleft()
                    p1, p2 = player_pair
                    
                    p1.in_queue = False
                    p1.player_available = False
                    p2.in_queue = False
                    p2.player_available = False

                    if not p1.is_alive():
                        print(f"[MATCHMAKER - SPFM] Removing disconnected {p1.name}")
                        continue

                    if not p2.is_alive():
                        print(f"[MATCHMAKER - SPFM] Removing disconnected {p2.name}")
                        continue

                    p1.player_number = 1
                    p2.player_number = 2

                    print(f"[MATCH FOUND - SPFM] {p1.name} vs {p2.name}")
                    threading.Thread(
                        target=self.synchronize_operators,
                        args=('SPFM', [p1, p2]),
                        daemon=True
                    ).start()

    def run_OVV2(self):
        print("[MATCHMAKER - OVV2] Running...")
        while True:
            time.sleep(1)

            if len(self.OVV2_queue) >= 2:
                with self.OVV2_LOCK:
                    p1 = self.OVV2_queue.popleft()
                    p2 = self.OVV2_queue.popleft()
                    p1.in_queue = False
                    p1.player_available = False
                    p2.in_queue = False
                    p2.player_available = False

                    if not p1.is_alive():
                        print(f"[MATCHMAKER - OVV2] Removing disconnected {p1.name}")
                        self.revive_conn(p2, "OVV2")
                        continue

                    if not p2.is_alive():
                        print(f"[MATCHMAKER - OVV2] Removing disconnected {p2.name}")
                        self.revive_conn(p1, "OVV2")
                        continue
                    
                    p1.player_number = 1
                    p2.player_number = 2
                    print(f"[MATCH FOUND] {p1.name} vs {p2.name}")
                    threading.Thread(
                        target=self.synchronize_operators,
                        args=('OVV2', [p1, p2]),
                        daemon=True
                    ).start()

    def run_OVV3(self):
        print("[MATCHMAKER - OVV3] Running...")
        while True:
            time.sleep(1)

            if len(self.OVV3_queue) >= 3:
                with self.OVV3_LOCK:
                    p1 = self.OVV3_queue.popleft()
                    p2 = self.OVV3_queue.popleft()
                    p3 = self.OVV3_queue.popleft()
                    p1.in_queue = False
                    p1.player_available = False
                    p2.in_queue = False
                    p2.player_available = False
                    p3.in_queue = False
                    p3.player_available = False

                    if not p1.is_alive():
                        print(f"[MATCHMAKER - OVV3] Removing disconnected {p1.name}")
                        self.revive_conn(p3, "OVV3")
                        self.revive_conn(p2, "OVV3")
                        continue

                    if not p2.is_alive():
                        print(f"[MATCHMAKER - OVV3] Removing disconnected {p2.name}")
                        self.revive_conn(p3, "OVV3")
                        self.revive_conn(p1, "OVV3")
                        continue
                
                    if not p3.is_alive():
                        print(f"[MATCHMAKER - OVV3] Removing disconnected {p3.name}")
                        self.revive_conn(p2, "OVV3")
                        self.revive_conn(p1, "OVV3")
                        continue
                    
                    p1.player_number = 1
                    p2.player_number = 2
                    p3.player_number = 3
                    print(f"[MATCH FOUND] {p1.name} vs {p2.name} vs {p3.name}")
                    threading.Thread(
                        target=self.synchronize_operators,
                        args=('OVV3', [p1, p2, p3]),
                        daemon=True
                    ).start()

    def run_OVV4(self):
        print("[MATCHMAKER - OVV4] Running...")
        while True:
            time.sleep(1)

            if len(self.OVV4_queue) >= 4:
                with self.OVV4_LOCK:
                    p1 = self.OVV4_queue.popleft()
                    p2 = self.OVV4_queue.popleft()
                    p3 = self.OVV4_queue.popleft()
                    p4 = self.OVV4_queue.popleft()
                    p1.in_queue = False
                    p1.player_available = False
                    p2.in_queue = False
                    p2.player_available = False
                    p3.in_queue = False
                    p3.player_available = False
                    p4.in_queue = False
                    p4.player_available = False

                    if not p1.is_alive():
                        print(f"[MATCHMAKER - OVV4] Removing disconnected {p1.name}")
                        self.revive_conn(p4, "OVV4")
                        self.revive_conn(p3, "OVV4")
                        self.revive_conn(p2, "OVV4")
                        continue

                    if not p2.is_alive():
                        print(f"[MATCHMAKER - OVV4] Removing disconnected {p2.name}")
                        self.revive_conn(p4, "OVV4")
                        self.revive_conn(p3, "OVV4")
                        self.revive_conn(p1, "OVV4")
                        continue

                    if not p3.is_alive():
                        print(f"[MATCHMAKER - OVV4] Removing disconnected {p3.name}")
                        self.revive_conn(p4, "OVV4")
                        self.revive_conn(p2, "OVV4")
                        self.revive_conn(p1, "OVV4")
                        continue

                    if not p4.is_alive():
                        print(f"[MATCHMAKER - OVV4] Removing disconnected {p4.name}")
                        self.revive_conn(p3, "OVV4")
                        self.revive_conn(p2, "OVV4")
                        self.revive_conn(p1, "OVV4")
                        continue

                    p1.player_number = 1
                    p2.player_number = 2
                    p3.player_number = 3
                    p4.player_number = 4
                    print(f"[MATCH FOUND] {p1.name} vs {p2.name} vs {p3.name} vs {p4.name}")
                    threading.Thread(
                        target=self.synchronize_operators,
                        args=('OVV4', [p1, p2, p3, p4]),
                        daemon=True
                    ).start()

    def run_TVV2(self):
        print("[MATCHMAKER - TVV2] Running...")
        while True:
            time.sleep(1)

            if len(self.TVV2_queue) >= 4:
                with self.TVV2_LOCK:
                    p1 = self.TVV2_queue.popleft()
                    p2 = self.TVV2_queue.popleft()
                    p3 = self.TVV2_queue.popleft()
                    p4 = self.TVV2_queue.popleft()
                    p1.in_queue = False
                    p1.player_available = False
                    p2.in_queue = False
                    p2.player_available = False
                    p3.in_queue = False
                    p3.player_available = False
                    p4.in_queue = False
                    p4.player_available = False

                    if not p1.is_alive():
                        print(f"[MATCHMAKER - TVV2] Removing disconnected {p1.name}")
                        self.revive_conn(p4, "TVV2")
                        self.revive_conn(p3, "TVV2")
                        self.revive_conn(p2, "TVV2")
                        continue

                    if not p2.is_alive():
                        print(f"[MATCHMAKER - TVV2] Removing disconnected {p2.name}")
                        self.revive_conn(p4, "TVV2")
                        self.revive_conn(p3, "TVV2")
                        self.revive_conn(p1, "TVV2")
                        continue

                    if not p3.is_alive():
                        print(f"[MATCHMAKER - TVV2] Removing disconnected {p3.name}")
                        self.revive_conn(p4, "TVV2")
                        self.revive_conn(p2, "TVV2")
                        self.revive_conn(p1, "TVV2")
                        continue

                    if not p4.is_alive():
                        print(f"[MATCHMAKER - TVV2] Removing disconnected {p4.name}")
                        self.revive_conn(p3, "TVV2")
                        self.revive_conn(p2, "TVV2")
                        self.revive_conn(p1, "TVV2")
                        continue

                    p1.player_number = 1
                    p2.player_number = 2
                    p3.player_number = 3
                    p4.player_number = 4
                    print(f"[MATCH FOUND] {p1.name} & {p2.name} vs {p3.name} & {p4.name}")
                    threading.Thread(
                        target=self.synchronize_operators,
                        args=('TVV2', [p1, p2, p3, p4]),
                        daemon=True
                    ).start()