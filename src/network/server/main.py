import threading, socket, orjson
import sys, pathlib, time
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(parent_dir))
from collections import deque
from player_conn import PlayerConnection
from matchmaker import Matchmaker
from src.network.database.players_db import get_player_by_name_tag, register_player, set_player_offline, set_player_online, set_all_players_offline

HOST = '0.0.0.0'
PORT = 5555

def player_reception_action(conn):
    buffer = ""
    while True:
        data = conn.recv(4096)
        if not data:
            return (None, None, None)
        buffer += data.decode('utf-8')
        if '\n' in buffer:
            msg, _ = buffer.split('\n', 1)
            parsed = orjson.loads(msg.encode('utf-8'))
            if parsed.get("type") == "client_access-login":
                name = parsed.get("name")
                hashtag = parsed.get("hashtag")
                player_data = get_player_by_name_tag(name, hashtag)
                if not player_data:
                    print(f"[ERROR] Player {name} with hashtag {hashtag} not found in database.")
                    msg = {
                        'type': 'player_not_found',
                        'message': f'Player {name} with hashtag {hashtag} not found.'
                    }
                    msg = orjson.dumps(msg).decode('utf-8') + '\n'
                    conn.send(msg.encode('utf-8'))
                    return (None, None, None)
                else:
                    if player_data.get("is_online", False):
                        print(f"[ERROR] Player {name} with hashtag {hashtag} is already online.")
                        msg = {
                            'type': 'player_already_online',
                            'message': f'Player {name} with hashtag {hashtag} is already online.'
                        }
                        msg = orjson.dumps(msg).decode('utf-8') + '\n'
                        conn.send(msg.encode('utf-8'))
                        return (None, None, None)
                    
                    set_player_online(player_data['id'])
                    return (player_data['id'], player_data['name'], player_data['hashtag'])
            if parsed.get("type") == "client_access-signup":
                name = parsed.get("name")
                hashtag = parsed.get("hashtag")
                try:
                    player_data = register_player(name, hashtag)
                    set_player_online(player_data['id'])
                    return (player_data['id'], player_data['name'], player_data['hashtag'])
                except ValueError as e:
                    print(f"[ERROR] Registration failed: {e}")
                    msg = {
                        'type': 'registration_error',
                        'message': str(e)
                    }
                    msg = orjson.dumps(msg).decode('utf-8') + '\n'
                    conn.send(msg.encode('utf-8'))
                    return (None, None, None)

def get_match_request(conn):
    buffer = ""
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                return (None, None)
            buffer += data.decode('utf-8')
            if '\n' in buffer:
                msg, _ = buffer.split('\n', 1)
                parsed = orjson.loads(msg.encode('utf-8'))
                if parsed.get("type") == "match_request":
                    mode = parsed["data"].get("mode")
                    if mode in ["OVV2", "OVV3", "OVV4", "TVV2", "SPFM"]:
                        return (mode, parsed["data"]["player_operator"])
                    else:
                        return ('NVO', None)
        except (socket.timeout, TimeoutError):
            continue
        except Exception as e:
            print(f"[MATCH REQUEST ERROR]: {e}")
            return (None, None)
        
def process_player_message(conn):
    buffer = ""
    try:
        data = conn.recv(4096)
        if not data:
            return None
        buffer += data.decode('utf-8')
        if '\n' in buffer:
            msg, buffer = buffer.split('\n', 1)
            return orjson.loads(msg.encode('utf-8'))
    except (socket.timeout, TimeoutError):
        return None
    except Exception as e:
        print(f"[PROCESS MESSAGE ERROR]: {e}")
        return None
    return None
        
class Server:
    def __init__(self):
        set_all_players_offline()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")

        self.players = dict()
        self.players_lock = threading.Lock()
        self.matchmaker = Matchmaker(self)

    def run(self):
        self.running = True
        threading.Thread(target=self.player_reception, daemon=True).start()
        threading.Thread(target=self.cleanup_disconnected_players, daemon=True).start()
        threading.Thread(target=self.matchmaker.run_OVV2, daemon=True).start()
        threading.Thread(target=self.matchmaker.run_OVV3, daemon=True).start()
        threading.Thread(target=self.matchmaker.run_OVV4, daemon=True).start()
        threading.Thread(target=self.matchmaker.run_TVV2, daemon=True).start()
        threading.Thread(target=self.matchmaker.run_SPFM, daemon=True).start()
        threading.Thread(target=self.matchmaker.run_queue_cleanup, daemon=True).start()

    def player_reception(self):
        while self.running:
            conn, addr = self.server_socket.accept()
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            
            threading.Thread(target=self.handle_new_connection, args=(conn, addr), daemon=True).start()
        
        self.running = False

    def handle_new_connection(self, conn, addr):
        player_id, player_name, player_hashtag = player_reception_action(conn=conn)
        if player_id is None:
            print(f"[FAILED] COULD NOT FETCH PLAYER DATA FROM CONNECTION {addr}")
            conn.close()
            return
            
        player = PlayerConnection(conn, addr, player_id=player_id, player_name=player_name, player_hashtag=player_hashtag)
        print(f"[CONNECTED] {addr} --> {player_id}/{player_name}/{player_hashtag}")
        with self.players_lock:
            self.players[str(player_id)] = player

        self.handle_player_requests(player)

    def handle_player_requests(self, player):
        if not self.running:
            return
        
        while player.is_alive():
            try:
                message = process_player_message(player.conn)
                
                if not message:
                    continue
                
                message_type = message.get("type")
                
                if not player.in_queue:
                    if message_type == "invitation":
                        name = message["data"].get("name")
                        hashtag = message["data"].get("hashtag")
                        player_data = get_player_by_name_tag(name, hashtag)
                        
                        if not player_data:
                            print(f"[ERROR] Player {name} with hashtag {hashtag} not found in database.")
                            player.send({
                                'type': 'player_not_found',
                                'message': f'Player {name} with hashtag {hashtag} not found.'
                            })
                            continue
                        
                        if not player_data.get('is_online', False):
                            print(f"[ERROR] Player {name} with hashtag {hashtag} is offline.")
                            player.send({
                                'type': 'player_offline',
                                'message': f'Player {name} with hashtag {hashtag} is offline.'
                            })
                            continue

                        if player_data.get('id') == player.id:
                            print(f"[ERROR] Player {name} with hashtag {hashtag} cannot invite themselves.")
                            player.send({
                                'type': 'player_cannot_invite_self',
                                'message': f'You cannot invite yourself.'
                            })
                            continue
                        
                        invited_player = None
                        with self.players_lock:
                            invited_player = self.players.get(str(player_data.get("id")))
                        
                        if invited_player is None:
                            continue
                        
                        if not invited_player.is_alive():
                            continue
                        
                        if invited_player.invitation_ongoing or not invited_player.player_available:
                            player.send({
                                "type": "player_has_invitation",
                                "message": f"Player {invited_player.name}#{invited_player.hashtag} is busy."
                            })
                            continue

                        invited_player.invitation_received = True
                        invited_player.invitation_ongoing = True
                        invited_player.player_invitation_info = {
                            "id": player.id,
                            "name": player.name,
                            "hashtag": player.hashtag
                        }
                        
                        player.invitation_received = True
                        player.invitation_ongoing = True
                        
                        player.send({
                            "type": "invitation_sent_successfully",
                            "data": {
                                "id": invited_player.id,
                                "name": invited_player.name,
                                "hashtag": invited_player.hashtag
                            }
                        })
                        player.player_invitation_info = {
                            "id": invited_player.id,
                            "name": invited_player.name,
                            "hashtag": invited_player.hashtag
                        }

                        invited_player.send({
                            "type": "invitation_from_player",
                            "data": {
                                "id": player.id,
                                "name": player.name,
                                "hashtag": player.hashtag
                            }
                        })
                    
                    elif message_type == "invitation_acceptance" or message_type == "invitation_rejection":
                        player_accepted = message_type == "invitation_acceptance"
                        
                        if not player.invitation_received or not player.invitation_ongoing:
                            continue
                        
                        inviting_player = None
                        inviting_player_id = player.player_invitation_info.get("id")
                        
                        with self.players_lock:
                            inviting_player = self.players.get(str(inviting_player_id))
                        
                        if inviting_player is None or not inviting_player.is_alive() or not inviting_player.invitation_ongoing:
                            player.send_clear_invitation_info_accepted()
                            player.send({
                                "type": "invitation_rejected",
                                "message": "Invitation has expired or the inviting player is no longer available."
                            })
                            continue
                        
                        player.invitation_accepted = player_accepted
                        player.invitation_ongoing = False
                        inviting_player.invitation_accepted = player_accepted
                        inviting_player.invitation_ongoing = False
                        
                        if player_accepted:
                            invitation_pair_id = f"{inviting_player.id}_{player.id}"
                            
                            inviting_player.invitation_pair_id = invitation_pair_id
                            player.invitation_pair_id = invitation_pair_id
                            
                            inviting_player.send({
                                "type": "invitation_acceptance",
                            })
                            
                            player.send({
                                "type": "invitation_acceptance",
                            })
                        else:
                            inviting_player.send({
                                "type": "invitation_rejected",
                            })
                            
                            player.send({
                                "type": "invitation_rejected",
                            })
                            
                            inviting_player.send_clear_invitation_info_accepted()
                            player.send_clear_invitation_info_accepted()

                    elif message_type == "match_request":
                        mode = message["data"].get("mode")
                        player_operator = message["data"].get("player_operator")
                        
                        if mode not in ["OVV2", "OVV3", "OVV4", "TVV2", "SPFM"]:
                            print(f"[SERVER][FAILED] NOT A VALID MODE")
                            continue
                        
                        successful = False
                        
                        if mode == "OVV2":
                            with self.matchmaker.OVV2_LOCK:
                                self.matchmaker.OVV2_queue.append(player)
                                successful = True
                        elif mode == "OVV3":
                            with self.matchmaker.OVV3_LOCK:
                                self.matchmaker.OVV3_queue.append(player)
                                successful = True
                        elif mode == "OVV4":
                            with self.matchmaker.OVV4_LOCK:
                                self.matchmaker.OVV4_queue.append(player)
                                successful = True
                        elif mode == "TVV2":
                            with self.matchmaker.TVV2_LOCK:
                                self.matchmaker.TVV2_queue.append(player)
                                successful = True
                        elif mode == "SPFM":
                            print(f"[SERVER] Player {player.name}#{player.hashtag} requested SPFM mode")
                            if not hasattr(player, 'invitation_pair_id') or not player.invitation_pair_id:
                                print(f"[SERVER][ERROR] Player {player.name} sent SPFM request without invitation pair ID")
                                continue
                            
                            with self.matchmaker.SPFM_LOCK:
                                if player in self.matchmaker.SPFM_waiting:
                                    continue
                                
                                partner_waiting = None
                                for waiting_player in list(self.matchmaker.SPFM_waiting):
                                    if (waiting_player.invitation_pair_id == player.invitation_pair_id and 
                                        waiting_player.id != player.id):
                                        partner_waiting = waiting_player
                                        self.matchmaker.SPFM_waiting.remove(waiting_player)
                                        break
                                
                                if partner_waiting:
                                    self.matchmaker.SPFM_queue.append((partner_waiting, player))
                                    successful = True
                                    print(f"[SPFM] Matched {partner_waiting.name} with {player.name}")
                                else:
                                    self.matchmaker.SPFM_waiting.append(player)
                                    successful = True
                                    print(f"[SPFM] {player.name} added to waiting list")
                        
                        if successful:
                            with player.queue_lock:
                                player.in_queue = True
                                player.queue_mode = mode
                                player.player_operator = player_operator
                                player.send({
                                    "type": "match_request_accepted",
                                    "mode": mode,
                                    "player_operator": player_operator,
                                })
                                print("[SERVER] Sent Mode Confirmation")

                    elif message_type == "invitation_cancel":
                        print(f"[SERVER] Player {player.name}#{player.hashtag} requested invitation cancellation")
                        
                        if not player.invitation_ongoing:
                            player.send({
                                "type": "invitation_cancel_accepted",
                                "message": "You have no ongoing invitation"
                            })
                            continue
                        
                        player.send({
                            "type": "invitation_cancel_accepted",
                        })
                        
                        inviting_player = None
                        inviting_player_id = player.player_invitation_info.get("id")
                        
                        with self.players_lock:
                            inviting_player = self.players.get(str(inviting_player_id))
                        
                        if inviting_player and inviting_player.is_alive():
                            inviting_player.send({
                                "type": "invitation_cancel_accepted",
                            })
                            inviting_player.clear_invitation_info()

                        player.clear_invitation_info()

                else:
                    if message_type == "match_request_cancel":
                        print(f"[SERVER] Player {player.name}#{player.hashtag} requested match cancellation")
                        
                        if not player.in_queue:
                            player.send({
                                "type": "match_request_cancelled",
                                "message": "You were not in a queue"
                            })
                            continue
                        
                        mode = player.queue_mode
                        
                        if mode == "OVV2":
                            with self.matchmaker.OVV2_LOCK:
                                if player in self.matchmaker.OVV2_queue:
                                    self.matchmaker.OVV2_queue.remove(player)
                                    print(f"[SERVER] Removed {player.name}#{player.hashtag} from OVV2 queue")
                        
                        elif mode == "OVV3":
                            with self.matchmaker.OVV3_LOCK:
                                if player in self.matchmaker.OVV3_queue:
                                    self.matchmaker.OVV3_queue.remove(player)
                                    print(f"[SERVER] Removed {player.name}#{player.hashtag} from OVV3 queue")
                        
                        elif mode == "OVV4":
                            with self.matchmaker.OVV4_LOCK:
                                if player in self.matchmaker.OVV4_queue:
                                    self.matchmaker.OVV4_queue.remove(player)
                                    print(f"[SERVER] Removed {player.name}#{player.hashtag} from OVV4 queue")
                        
                        elif mode == "TVV2":
                            with self.matchmaker.TVV2_LOCK:
                                if player in self.matchmaker.TVV2_queue:
                                    self.matchmaker.TVV2_queue.remove(player)
                                    print(f"[SERVER] Removed {player.name}#{player.hashtag} from TVV2 queue")
                        
                        elif mode == "SPFM":
                            with self.matchmaker.SPFM_LOCK:
                                if player in self.matchmaker.SPFM_waiting:
                                    self.matchmaker.SPFM_waiting.remove(player)
                                    print(f"[SERVER] Removed {player.name}#{player.hashtag} from SPFM waiting list")
                                
                                to_remove = None
                                for pair in self.matchmaker.SPFM_queue:
                                    if player in pair:
                                        to_remove = pair
                                        break
                                
                                if to_remove:
                                    self.matchmaker.SPFM_queue.remove(to_remove)
                                    print(f"[SERVER] Removed {player.name}#{player.hashtag} from SPFM queue")
                        
                        with player.queue_lock:
                            player.in_queue = False
                            player.queue_mode = None
                            player.player_operator = None
                        
                        player.send({
                            "type": "match_request_cancelled",
                            "message": "Match request cancelled successfully"
                        })
                        print(f"[SERVER] Match cancellation processed for {player.name}#{player.hashtag}")

            except Exception as e:
                print(f"[PLAYER HANDLER ERROR] {e}")
                continue

    def cleanup_disconnected_players(self):
        if not self.running:
            return
        while self.running:
            time.sleep(5)
            with self.players_lock:
                before = len(self.players)
                disconnected_players = []

                # FINDING DISCONNECTED PLAYERS AND MARKING DISCONNECTED
                for player in self.players.values():
                    if not player.is_alive():
                        disconnected_players.append(player)
                
                # CHNAGING ONLINE STATUS FOR DISCONNECTED PLAYERS
                for player in disconnected_players:
                    print(f"[CLEANUP] Marking {player.name}#{player.hashtag} as offline")
                    set_player_offline(player.id)
                
                # REMOVING
                self.players = {str(p.id):p for p in self.players.values() if p.is_alive()}
                after = len(self.players)
                
                if before != after:
                    print(f"[CLEANUP] Removed {before - after} disconnected players")


if __name__ == "__main__":
    server = Server()
    server.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        with server.players_lock:
            for player in server.players.values():
                set_player_offline(player.id)
        server.running = False