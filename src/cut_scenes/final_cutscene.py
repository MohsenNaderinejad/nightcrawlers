import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.engine.cameras import *
from src.items.dialogue import *
from src.engine.cut_scene import *

def THE_END(game):
    cs = CutSceneManager(game)
    boss = game.level.BOSS
    player = game.level.players.get_player()
    cs.temp_data = {}

    # Prepration
    def player_camera_focus(step):
        game.target_entity = player
        step.next_step()

    def boss_camera_focus(step):
        game.target_entity = boss
        step.next_step()

    def wait(step):
        cs.temp_data.setdefault('wait', 0)
        cs.temp_data['wait'] += 1
        if cs.temp_data['wait'] >= 90:
            cs.temp_data['wait'] = 0
            step.next_step()
        
    # ======= CUTSCENE START ========
    
    # wait

    def player_talks(step):
        dialogue = [
            {"entity": player, "text": "It's over.", "show_left": True},
            {"entity": player, "text": "You're finished.", "show_left": True},
            {"entity": player, "text": "This ends now.", "show_left": True},
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait
    
    def boss_alive(step):
        dialogue = [
            {"entity": boss, "text": "You speak like a victor.", "show_left": False},
            {"entity": player, "text": "What the ..... ??!?", "show_left": True},
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # boss camera focus

    # wait

    def boss_talks(step):
        dialogue = [
            {"entity": boss, "text": "But all you've done is sever a limb from something far older than you.", "show_left": False},
            {"entity": boss, "text": "You never understood what this was.", "show_left": False},
            {"entity": boss, "text": "This form, this voice — they were a conduit. Not the source.", "show_left": False},
            {"entity": boss, "text": "Chaos is not an enemy. It’s a current.", "show_left": False},
            {"entity": boss, "text": "I was the dam. You shattered it.", "show_left": False},
            {"entity": boss, "text": "You wanted change. But change without comprehension... is collapse.", "show_left": False},
            {"entity": boss, "text": "You wanted to end the cycle.", "show_left": False},
            {"entity": boss, "text": "Instead, you’ve made yourself part of it.", "show_left": False},
            {"entity": boss, "text": "You now carry the imbalance you thought you were fighting.", "show_left": False},
            {"entity": boss, "text": "I am not here to punish you.", "show_left": False},
            {"entity": boss, "text": "I am here to correct the error.", "show_left": False},
            {"entity": boss, "text": "You were warned.", "show_left": False},
            {"entity": boss, "text": "And now —", "show_left": False},
            {"entity": boss, "text": "You will be removed.", "show_left": False}
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # player camera focus

    # wait

    def boss_kills_player(step):
        player.death_action()
        step.next_step()
    
    # wait

    def game_pending_action(step):
        game.level.pending_action = 'finish'
        step.next_step()

    # wait

    cs.add_step(wait)
    cs.add_step(player_talks)
    cs.add_step(wait)
    cs.add_step(boss_alive)
    cs.add_step(wait)
    cs.add_step(boss_camera_focus)
    cs.add_step(wait)
    cs.add_step(boss_talks)
    cs.add_step(wait)
    cs.add_step(player_camera_focus)
    cs.add_step(wait)
    cs.add_step(boss_kills_player)
    cs.add_step(wait)
    cs.add_step(game_pending_action)

    game.cutscene_manager = cs
    game.cutscene_mode = True