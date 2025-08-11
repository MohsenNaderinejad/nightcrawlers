import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.engine.cameras import *
from src.items.dialogue import *
from src.engine.cut_scene import *

def boss_fourth_phase_endgame(game):
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

    def player_turn_left(step):
        player.animation_manager.flip = True
        step.next_step()

    def player_turn_right(step):
        player.animation_manager.flip = False
        step.next_step()

    def player_camera_focus(step):
        game.target_entity = player
        step.next_step()

    def boss_camera_focus(step):
        game.target_entity = boss
        step.next_step()
    
    def show_boss(step):
        boss.show_black_circle = True
        step.next_step()

    def hide_boss(step):
        boss.show_black_circle = False
        step.next_step()

    def wait(step):
        cs.temp_data.setdefault('wait', 0)
        cs.temp_data['wait'] += 1
        if cs.temp_data['wait'] >= 90:
            cs.temp_data['wait'] = 0
            step.next_step()
        
    # ======= CUTSCENE START ========
    
    # player turn right

    # boss turn left

    def player_falls_in(step):
        if player.collisions.collision['down']:
            step.next_step()

    # wait
    
    def player_confusion_one(step):
        game.dialogue_manager.start(player, "Where are you damn wicked!?", bottom_mode=True, show_left=True)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # player turn left

    # wait

    # player turn right

    # wait
    
    def player_confusion_two(step):
        game.dialogue_manager.start(player, "Where are you ???!!!", bottom_mode=True, show_left=True)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # player turn left
    
    # wait

    # show boss

    # wait

    # boss turn right

    # wait

    def player_realizing(step):
        game.dialogue_manager.start(player, "There you are !", bottom_mode=True, show_left=True)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    def player_walks(step):
        cs.temp_data.setdefault('player_walks', 0)
        cs.temp_data['player_walks'] += 1
        player.controller.movement['RMove'] = 1
        if cs.temp_data['player_walks'] > 30:
            player.controller.movement['RMove'] = 0
            step.next_step()

    # wait

    # boss camera focus

    # wait

    def boss_talks_part_one(step):
        dialogue = [
        {"entity": boss, "text": "You still don’t see it.", "show_left": False},
        {"entity": boss, "text": "After everything - after all you’ve heard - you still think this is a matter of will.", "show_left": False},
        {"entity": player, "text": "You can not predict ev...", "show_left": True},
        {"entity": boss, "text": "Silence!!!", "show_left": False},
        {"entity": boss, "text": "I Do the Talking from now on!", "show_left": False},
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # boss turn right

    # wait

    def boss_talks_part_two(step):
        dialogue = [
        {"entity": boss, "text": "You Think That if you just push hard enough, the world will change to match your vision.", "show_left": False},
        {"entity": boss, "text": "But things do change. Empires fall. Maps redraw. Names fade.", "show_left": False},
        {"entity": boss, "text": "And still, people remain the same.", "show_left": False},
        {"entity": boss, "text": "They shout about peace while sharpening blades.", "show_left": False},
        {"entity": boss, "text": "They curse chaos, then create it when peace grows quiet.", "show_left": False},
        {"entity": boss, "text": "I’ve tried to make you understand. I’ve shown you what this is.", "show_left": False},
        {"entity": boss, "text": "But you don’t want truth.", "show_left": False},
        {"entity": boss, "text": "You want to be right.", "show_left": False},
        {"entity": boss, "text": "And I’m done trying to convince you.", "show_left": False},
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # boss turn left

    # wait

    # hide boss

    # wait

    # player focus camera

    # wait

    def boss_remarks(step):
        game.dialogue_manager.start(boss, "Let’s finish this - before your ignorance does more damage than the chaos you fear.", bottom_mode=True, show_left=False)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    cs.add_step(player_turn_right)
    cs.add_step(boss_turn_left)
    cs.add_step(player_falls_in)
    cs.add_step(wait)
    cs.add_step(player_confusion_one)
    cs.add_step(wait)
    cs.add_step(player_turn_left)
    cs.add_step(wait)
    cs.add_step(player_turn_right)
    cs.add_step(wait)
    cs.add_step(player_confusion_two)
    cs.add_step(wait)
    cs.add_step(player_turn_left)
    cs.add_step(wait)
    cs.add_step(show_boss)
    cs.add_step(wait)
    cs.add_step(player_turn_right)
    cs.add_step(wait)
    cs.add_step(player_realizing)
    cs.add_step(wait)
    cs.add_step(player_walks)
    cs.add_step(wait)
    cs.add_step(boss_camera_focus)
    cs.add_step(wait)
    cs.add_step(boss_talks_part_one)
    cs.add_step(wait)
    cs.add_step(boss_turn_right)
    cs.add_step(wait)
    cs.add_step(boss_talks_part_two)
    cs.add_step(wait)
    cs.add_step(boss_turn_left)
    cs.add_step(wait)
    cs.add_step(hide_boss)
    cs.add_step(wait)
    cs.add_step(player_camera_focus)
    cs.add_step(wait)
    cs.add_step(boss_remarks)
    cs.add_step(wait)

    game.cutscene_manager = cs
    game.cutscene_mode = True