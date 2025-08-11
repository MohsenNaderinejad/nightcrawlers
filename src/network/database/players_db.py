import json, os
import threading

DB_PATH = "players.json"
db_lock = threading.RLock()

def load_database():
    with db_lock:
        if not os.path.exists(DB_PATH):
            with open(DB_PATH, "w") as f:
                json.dump([], f)
        with open(DB_PATH, "r") as f:
            return json.load(f)

def save_database(db):
    with db_lock:
        with open(DB_PATH, "w") as f:
            json.dump(db, f, indent=2)

def generate_new_id(db):
    if not db:
        return 1
    return max(player["id"] for player in db) + 1

def is_name_hashtag_unique(db, name, hashtag):
    return all(p["name"] != name or p["hashtag"] != hashtag for p in db)

def register_player(name, hashtag):
    with db_lock:
        db = load_database()
        
        if not is_name_hashtag_unique(db, name, hashtag):
            raise ValueError("Name#Hashtag already taken.")
        
        new_id = generate_new_id(db)
        new_player = {
            "id": new_id,
            "name": name,
            "hashtag": hashtag,
            "is_online": False,
        }
        
        db.append(new_player)
        save_database(db)
        return new_player

def get_player_by_id(pid):
    with db_lock:
        db = load_database()
        return next((p for p in db if p["id"] == pid), None)

def get_player_by_name_tag(name, hashtag):
    with db_lock:
        db = load_database()
        player = next((p for p in db if p["name"] == name and p["hashtag"] == hashtag), None)
        return player

def set_player_offline(player_id):
    with db_lock:
        db = load_database()
        player = next((p for p in db if p["id"] == player_id), None)

    if player:
        player["is_online"] = False
        save_database(db)
        print(f"[DB] Player {player['name']}#{player['hashtag']} is now OFFLINE")
        return True
    return False

def set_all_players_offline():
    with db_lock:
        db = load_database()
        for player in db:
            player["is_online"] = False
        save_database(db)
    print("[DB] All players are now OFFLINE")
    return True

def set_player_online(player_id):
    with db_lock:
        db = load_database()
    player = next((p for p in db if p["id"] == player_id), None)
    
    if player:
        player["is_online"] = True
        save_database(db)
        print(f"[DB] Player {player['name']}#{player['hashtag']} is now ONLINE")
        return True
    return False

def get_online_players():
    with db_lock:
        db = load_database()
        return [p for p in db if p.get("is_online", False)]

def get_offline_players():
    with db_lock:
        db = load_database()
        return [p for p in db if not p.get("is_online", False)]
