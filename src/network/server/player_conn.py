import threading, time, socket, orjson
import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(parent_dir))
from collections import deque
from src.network.database.players_db import set_player_offline
class PlayerConnection:
    def __init__(self, conn, addr, player_id, player_name, player_hashtag):
        self.conn = conn
        self.conn.settimeout(0.001)
        self.addr = addr
        self.id = player_id
        self.name = player_name
        self.hashtag = player_hashtag
        self.in_queue = False
        self.queue_mode = None
        self.queue_lock = threading.Lock()
        self.player_available = True 
        self.player_operator = None
        self.player_number = -1
        self.snapshot = {}
        self.message_buffer = []
        self.buffer = ""
        self.input_buffer = deque(maxlen=60)
        self.lock = threading.Lock()
        self.last_snapshot_time = time.perf_counter()
        self.running = True
        self._disconnected = False
        self.invitation_received = False
        self.invitation_accepted = False
        self.invitation_ongoing = False
        self.invitation_pair_id = None
        self.player_invitation_info = {
            "id": None,
            "name": None,
            "hashtag": None
        }

        threading.Thread(target=self._recv_loop, daemon=True).start()

        self._incoming = deque()

        self.send({"type": "assign_id", "id": self.id})

    def clear_invitation_info(self):
        self.invitation_received = False
        self.invitation_accepted = False
        self.invitation_pair_id = None
        self.invitation_ongoing = False
        self.player_invitation_info = {
            "id": None,
            "name": None,
            "hashtag": None
        }

    def send_clear_invitation_info_accepted(self):
        message = {
            "type": "clear_invitation_info_accepted",
        }
        self.send(message)
        self.clear_invitation_info()

    def get_operator_confirmation(self):
        with self.lock:
            for message in list(self.message_buffer):
                if message.get("type") == "operator_confirm" and message["data"].get("id") == self.id:
                    self.message_buffer.remove(message)
                    return True
        return False

    def _recv_loop(self):
        while self.running:
            try:
                data = self.conn.recv(4096)
                if not data:
                    print(f"[DISCONNECT] {self.name} socket closed")
                    self.running = False
                    break
                self._incoming.append(data)
                
                while self._incoming:
                    data = self._incoming.popleft()
                    self.buffer += data.decode('utf-8')
                    while '\n' in self.buffer:
                        msg, self.buffer = self.buffer.split('\n', 1)
                        try:
                            parsed = orjson.loads(msg.encode('utf-8'))
                            snapshot_time = parsed["data"].get("timestamp", 0)

                            if parsed.get("type") == "operator_confirm":
                                with self.lock:
                                    self.message_buffer.append(parsed)
                                    continue
                            else:
                                if snapshot_time > self.last_snapshot_time:
                                    with self.lock:
                                        self.snapshot = parsed["data"]
                                        self.snapshot["id"] = self.id
                                        self.snapshot["name"] = self.name
                                        self.snapshot["hashtag"] = self.hashtag
                                        self.snapshot["player_number"] = self.player_number
                                        self.input_buffer.append(parsed["data"])
                                        self.last_snapshot_time = snapshot_time
                        except Exception as e:
                            print(f"[PARSE ERROR]: {e}")
            except socket.timeout:
                continue
            except Exception as e:
                # print(f"[PLAYER {self.id} RECV ERROR]:", e)
                self.running = False
                break

    def _mark_offline(self):
        if not self._disconnected:
            set_player_offline(self.id)
            self._disconnected = True

    def get_snapshot(self):
        with self.lock:
            if self.input_buffer:
                return self.input_buffer[-1]
            return self.snapshot

    def is_alive(self):
        return self.running

    def send(self, message: dict):
        try:
            msg = orjson.dumps(message).decode('utf-8') + '\n'
            self.conn.send(msg.encode('utf-8'))
        except (socket.timeout, BlockingIOError):
            return
        except Exception as e:
            print(f"[SEND ERROR] {self.name} hard disconnect: {e}")
            self.running = False

    def connection_reset(self):
        with self.queue_lock:
            self.in_queue = False
            self.queue_mode = None
            self.player_available = True
            self.snapshot = {}
            self.message_buffer = []
            self.buffer = ""
            self.input_buffer = deque(maxlen=60)
            self.player_operator = None
            self.player_number = -1
            self._incoming = deque()
        print(f"[SERVER] PLAYER {self.id}/{self.name}/{self.hashtag} CONNECTION RESET")

    def send_forced_exit_match(self):
        self.connection_reset()
        message = {
            'type': 'forced_exit',
            'message': 'One Of The Players Disconnected From Match'
        }
        self.send(message=message)
        print(f"[SERVER] SENT (forced_exit) MESSAGE --> {self.id}")

    def send_match_over(self, winner_number):
        self.connection_reset()
        message = {
            'type': 'match_over',
            'message': winner_number
        }
        self.send(message=message)
        print(f"[SERVER] SENT (match_over) MESSAGE --> {self.id}")

    def close(self):
        self._mark_offline()
        self.running = False
        try:
            self.conn.close()
        except:
            pass
