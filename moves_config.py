# ─────────────────────────────────────────────
# moves_config.py
# Move set complet pentru sistemul de lupta Arena.
#
# STRUCTURA MOVE:
# {
#   'key':        str,      # ID unic
#   'name':       str,      # Nume afisat
#   'icon':       str,      # Emoji
#   'nature':     str,      # Natura move-ului (pentru interactiuni)
#   'type':       str,      # 'attack' | 'status' | 'heal'
#   'power':      float,    # Multiplicator damage (bazat pe attack al atacatorului)
#   'accuracy':   float,    # Sansa de hit (0.0-1.0)
#   'unlock_level': int,    # Nivelul minim pentru deblocare
#   'species':    list|None,# None = orice specie, sau lista de specii specifice
#   'natures':    list|None,# None = orice natura, sau lista de naturi specifice
#   'effect': {             # Optional
#       'type':    str,     # 'stun' | 'burn' | 'poison' | 'freeze' | 'heal' | 'shield' | 'speed_down' | 'attack_down'
#       'chance':  float,   # Sansa de aplicare (0.0-1.0)
#       'value':   int,     # Valoare efect (damage per tur, % heal, etc)
#       'turns':   int,     # Durata in tururi
#   }
# }
# ─────────────────────────────────────────────

MOVES = {

    # ════════════════════════════════════════
    # BASIC ATTACKS — disponibile tuturor
    # ════════════════════════════════════════
    'scratch': {
        'key': 'scratch',
        'name': 'Zgârietură',
        'icon': '🐾',
        'nature': None,
        'type': 'attack',
        'power': 0.8,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': None,
        'effect': None,
    },
    'headbutt': {
        'key': 'headbutt',
        'name': 'Cap în cap',
        'icon': '💥',
        'nature': None,
        'type': 'attack',
        'power': 1.0,
        'accuracy': 0.9,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': None,
        'effect': {
            'type': 'stun',
            'chance': 0.15,
            'value': 0,
            'turns': 1,
        },
    },

    # ════════════════════════════════════════
    # FIRE MOVES
    # ════════════════════════════════════════
    'ember': {
        'key': 'ember',
        'name': 'Jeratic',
        'icon': '🔥',
        'nature': 'fire',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['fire'],
        'effect': {
            'type': 'burn',
            'chance': 0.2,
            'value': 5,
            'turns': 3,
        },
    },
    'flame_burst': {
        'key': 'flame_burst',
        'name': 'Explozie de Flăcări',
        'icon': '🌋',
        'nature': 'fire',
        'type': 'attack',
        'power': 1.6,
        'accuracy': 0.85,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['fire'],
        'effect': {
            'type': 'burn',
            'chance': 0.35,
            'value': 8,
            'turns': 3,
        },
    },
    'heat_wave': {
        'key': 'heat_wave',
        'name': 'Val de Căldură',
        'icon': '♨️',
        'nature': 'fire',
        'type': 'status',
        'power': 0.5,
        'accuracy': 0.9,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['fire'],
        'effect': {
            'type': 'attack_down',
            'chance': 1.0,
            'value': 15,
            'turns': 3,
        },
    },
    'inferno': {
        'key': 'inferno',
        'name': 'Infern',
        'icon': '🌠',
        'nature': 'fire',
        'type': 'attack',
        'power': 2.2,
        'accuracy': 0.75,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['fire'],
        'effect': {
            'type': 'burn',
            'chance': 0.6,
            'value': 12,
            'turns': 4,
        },
    },

    # ════════════════════════════════════════
    # WATER MOVES
    # ════════════════════════════════════════
    'water_gun': {
        'key': 'water_gun',
        'name': 'Jet de Apă',
        'icon': '💧',
        'nature': 'water',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['water'],
        'effect': None,
    },
    'aqua_rush': {
        'key': 'aqua_rush',
        'name': 'Asalt Acvatic',
        'icon': '🌊',
        'nature': 'water',
        'type': 'attack',
        'power': 1.5,
        'accuracy': 0.9,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['water'],
        'effect': {
            'type': 'speed_down',
            'chance': 0.3,
            'value': 20,
            'turns': 2,
        },
    },
    'mist_veil': {
        'key': 'mist_veil',
        'name': 'Văl de Ceață',
        'icon': '🌫️',
        'nature': 'water',
        'type': 'status',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['water'],
        'effect': {
            'type': 'shield',
            'chance': 1.0,
            'value': 25,
            'turns': 3,
        },
    },
    'tidal_wave': {
        'key': 'tidal_wave',
        'name': 'Val Uriaș',
        'icon': '🌀',
        'nature': 'water',
        'type': 'attack',
        'power': 2.0,
        'accuracy': 0.8,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['water'],
        'effect': {
            'type': 'speed_down',
            'chance': 0.5,
            'value': 30,
            'turns': 3,
        },
    },

    # ════════════════════════════════════════
    # NATURE MOVES
    # ════════════════════════════════════════
    'vine_whip': {
        'key': 'vine_whip',
        'name': 'Bici de Viță',
        'icon': '🌿',
        'nature': 'nature',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['nature'],
        'effect': None,
    },
    'spore_cloud': {
        'key': 'spore_cloud',
        'name': 'Nor de Spori',
        'icon': '🍄',
        'nature': 'nature',
        'type': 'status',
        'power': 0,
        'accuracy': 0.9,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['nature'],
        'effect': {
            'type': 'poison',
            'chance': 1.0,
            'value': 6,
            'turns': 4,
        },
    },
    'regrowth': {
        'key': 'regrowth',
        'name': 'Regenerare',
        'icon': '🌱',
        'nature': 'nature',
        'type': 'heal',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['nature'],
        'effect': {
            'type': 'heal',
            'chance': 1.0,
            'value': 30,
            'turns': 1,
        },
    },
    'overgrowth': {
        'key': 'overgrowth',
        'name': 'Creștere Explozivă',
        'icon': '🌳',
        'nature': 'nature',
        'type': 'attack',
        'power': 2.0,
        'accuracy': 0.85,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['nature'],
        'effect': {
            'type': 'poison',
            'chance': 0.4,
            'value': 8,
            'turns': 3,
        },
    },

    # ════════════════════════════════════════
    # EARTH MOVES
    # ════════════════════════════════════════
    'rock_throw': {
        'key': 'rock_throw',
        'name': 'Aruncat cu Piatră',
        'icon': '🪨',
        'nature': 'earth',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 0.95,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['earth'],
        'effect': None,
    },
    'tremor': {
        'key': 'tremor',
        'name': 'Cutremur',
        'icon': '🌍',
        'nature': 'earth',
        'type': 'attack',
        'power': 1.4,
        'accuracy': 0.85,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['earth'],
        'effect': {
            'type': 'stun',
            'chance': 0.25,
            'value': 0,
            'turns': 1,
        },
    },
    'stone_wall': {
        'key': 'stone_wall',
        'name': 'Zid de Piatră',
        'icon': '🏔️',
        'nature': 'earth',
        'type': 'status',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['earth'],
        'effect': {
            'type': 'shield',
            'chance': 1.0,
            'value': 40,
            'turns': 4,
        },
    },
    'earthquake': {
        'key': 'earthquake',
        'name': 'Seism',
        'icon': '⛰️',
        'nature': 'earth',
        'type': 'attack',
        'power': 2.2,
        'accuracy': 0.8,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['earth'],
        'effect': {
            'type': 'stun',
            'chance': 0.4,
            'value': 0,
            'turns': 2,
        },
    },

    # ════════════════════════════════════════
    # STORM MOVES
    # ════════════════════════════════════════
    'spark': {
        'key': 'spark',
        'name': 'Scânteie',
        'icon': '⚡',
        'nature': 'storm',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['storm'],
        'effect': {
            'type': 'stun',
            'chance': 0.1,
            'value': 0,
            'turns': 1,
        },
    },
    'thunder_strike': {
        'key': 'thunder_strike',
        'name': 'Lovitură de Tunet',
        'icon': '🌩️',
        'nature': 'storm',
        'type': 'attack',
        'power': 1.6,
        'accuracy': 0.85,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['storm'],
        'effect': {
            'type': 'stun',
            'chance': 0.3,
            'value': 0,
            'turns': 1,
        },
    },
    'speed_boost': {
        'key': 'speed_boost',
        'name': 'Accelerare',
        'icon': '💨',
        'nature': 'storm',
        'type': 'status',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['storm'],
        'effect': {
            'type': 'speed_up',
            'chance': 1.0,
            'value': 30,
            'turns': 3,
        },
    },
    'thunderstorm': {
        'key': 'thunderstorm',
        'name': 'Furtună Electrică',
        'icon': '🌪️',
        'nature': 'storm',
        'type': 'attack',
        'power': 2.2,
        'accuracy': 0.75,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['storm'],
        'effect': {
            'type': 'stun',
            'chance': 0.5,
            'value': 0,
            'turns': 2,
        },
    },

    # ════════════════════════════════════════
    # ICE MOVES
    # ════════════════════════════════════════
    'ice_shard': {
        'key': 'ice_shard',
        'name': 'Șchiță de Gheață',
        'icon': '❄️',
        'nature': 'ice',
        'type': 'attack',
        'power': 0.9,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['ice'],
        'effect': {
            'type': 'speed_down',
            'chance': 0.2,
            'value': 15,
            'turns': 2,
        },
    },
    'frost_bite': {
        'key': 'frost_bite',
        'name': 'Degerătură',
        'icon': '🥶',
        'nature': 'ice',
        'type': 'attack',
        'power': 1.4,
        'accuracy': 0.9,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['ice'],
        'effect': {
            'type': 'freeze',
            'chance': 0.25,
            'value': 0,
            'turns': 2,
        },
    },
    'blizzard': {
        'key': 'blizzard',
        'name': 'Viscol',
        'icon': '🌨️',
        'nature': 'ice',
        'type': 'attack',
        'power': 1.8,
        'accuracy': 0.8,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['ice'],
        'effect': {
            'type': 'freeze',
            'chance': 0.4,
            'value': 0,
            'turns': 2,
        },
    },
    'absolute_zero': {
        'key': 'absolute_zero',
        'name': 'Zero Absolut',
        'icon': '🧊',
        'nature': 'ice',
        'type': 'attack',
        'power': 2.5,
        'accuracy': 0.65,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['ice'],
        'effect': {
            'type': 'freeze',
            'chance': 0.7,
            'value': 0,
            'turns': 3,
        },
    },

    # ════════════════════════════════════════
    # SHADOW MOVES
    # ════════════════════════════════════════
    'shadow_strike': {
        'key': 'shadow_strike',
        'name': 'Lovitură din Umbră',
        'icon': '🌑',
        'nature': 'shadow',
        'type': 'attack',
        'power': 1.1,
        'accuracy': 0.95,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['shadow'],
        'effect': None,
    },
    'vanish': {
        'key': 'vanish',
        'name': 'Dispariție',
        'icon': '👻',
        'nature': 'shadow',
        'type': 'status',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['shadow'],
        'effect': {
            'type': 'evasion_up',
            'chance': 1.0,
            'value': 40,
            'turns': 3,
        },
    },
    'soul_drain': {
        'key': 'soul_drain',
        'name': 'Drenare de Suflet',
        'icon': '💜',
        'nature': 'shadow',
        'type': 'attack',
        'power': 1.2,
        'accuracy': 0.9,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['shadow'],
        'effect': {
            'type': 'lifesteal',
            'chance': 1.0,
            'value': 40,
            'turns': 1,
        },
    },
    'nightmare': {
        'key': 'nightmare',
        'name': 'Coșmar',
        'icon': '🕷️',
        'nature': 'shadow',
        'type': 'attack',
        'power': 2.0,
        'accuracy': 0.8,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['shadow'],
        'effect': {
            'type': 'attack_down',
            'chance': 0.5,
            'value': 25,
            'turns': 3,
        },
    },

    # ════════════════════════════════════════
    # CRYSTAL MOVES
    # ════════════════════════════════════════
    'crystal_shard': {
        'key': 'crystal_shard',
        'name': 'Schijă de Cristal',
        'icon': '💎',
        'nature': 'crystal',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 0.95,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['crystal'],
        'effect': None,
    },
    'refraction': {
        'key': 'refraction',
        'name': 'Refracție',
        'icon': '🔮',
        'nature': 'crystal',
        'type': 'status',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['crystal'],
        'effect': {
            'type': 'reflect',
            'chance': 1.0,
            'value': 30,
            'turns': 3,
        },
    },
    'prism_beam': {
        'key': 'prism_beam',
        'name': 'Rază Prismatică',
        'icon': '🌈',
        'nature': 'crystal',
        'type': 'attack',
        'power': 1.7,
        'accuracy': 0.85,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['crystal'],
        'effect': None,
    },
    'diamond_storm': {
        'key': 'diamond_storm',
        'name': 'Furtună de Diamante',
        'icon': '✨',
        'nature': 'crystal',
        'type': 'attack',
        'power': 2.2,
        'accuracy': 0.78,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['crystal'],
        'effect': {
            'type': 'reflect',
            'chance': 0.5,
            'value': 20,
            'turns': 2,
        },
    },

    # ════════════════════════════════════════
    # STEEL MOVES
    # ════════════════════════════════════════
    'iron_claw': {
        'key': 'iron_claw',
        'name': 'Gheară de Fier',
        'icon': '⚙️',
        'nature': 'steel',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['steel'],
        'effect': None,
    },
    'metal_shield': {
        'key': 'metal_shield',
        'name': 'Scut de Metal',
        'icon': '🛡️',
        'nature': 'steel',
        'type': 'status',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['steel'],
        'effect': {
            'type': 'shield',
            'chance': 1.0,
            'value': 50,
            'turns': 4,
        },
    },
    'steel_edge': {
        'key': 'steel_edge',
        'name': 'Tăiș de Oțel',
        'icon': '⚔️',
        'nature': 'steel',
        'type': 'attack',
        'power': 1.6,
        'accuracy': 0.9,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['steel'],
        'effect': {
            'type': 'attack_down',
            'chance': 0.3,
            'value': 20,
            'turns': 2,
        },
    },
    'iron_fortress': {
        'key': 'iron_fortress',
        'name': 'Fortăreață de Fier',
        'icon': '🏰',
        'nature': 'steel',
        'type': 'attack',
        'power': 2.0,
        'accuracy': 0.85,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['steel'],
        'effect': {
            'type': 'shield',
            'chance': 0.4,
            'value': 30,
            'turns': 2,
        },
    },

    # ════════════════════════════════════════
    # LIGHT MOVES
    # ════════════════════════════════════════
    'light_beam': {
        'key': 'light_beam',
        'name': 'Rază de Lumină',
        'icon': '✨',
        'nature': 'light',
        'type': 'attack',
        'power': 1.0,
        'accuracy': 1.0,
        'unlock_level': 1,
        'species': None,
        'max_mp':  15,
        'natures': ['light'],
        'effect': None,
    },
    'holy_light': {
        'key': 'holy_light',
        'name': 'Lumină Sfântă',
        'icon': '🌟',
        'nature': 'light',
        'type': 'heal',
        'power': 0,
        'accuracy': 1.0,
        'unlock_level': 5,
        'species': None,
        'max_mp':  15,
        'natures': ['light'],
        'effect': {
            'type': 'heal',
            'chance': 1.0,
            'value': 35,
            'turns': 1,
        },
    },
    'radiance': {
        'key': 'radiance',
        'name': 'Radianță',
        'icon': '☀️',
        'nature': 'light',
        'type': 'attack',
        'power': 1.5,
        'accuracy': 0.9,
        'unlock_level': 10,
        'species': None,
        'max_mp':  15,
        'natures': ['light'],
        'effect': {
            'type': 'attack_down',
            'chance': 0.35,
            'value': 20,
            'turns': 2,
        },
    },
    'divine_judgment': {
        'key': 'divine_judgment',
        'name': 'Judecată Divină',
        'icon': '⚖️',
        'nature': 'light',
        'type': 'attack',
        'power': 2.2,
        'accuracy': 0.8,
        'unlock_level': 20,
        'species': None,
        'max_mp':  15,
        'natures': ['light'],
        'effect': {
            'type': 'heal',
            'chance': 0.5,
            'value': 20,
            'turns': 1,
        },
    },
}


# ─────────────────────────────────────────────
# HELPER — returneaza move set pentru un pet
# 4 move-uri: scratch (basic) + 3 din natura,
# deblocate progresiv pe nivel
# ─────────────────────────────────────────────

def get_moveset(species: str, nature: str | None, level: int) -> list[dict]:
    """
    Returneaza lista de 4 move-uri disponibile pentru un pet.
    - Slot 1: scratch (basic, intotdeauna)
    - Slot 2: headbutt (basic, intotdeauna)
    - Slot 3-4: move-uri din natura, deblocate pe nivel
    """
    result = [MOVES['scratch'], MOVES['headbutt']]

    if nature:
        # Filtreaza move-urile specifice naturii, sortate dupa unlock_level
        nature_moves = sorted(
            [m for m in MOVES.values()
             if m['natures'] and nature in m['natures']
             and m['unlock_level'] <= level],
            key=lambda m: m['unlock_level']
        )
        # Ia cel mult 2, preferand cele mai avansate
        advanced = nature_moves[-2:] if len(nature_moves) >= 2 else nature_moves
        result.extend(advanced)

    # Completeaza pana la 4 cu scratch daca lipseste natura
    while len(result) < 4:
        result.append(MOVES['scratch'])

    return result[:4]


def get_move(move_key: str) -> dict | None:
    return MOVES.get(move_key)
