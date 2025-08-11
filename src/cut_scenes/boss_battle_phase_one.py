import pygame, sys, pathlib, os
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.engine.cameras import *
from src.items.dialogue import *
from src.engine.cut_scene import *

def boss_intro_cutscene(game):
    cs = CutSceneManager(game)
    boss = game.level.BOSS
    player = game.level.players.get_player()
    cs.temp_data = {}

    # Prepration
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

    def wait(step):
        cs.temp_data.setdefault('wait', 0)
        cs.temp_data['wait'] += 1
        if cs.temp_data['wait'] >= 90:
            cs.temp_data['wait'] = 0
            step.next_step()

    # =========== Cutscene Start ===========

    # player turn right

    # show Boss

    def player_falls_in(step):
        if player.collisions.collision['down']:
            step.next_step()

    # wait

    def player_walks_in(step):
        player.controller.movement['RMove'] = 1
        if abs(player.rect().centerx - game.level.cameras[0].center_position.x) <= 150:
            player.controller.movement['RMove'] = 0
            step.next_step()

    # wait

    # boss camera focus

    # wait

    def boss_talks_with_the_worthy(step):
        dialogue = [
            {"entity": boss, "text": "So... you've come. That was always the trajectory, wasn't it?", "show_left": False},
            {"entity": boss, "text": "Your determination is admirable. But misplaced.", "show_left": False},
            {"entity": boss, "text": "This isn’t about triumph. It’s not about right or wrong.", "show_left": False},
            {"entity": boss, "text": "It’s about what holds. What keeps the world from collapsing under its own contradictions.", "show_left": False},
            {"entity": boss, "text": "I’ve seen civilizations rise on dreams and fall to the same.", "show_left": False},
            {"entity": boss, "text": "Peace is always declared. And always abandoned.", "show_left": False},
            {"entity": boss, "text": "You think I obstruct progress. But progress without structure is collapse wearing a crown.", "show_left": False},
            {"entity": boss, "text": "What I am is not a threat. It is a necessity.", "show_left": False},
            {"entity": boss, "text": "Chaos is not a force I unleash. It’s one I contain.", "show_left": False},
            {"entity": boss, "text": "Measured. Directed. Held back from consuming all of it.", "show_left": False},
            {"entity": boss, "text": "You don’t see it yet. That’s understandable. Most don’t.", "show_left": False},
            {"entity": boss, "text": "This is not destiny. Not punishment. It’s balance.", "show_left": False},
            {"entity": boss, "text": "And if I fall... that balance goes with me.", "show_left": False}
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    def change_camera_target(step):
        game.target_entity = game.level.cameras[0]
        step.next_step()

    # wait

    def boss_walks(step):
        boss.controller.movement['LMove'] = 1
        if abs(boss.rect().centerx - game.level.cameras[0].center_position.x) <= 150:
            boss.controller.movement['LMove'] = 0
            step.next_step()

    # wait

    def finish_cutscene(step):
        game.dialogue_manager.start(player, "The Chaos ends! right here! right now!", show_left=True)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # player camera focus

    # wait

    cs.add_step(player_turn_right)
    cs.add_step(show_boss)
    cs.add_step(player_falls_in)
    cs.add_step(wait)
    cs.add_step(player_walks_in)
    cs.add_step(wait)
    cs.add_step(boss_camera_focus)
    cs.add_step(wait)
    cs.add_step(boss_talks_with_the_worthy)
    cs.add_step(wait)
    cs.add_step(change_camera_target)
    cs.add_step(wait)
    cs.add_step(boss_walks)
    cs.add_step(wait)
    cs.add_step(finish_cutscene)
    cs.add_step(wait)
    cs.add_step(player_camera_focus)
    cs.add_step(wait)

    game.cutscene_manager = cs
    game.cutscene_mode = True


# SINGLE LINE BASED ----------------->
#game.dialogue_manager.start(player, "We’ve reached the edge...", bottom_mode=True, show_left=True)

# SCRIPT BASED ------------>
# game.dialogue_manager.start_script([
#     {"entity": boss, "text": "You're too late!", "show_left": False},
#     {"entity": player, "text": "We'll see about that.", "show_left": True},
#     {"entity": boss, "text": "Then come."}
# ])