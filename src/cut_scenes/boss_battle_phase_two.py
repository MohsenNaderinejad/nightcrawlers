import sys, pathlib
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.utils import *
from src.engine.cameras import *
from src.items.dialogue import *
from src.engine.cut_scene import *

def boss_second_phase_explanation(game):
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
        
    # ======= CUTSCENE START ========
    
    # player turn left
    
    # boss turn left

    def player_falls_in(step):
        if player.collisions.collision['down']:
            step.next_step()

    # wait

    def player_confusion(step):
        game.dialogue_manager.start(player, "What The ...??? How did I get here ???!!!", bottom_mode=True, show_left=True)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # boss camera focus

    # wait

    # show boss

    # wait

    def boss_walks_away(step):
        boss.controller.movement['LMove'] = 1
        if abs(player.rect().centerx - boss.rect().centerx) > 250:
            boss.controller.movement['LMove'] = 0
            cs.temp_data.setdefault('stop_motion', False)
            step.next_step()

    # wait

    def boss_remarks(step):
        game.dialogue_manager.start(boss, "Beautiful! Is it not ?", bottom_mode=True, show_left=False)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    def boss_talks_part_one(step):
        dialogue = [
            {"entity": boss, "text": "Look around you. What do you perceive? A problem to solve? A villain to slay?", "show_left": False},
            {"entity": boss, "text": "You believe this ends with me? It doesn’t. Eliminate this form, and the function persists.", "show_left": False},
            {"entity": boss, "text": "Another will emerge - perhaps not immediately, perhaps not willingly, but inevitably. Chaos does not vanish. It reconstitutes.", "show_left": False},
            {"entity": boss, "text": "This pattern is not imposed upon your kind. It is authored by them.", "show_left": False},
            {"entity": player, "text": "No... you're just twisting things.", "show_left": True},
            {"entity": player, "text": "People want peace. They just... they just don’t always know how to get it.", "show_left": True},
            {"entity": player, "text": "That doesn’t make this right.", "show_left": True},
            {"entity": boss, "text": "Warfare, grievance, dissent, spectacle - these are not anomalies. They are rituals.", "show_left": False},
            {"entity": boss, "text": "Stillness offends the instinct. Predictability suffocates the spirit.", "show_left": False},
            {"entity": boss, "text": "They seek friction, not comfort. Conflict makes them feel awake.", "show_left": False},
            {"entity": boss, "text": "I do not incite this nature. I regulate it. Measure it. Temper it before it consumes them.", "show_left": False},
        ]
        if not cs.temp_data.get('stop_motion', False):
            boss.controller.movement['LMove'] = 1
        if abs(player.rect().centerx - boss.rect().centerx) > 400:
            boss.controller.movement['LMove'] = 0
            cs.temp_data['stop_motion'] = True
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # boss turn right

    # wait

    def boss_talks_part_two(step):
        dialogue = [
            {"entity": boss, "text": "Without that - without me - there is only unmanaged entropy.", "show_left": False},
            {"entity": boss, "text": "I do not relish this role. But it is mine.", "show_left": False},
            {"entity": boss, "text": "You call it tyranny. I call it containment.", "show_left": False},
            {"entity": boss, "text": "And when the burden is yours... when the weight is no longer theoretical... you will understand.", "show_left": False},
            {"entity": boss, "text": "Not all chaos is destruction. Sometimes... it is the only structure that remains.", "show_left": False}
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait

    # boss turn left

    # wait

    # player camera focus

    # wait

    def player_walks(step):
        player.controller.movement['LMove'] = 1
        if abs(boss.rect().centerx - player.rect().centerx) <= 275:
            player.controller.movement['LMove'] = 0
            step.next_step()

    # wait

    def final_talk(step):
        dialogue = [
            {"entity": player, "text": "Bring it On!!!", "show_left": True},
            {"entity": boss, "text": "As You Wish", "show_left": False}
        ]
        game.dialogue_manager.start_script(dialogue)
        step.dialogue_shown = True
        step.waiting_for_input = True

    # wait
    
    cs.add_step(player_turn_left)
    cs.add_step(boss_turn_left)
    cs.add_step(player_falls_in)
    cs.add_step(wait)
    cs.add_step(player_confusion)
    cs.add_step(wait)
    cs.add_step(boss_camera_focus)
    cs.add_step(wait)
    cs.add_step(show_boss)
    cs.add_step(wait)
    cs.add_step(boss_walks_away)
    cs.add_step(wait)
    cs.add_step(boss_remarks)
    cs.add_step(wait)
    cs.add_step(boss_talks_part_one)
    cs.add_step(wait)
    cs.add_step(boss_turn_right)
    cs.add_step(wait)
    cs.add_step(boss_talks_part_two)
    cs.add_step(wait)
    cs.add_step(boss_turn_left)
    cs.add_step(wait)
    cs.add_step(player_camera_focus)
    cs.add_step(wait)
    cs.add_step(player_walks)
    cs.add_step(wait)
    cs.add_step(final_talk)
    cs.add_step(wait)

    game.cutscene_manager = cs
    game.cutscene_mode = True