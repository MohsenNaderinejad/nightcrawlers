import pygame, string

# Configuration file for the game

DEBUG = False # Set to False for production
FPS = 60
SCREEN_SIZE = (1600, 900)
DISPLAY_SIZE = (880, 495)
PLAYER_WEAPONS = ['colt', 'shotgun', 'dua_colt', 'revolver', 'm95']

PLAYER_WEAPONS_CONFIG = {
    'colt': {
        'magazine_capacity': 8,
        'total_ammo': 72,
        'fire_rate': 20,
        'bullet_speed': 9,          
        'bullet_damage': 10,         
        'ammo_reduction': 1,
        'total_reload_time': 50,
    },
    'shotgun': {
        'magazine_capacity': 12,
        'total_ammo': 72,
        'fire_rate': 70,
        'bullet_speed': 6,
        'bullet_damage': 10,
        'ammo_reduction': 3,
        'total_reload_time': 120,
    },
    'revolver': {
        'magazine_capacity': 6,
        'total_ammo': 54,
        'fire_rate': 40,
        'bullet_speed': 8,
        'bullet_damage': 16,         
        'ammo_reduction': 1,
        'total_reload_time': 90,
    },
    'm95': {
        'magazine_capacity': 40,
        'total_ammo': 360,
        'fire_rate': 12,        
        'bullet_speed': 7,
        'bullet_damage': 6,
        'ammo_reduction': 1,
        'total_reload_time': 80,
    }
}

ENEMY_GUNS = {
    'freezer': {
        'bullet_damage': 4,
        'bullet_speed': 1.8,
        'fire_rate': 270
    },
    'simple_gun': {
        'bullet_damage': 6,
        'bullet_speed': 3.8,
        'fire_rate': 160
    },
    'blinder_gun': {
        'bullet_damage': 1,
        'bullet_speed': 2.2,
        'fire_rate': 280
    }
}

ENEMY_ATTRS = {
    'bomber': {
        'attack_damage': 14,
        'HP': 30,
        'aggro_range': 600,
        'attack_range': 2,
        'sight_range': 650,
        'field_of_view': 90,
        'walk_speed': 1,
        'run_speed': 1.4,
    },
    'freezer': {
        'attack_damage': 6,
        'HP': 50,
        'aggro_range_x': 500,
        'aggro_range_y': DISPLAY_SIZE[1] - 90,
        'attack_range': 400,
        'sight_range_x': 600,
        'sight_range_y': DISPLAY_SIZE[1] - 40,
        'field_of_view': 360,
        'walk_speed': 1,
        'run_speed': 1.1,
    },
    'tank': {
        'HP': 140,
        'aggro_range': 1000,
        'attack_range': 800,
        'sight_range': 1200,
        'field_of_view': 75,
        'walk_speed': 0.2,
        'run_speed': 0.7,
    },
    'samurai': {
        'attack_damage': {
            'attack_1': 14,
            'attack_3': 18
        },
        'HP': 115,
        'aggro_range': DISPLAY_SIZE[0] - 20,
        'attack_range': 10,
        'sight_range': DISPLAY_SIZE[0] - 30,
        'field_of_view': 90,
        'walk_speed': 0.6,
        'run_speed': 1.2,
    }
}

BOSS_ATTRS = {
    'HP': 40 if DEBUG else 1600,
    'REMAINED_HP': 10 if DEBUG else 400,
    'attack_damage': 20,
    'aggro_range': DISPLAY_SIZE[0],
    'attack_range': 30,
    'sight_range': DISPLAY_SIZE[0],
    'field_of_view': 360,
    'walk_speed': 1,
    'run_speed': 1,
    'boss_teleportation_cooldown_max': 300,
    'teleport_distance_threshold': 180,
}

PLAYER_ONE_KEY_BIND = {
    'jump_key': pygame.K_w,
    'left_key': pygame.K_a,
    'right_key': pygame.K_d,
    'shoot_key': pygame.K_q,
    'fshift_key': pygame.K_LSHIFT,
    'sshift_key': pygame.K_LSHIFT,
    'reload_key': pygame.K_r,
    'change_gun_key': pygame.K_v
}
PLAYER_TWO_KEY_BIND = {
    'jump_key': pygame.K_UP,
    'left_key': pygame.K_LEFT,
    'right_key': pygame.K_RIGHT,
    'shoot_key': pygame.K_RCTRL,
    'fshift_key': pygame.K_RSHIFT,
    'sshift_key': pygame.K_RSHIFT,
    'reload_key': pygame.K_SLASH,
    'change_gun_key': pygame.K_QUOTE
}

PROMPTS = {
    'boss': {
        '1': "Write a short monologue (8–14 words) to be spoken mid-battle by a calm, well-mannered god who governs chaos and fear.\n"
                  "He speaks without hostility. His role is to maintain balance in a chaotic world.\n"
                  "Tone: composed, logical, respectful. Avoid threats, drama, or metaphors.\n"
                  "He explains the necessity of his existence, not with pride, but with reason.",

        '2': "Write a short monologue (8–14 words) from a disappointed god of chaos and fear.\n"
                  "He notices the player repeating humanity’s mistakes. Tone is still logical but lightly frustrated.\n"
                  "He points out contradiction calmly, without taunting or anger.\n"
                  "Avoid emotion-heavy words—he still wants the player to understand.",

        '3': "Write a short monologue (8–14 words) from a god clearly frustrated by the player’s hypocrisy.\n"
                  "The player fights chaos with chaos. Tone is cold, disappointed, restrained—but firmer than before.\n"
                  "He no longer believes reason will work. Avoid threats or shouting, but show control slipping slightly.",

        '4': "Write a short monologue (8–14 words) from a god who has given up on reasoning.\n"
                  "Tone is final, cold, and corrective. He no longer explains—he acts.\n"
                  "No more persuasion. No metaphors. Just calm resolve to remove a dangerous imbalance."
    },

    'player': {
        '1': "Write a short monologue (8–14 words) to be spoken mid-battle by a young, emotional fighter.\n"
                  "They believe defeating the god will bring peace and happiness.\n"
                  "Tone is bold, naive, impatient. No philosophical reasoning—just raw belief and defiance.",

        '2': "Write a short monologue (8–14 words) from a player who feels slight doubt but pushes forward.\n"
                  "Tone is confused, emotional, but still defiant. They don’t understand the god’s logic,\n"
                  "but want to end him anyway. Keep the line youthful and stubborn.",

        '3': "Write a short monologue (8–14 words) from a frustrated and emotional player mid-battle.\n"
                  "They’re losing patience, angry, and blinded by urgency. Tone is aggressive but still immature.\n"
                  "They believe the god is wrong, even if they can't explain why.",

        '4': "Write a short monologue (8–14 words) from a player who is exhausted but still convinced they’re right.\n"
                  "Tone is broken, angry, emotional. They don’t understand—but they must win.\n"
                  "No philosophy, just raw desperation and misguided certainty."
    }
}

ALLOWED_WORDS = list(string.ascii_letters) + list(string.digits)