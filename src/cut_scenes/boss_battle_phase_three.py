import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.engine.cameras import *
from src.items.dialogue import *
from src.engine.cut_scene import *

def boss_third_phase_tired(game):
    cs = CutSceneManager(game)
    boss = game.level.BOSS
    player = game.level.players.get_player()
    cs.temp_data = {}

    # Prepration
    def boss_turn_right(step):
        boss.animation_manager.flip = False
        step.next_step()

    def boss_turn_left(step):
        boss.animation_manager.flip = True
        step.next_step()

    def player_turn_right(step):
        player.animation_manager.flip = False
        step.next_step()

    def boss_camera_focus(step):
        game.target_entity = boss
        step.next_step()

    def player_camera_focus(step):
        game.target_entity = player
        step.next_step()
    
    def show_boss(step):
        boss.show_black_circle = True
        step.next_step()

    def wait(step):
        cs.temp_data.setdefault('wait', 0)
        cs.temp_data['wait'] += 1
        if cs.temp_data['wait'] >= 90:
            cs.temp_data['wait'] = 0
            step.next_step()
        
    # ======= CUTSCENE START ========

    # show boss
    
    # player turn right
    
    # boss turn left

    def player_falls_in(step):
        if player.collisions.collision['down']:
            step.next_step()

    # wait

    def player_questions(step):
        game.dialogue_manager.start(player, "what are you trying to achieve ??? all of this to only convince me that you are \"GOOD God\"!!??", bottom_mode=True, show_left=True)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # boss camera focus

    # wait

    def boss_talks(step):
        dialogue = [
            {"entity": boss, "text": "So this is your answer.", "show_left": False},
            {"entity": boss, "text": "Rage, again. Violence, again.", "show_left": False},
            {"entity": boss, "text": "You come here speaking of peace—", "show_left": False},
            {"entity": boss, "text": "Yet all you've done is mirror the very chaos you claim to destroy.", "show_left": False},
            {"entity": boss, "text": "Strike after strike. Word after word. And still, you believe you're different.", "show_left": False},
            {"entity": boss, "text": "Do you truly think chaos ends when it’s met with more chaos?", "show_left": False},
            {"entity": boss, "text": "That fear submits when shouted down?", "show_left": False},
            {"entity": boss, "text": "No. That’s not peace. That’s control. That’s pride.", "show_left": False},
            {"entity": boss, "text": "And I've seen it, again and again—", "show_left": False},
            {"entity": boss, "text": "The fire that swears it will burn cleaner than the last.", "show_left": False},
            {"entity": boss, "text": "But fire... is still fire.", "show_left": False}
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # boss turn right

    # wait

    def change_camera_target(step):
            game.target_entity = game.level.cameras[0]
            step.next_step()

    # wait

    def final_talk(step):
        dialogue = [
            {"entity": boss, "text": "You're beginning to see it, aren't you? The world doesn't move without friction.", "show_left": False},
            {"entity": player, "text": "Maybe. But friction isn't the only way forward.", "show_left": True},
            {"entity": boss, "text": "It’s the only way that’s ever lasted.", "show_left": False},
            {"entity": player, "text": "Then maybe it's time something finally changed.", "show_left": True}
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # player camera focus

    cs.add_step(show_boss)
    cs.add_step(player_turn_right)
    cs.add_step(boss_turn_left)
    cs.add_step(player_falls_in)
    cs.add_step(wait)
    cs.add_step(player_questions)
    cs.add_step(wait)
    cs.add_step(boss_camera_focus)
    cs.add_step(wait)
    cs.add_step(boss_talks)
    cs.add_step(wait)
    cs.add_step(boss_turn_right)
    cs.add_step(wait)
    cs.add_step(change_camera_target)
    cs.add_step(wait)
    cs.add_step(final_talk)
    cs.add_step(wait)
    cs.add_step(player_camera_focus)
    cs.add_step(wait)

    game.cutscene_manager = cs
    game.cutscene_mode = True