import socket, threading, orjson, time

class GameClient:
    def __init__(self, name, hashtag, ip='127.0.0.1', port=5555):
        self.addr = (ip, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.connect(self.addr)

        self.name = name
        self.hashtag = hashtag
        self.buffer = ""
        self.running = True
        self.state_callback = None  # set externally by game.py
        self.player_number = None  # set by server after ID assignment
        self.id = None  # assigned by server
        self.mode = None # Sent by client but accepted and confirmed by Server
        self.player_operator = None # Sent by client but accepted and confirmed by Server
        self.in_queue = False  # set by server when in queue

        self.error_message = None
        self.error_type = None

        self.invitation_sent_successfully = False
        self.invitation_received = False
        self.invitation_accepted = False
        self.invitation_ongoing = False

        self.player_invitation_info = {
            "id": None,
            "name": None,
            "hashtag": None
        }

        threading.Thread(target=self.listen, daemon=True).start()

    def account(self, login=True):
        self.socket.send(orjson.dumps({
            "type": "client_access-login" if login else "client_access-signup",
            "name": self.name,
            "hashtag": self.hashtag
        }) + b"\n")

    def close_client(self):
        self.running = False
        self.socket.close()

    def send_invitation(self, name, hashtag):
        if not self.running or self.id is None:
            return
        invitation = {
            "type": "invitation",
            "data": {
                "name": name,
                "hashtag": hashtag
            }
        }
        self.socket.send(orjson.dumps(invitation) + b"\n")
        # print(f"[CLIENT] Sent Invitation to Player {name}/{hashtag}")

    def send_invitation_cancel(self):
        if not self.running or self.id is None:
            return
        cancel = {
            "type": "invitation_cancel",
            "data": {}
        }
        self.socket.send(orjson.dumps(cancel) + b"\n")
        # print(f"[CLIENT] Sent Invitation Cancel")

    def send_invitation_acceptance(self):
        if not self.running or self.id is None:
            return
        acceptance = {
            "type": "invitation_acceptance",
            "data": {}
        }
        self.socket.send(orjson.dumps(acceptance) + b"\n")
        # print(f"[CLIENT] Sent Invitation Acceptance")

    def send_invitation_rejection(self):
        if not self.running or self.id is None:
            return
        rejection = {
            "type": "invitation_rejection",
            "data": {}
        }
        self.socket.send(orjson.dumps(rejection) + b"\n")
        # print(f"[CLIENT] Sent Invitation Rejection")

    def clear_invitation_info(self):
        self.invitation_sent_successfully = False
        self.invitation_received = False
        self.invitation_accepted = False
        self.invitation_ongoing = False
        self.player_invitation_info = {
            "id": None,
            "name": None,
            "hashtag": None
        }
        # print("[CLIENT] Cleared Invitation Info")

    def send_match_request(self, mode: str, player_operator):
        if not self.running or self.id is None:
            return
        request = {
            "type": "match_request",
            "data": {
                "id": self.id,
                "name": self.name,
                "hashtag": self.hashtag,
                "mode": mode,
                "player_operator": player_operator,
            }
        }
        self.socket.send(orjson.dumps(request) + b"\n")

        # print(f"[CLIENT] Sent Match Request")

    def send_match_request_cancel(self):
        if not self.running or self.id is None:
            return
        cancel = {
            "type": "match_request_cancel",
            "data": {}
        }
        self.socket.send(orjson.dumps(cancel) + b"\n")
        # print(f"[CLIENT] Sent Match Request Cancel")

    def send_operator_confirm(self):
        if not self.running or self.id is None:
            return
        message = {
            "type": "operator_confirm",
            "data": {
                "id": self.id,
                "player_number": self.player_number
            }
        }
        self.socket.send(orjson.dumps(message) + b"\n")

        # print("[CLIENT] Sent Operator Confirmation")

    def exit_match(self):
        self.mode = None
        self.state_callback = None
        self.in_queue = False
        self.buffer = ""
        self.player_number = None
        self.player_operator = None
        self.clear_invitation_info()

    def send_snapshot(self, snapshot: dict):
        """
        Send your full player state snapshot.
        Server must attach your ID if not added.
        template:
        {
            "type": "snapshot",
            "data": {   ----> snapshot in the function below
                "id": 1,
                "name": "Player1",
                "player_number": 1,
                "input": { ... },
                "mouse": { "x": 200, "y": 150 }
            }
        }
        """
        if not self.running or self.id is None:
            return

        snapshot["id"] = self.id # enforce id
        snapshot["name"] = self.name  # enforce name
        snapshot["hashtag"] = self.hashtag  # enforce hashtag
        snapshot["timestamp"] = time.perf_counter()
        try:
            msg = orjson.dumps({"type": "snapshot", "data": snapshot}) + b'\n'
            self.socket.send(msg)
        except:
            self.running = False

    def listen(self):
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                self.buffer += data.decode('utf-8')
                while '\n' in self.buffer:
                    msg, self.buffer = self.buffer.split('\n', 1)
                    self.handle_message(msg)
            except:
                break
        self.running = False

    def handle_message(self, raw_json):
        try:
            message = orjson.loads(raw_json.encode('utf-8'))
            msg_type = message.get("type")

            if msg_type == "assign_id":
                self.id = message["id"]
                # print(f"[CLIENT] Assigned ID: {self.id}")

            elif msg_type in ["operator_sync", "all_operators_confirmed", "state", "opp_ready", "forced_exit", "match_over"]:
                if self.state_callback:
                    self.state_callback(message)

            elif msg_type == "match_request_accepted":
                self.mode = message["mode"]
                self.player_operator = message["player_operator"]
                self.in_queue = True
                # print(f"[CLIENT] MATCH REQUEST ACCEPTED ---> MODE {self.mode} WITH OP {self.player_operator}")

            elif msg_type == "match_request_cancelled":
                self.exit_match()
                # print("[CLIENT] MATCH REQUEST CANCELLED")

            elif msg_type in ['registration_error', 'player_not_found', 'player_already_online', 'player_offline', 'player_cannot_invite_self', 'player_has_invitation']:
                self.error_type = msg_type
                self.error_message = message.get('message', 'Unknown error')
                # print(f"[CLIENT ERROR] {self.error_message}")

            elif msg_type == 'invitation_sent_successfully':
                self.invitation_sent_successfully = True
                self.invitation_ongoing = True
                invited_player = message["data"]
                self.player_invitation_info = {
                    "id": invited_player["id"],
                    "name": invited_player["name"],
                    "hashtag": invited_player["hashtag"]
                }
                # print("[CLIENT] Invitation Sent Confirmation")

            elif msg_type == 'player_has_invitation':
                self.invitation_sent_successfully = True
                self.invitation_accepted = False
                self.invitation_ongoing = True
                # print("[CLIENT] Player has Invitation")

            elif msg_type == 'invitation_from_player':
                self.invitation_received = True
                self.invitation_ongoing = True
                self.player_invitation_info["id"] = message["data"]["id"]
                self.player_invitation_info["name"] = message["data"]["name"]
                self.player_invitation_info["hashtag"] = message["data"]["hashtag"]
                # print("[CLIENT] Invitation Received")

            elif msg_type == 'invitation_acceptance':
                self.invitation_accepted = True
                # print("[CLIENT] Invitation Accepted")

            elif msg_type == 'invitation_rejected':
                self.clear_invitation_info()
                # print("[CLIENT] Invitation Rejected")

            elif msg_type == 'invitation_cancel_accepted':
                self.clear_invitation_info()
                # print("[CLIENT] Invitation Cancel Accepted")

        except Exception as e:
            print(f"[CLIENT ERROR] {e}")
            # print(f"[CLIENT DEBUG] Raw JSON: {raw_json}")
            pass
