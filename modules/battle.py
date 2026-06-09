"""
modules/battle.py
Sistemul de lupta PvE Arena.
"""
import random
import math
from modules.db import get_db
from modules.pets import get_pet, get_form
from cogs.petgame_stats import get_stats_at_level
from cogs.petgame_natures import get_interaction
from moves_config import get_moveset, get_move


# ─────────────────────────────────────────────
# GENERARE NPC INAMIC
# ─────────────────────────────────────────────

SPECIES_LIST   = ['dog', 'cat', 'blackcat', 'duck']
NATURES_LIST   = ['fire', 'water', 'nature', 'earth', 'storm', 'ice', 'shadow', 'crystal', 'steel', 'light']
SPECIES_NAMES  = {'dog': 'Câine', 'cat': 'Pisică', 'blackcat': 'Pisică Neagră', 'duck': 'Rață'}
NPC_NAMES      = [
    'Brutus', 'Fang', 'Claw', 'Shadow', 'Blaze', 'Storm', 'Rex',
    'Nova', 'Zephyr', 'Ember', 'Frost', 'Titan', 'Viper', 'Ace'
]


def generate_npc(player_level: int) -> dict:
    """Genereaza un NPC random cu nivel apropriat (+-3 fata de player)."""
    level     = max(1, player_level + random.randint(-3, 3))
    species   = random.choice(SPECIES_LIST)
    nature    = random.choice(NATURES_LIST)
    form      = get_form(level)
    stats     = get_stats_at_level(species, nature, level, form)
    moveset   = get_moveset(species, nature, level)
    name      = random.choice(NPC_NAMES)

    gender     = random.choice(['Male', 'Female'])
    stage      = f'Stage{form}'
    image_url  = f'/static/00transparent/{species}/{stage}-Basic-Form-{gender}.png'

    return {
        'id':           f'npc_{random.randint(10000, 99999)}',
        'name':         name,
        'species':      species,
        'species_name': SPECIES_NAMES.get(species, species),
        'nature':       nature,
        'level':        level,
        'form':         form,
        'hp_max':       stats['hp'],
        'hp_current':   stats['hp'],
        'stats':        stats,
        'moveset':      [m['key'] for m in moveset],
        'image_url':    image_url,
        'is_npc':       True,
        'status':       None,  # stun, burn, poison, freeze
        'status_turns': 0,
        'status_value': 0,
        'shield':       0,
        'speed_mod':    0,
        'attack_mod':   0,
        'evasion_mod':  0,
    }


# ─────────────────────────────────────────────
# BUILD COMBATANT din pet DB
# ─────────────────────────────────────────────

def build_combatant(pet: dict) -> dict:
    """Construieste structura de combatant din datele petului."""
    level   = pet['level']
    form    = get_form(level)
    species = pet['species']
    nature  = pet.get('nature')
    stats   = get_stats_at_level(species, nature, level, form)
    moveset = get_moveset(species, nature, level)

    return {
        'id':           pet.get('id', 0),
        'name':         pet['name'],
        'species':      species,
        'species_name': SPECIES_NAMES.get(species, species),
        'nature':       nature,
        'level':        level,
        'form':         form,
        'hp_max':       stats['hp'],
        'hp_current':   min(pet.get('hp_current', stats['hp']), stats['hp']),
        'stats':        stats,
        'moveset':      [m['key'] for m in moveset],
        'image_url':    pet.get('image_url', f'/static/pets/{species}/00transparent/form{form}.png'),
        'is_npc':       False,
        'status':       None,
        'status_turns': 0,
        'status_value': 0,
        'shield':       0,
        'speed_mod':    0,
        'attack_mod':   0,
        'evasion_mod':  0,
    }


# ─────────────────────────────────────────────
# CALCUL DAMAGE
# ─────────────────────────────────────────────

def calculate_damage(attacker: dict, defender: dict, move: dict) -> tuple[int, str]:
    """
    Calculeaza damage-ul unui move.
    Returneaza (damage, effectiveness_label).
    """
    if move['type'] in ('status', 'heal'):
        return 0, ''

    base_attack  = attacker['stats']['attack'] + attacker['attack_mod']
    base_defense = max(1, defender['stats']['defense'])
    power        = move['power']

    # Interactiune natura
    effectiveness = 1.0
    label = ''
    if move.get('nature') and defender.get('nature'):
        result = get_interaction(move['nature'], defender['nature'])
        effectiveness = result['multiplier']
        label = result['label']
        if effectiveness == 0.0:
            return 0, label

    # Formula damage
    damage = math.floor(base_attack * power * effectiveness / base_defense * 10)
    damage = max(1, damage)

    # Random variance ±10%
    damage = math.floor(damage * random.uniform(0.9, 1.1))

    # Scade shield daca exista
    if defender['shield'] > 0:
        absorbed = min(defender['shield'], damage)
        damage   = damage - absorbed

    return max(0, damage), label


# ─────────────────────────────────────────────
# APLICA EFECT
# ─────────────────────────────────────────────

def apply_effect(target: dict, effect: dict) -> str | None:
    """Aplica efectul unui move pe target. Returneaza mesaj sau None."""
    if not effect:
        return None
    if random.random() > effect['chance']:
        return None

    etype = effect['type']
    val   = effect['value']
    turns = effect['turns']

    if etype == 'stun':
        target['status'] = 'stun'
        target['status_turns'] = turns
        return f'{target["name"]} este amețit!'

    elif etype == 'burn':
        target['status'] = 'burn'
        target['status_turns'] = turns
        target['status_value'] = val
        return f'{target["name"]} este în flăcări! (-{val} HP/tur)'

    elif etype == 'poison':
        target['status'] = 'poison'
        target['status_turns'] = turns
        target['status_value'] = val
        return f'{target["name"]} este otrăvit! (-{val} HP/tur)'

    elif etype == 'freeze':
        target['status'] = 'freeze'
        target['status_turns'] = turns
        return f'{target["name"]} este înghețat!'

    elif etype == 'heal':
        healed = math.floor(target['hp_max'] * val / 100)
        target['hp_current'] = min(target['hp_max'], target['hp_current'] + healed)
        return f'{target["name"]} s-a vindecat cu {healed} HP!'

    elif etype == 'shield':
        target['shield'] = val
        return f'{target["name"]} are un scut de {val}!'

    elif etype == 'speed_down':
        target['speed_mod'] = -val
        target['status_turns'] = max(target['status_turns'], turns)
        return f'Viteza lui {target["name"]} a scăzut!'

    elif etype == 'speed_up':
        target['speed_mod'] = val
        return f'Viteza lui {target["name"]} a crescut!'

    elif etype == 'attack_down':
        target['attack_mod'] = -val
        return f'Atacul lui {target["name"]} a scăzut!'

    elif etype == 'evasion_up':
        target['evasion_mod'] = val
        return f'Eludarea lui {target["name"]} a crescut!'

    elif etype == 'lifesteal':
        steal = math.floor(target['hp_current'] * val / 100)
        return f'life_steal:{steal}'  # procesat de caller

    elif etype == 'reflect':
        target['shield'] = val
        return f'{target["name"]} reflectă {val}% din damage!'

    return None


# ─────────────────────────────────────────────
# PROCESEAZA TUR STATUS
# ─────────────────────────────────────────────

def process_status_tick(combatant: dict) -> list[str]:
    """Aplica damage/efecte de status la inceput de tur. Returneaza log."""
    log = []
    status = combatant.get('status')

    if status in ('burn', 'poison') and combatant['status_turns'] > 0:
        dmg = combatant['status_value']
        combatant['hp_current'] = max(0, combatant['hp_current'] - dmg)
        combatant['status_turns'] -= 1
        label = '🔥' if status == 'burn' else '☠️'
        log.append(f'{label} {combatant["name"]} pierde {dmg} HP din {status}!')
        if combatant['status_turns'] == 0:
            combatant['status'] = None

    elif status in ('stun', 'freeze') and combatant['status_turns'] > 0:
        combatant['status_turns'] -= 1
        if combatant['status_turns'] == 0:
            combatant['status'] = None

    return log


# ─────────────────────────────────────────────
# EXECUTA MOVE
# ─────────────────────────────────────────────

def execute_move(attacker: dict, defender: dict, move_key: str) -> dict:
    """
    Executa un move. Returneaza log-ul actiunii.
    """
    move = get_move(move_key)
    if not move:
        return {'log': [f'{attacker["name"]} nu cunoaște move-ul!'], 'hit': False}

    log    = []
    result = {'log': log, 'hit': False, 'damage': 0, 'effectiveness': '', 'effect_msg': None}

    # Stun/freeze blocheaza atacul
    if attacker.get('status') in ('stun', 'freeze'):
        log.append(f'{attacker["name"]} nu poate acționa! ({attacker["status"]})')
        return result

    # Accuracy check
    evasion_bonus = defender.get('evasion_mod', 0) / 100
    hit_chance    = move['accuracy'] * (1 - evasion_bonus * 0.5)
    if random.random() > hit_chance:
        log.append(f'{attacker["name"]} a ratat!')
        return result

    result['hit'] = True

    if move['type'] == 'heal':
        effect_msg = apply_effect(attacker, move.get('effect'))
        if effect_msg:
            log.append(effect_msg)
        result['effect_msg'] = effect_msg

    elif move['type'] == 'status':
        log.append(f'{attacker["name"]} folosește {move["name"]}!')
        effect_msg = apply_effect(defender if 'down' in move.get('effect', {}).get('type', '') else attacker, move.get('effect'))
        if effect_msg:
            log.append(effect_msg)
        result['effect_msg'] = effect_msg

    else:  # attack
        damage, eff_label = calculate_damage(attacker, defender, move)
        result['damage']        = damage
        result['effectiveness'] = eff_label

        if eff_label == 'Imun!':
            log.append(f'{attacker["name"]} folosește {move["name"]} — {eff_label}')
        else:
            defender['hp_current'] = max(0, defender['hp_current'] - damage)
            log.append(f'{attacker["name"]} folosește {move["name"]}! (-{damage} HP{" — " + eff_label if eff_label else ""})')

            # Aplica efect
            if move.get('effect'):
                effect_msg = apply_effect(defender, move['effect'])
                if effect_msg:
                    if effect_msg.startswith('life_steal:'):
                        steal = int(effect_msg.split(':')[1])
                        attacker['hp_current'] = min(attacker['hp_max'], attacker['hp_current'] + steal)
                        log.append(f'{attacker["name"]} absoarbe {steal} HP!')
                    else:
                        log.append(effect_msg)
                    result['effect_msg'] = effect_msg

    return result


# ─────────────────────────────────────────────
# TUR COMPLET (player move + npc ai)
# ─────────────────────────────────────────────

def get_speed(combatant: dict) -> int:
    return combatant['stats']['speed'] + combatant.get('speed_mod', 0)


def npc_choose_move(npc: dict, player: dict) -> str:
    """AI simplu — alege random din moveset, cu preferinta pentru attack."""
    moveset = npc['moveset']
    attacks = [m for m in moveset if get_move(m) and get_move(m)['type'] == 'attack']
    if attacks and random.random() < 0.7:
        return random.choice(attacks)
    return random.choice(moveset)


def execute_turn(player: dict, npc: dict, player_move_key: str) -> dict:
    """
    Executa un tur complet:
    1. Status tick pentru amandoi
    2. Decide ordinea (speed)
    3. Primul atacator executa
    4. Daca adversarul e in viata, executa al doilea
    5. Returneaza starea dupa tur
    """
    log = []

    # Status ticks
    p_status_log = process_status_tick(player)
    n_status_log = process_status_tick(npc)
    log.extend(p_status_log)
    log.extend(n_status_log)

    # NPC alege move
    npc_move_key = npc_choose_move(npc, player)

    # Ordine atac
    player_speed = get_speed(player)
    npc_speed    = get_speed(npc)

    if player_speed >= npc_speed:
        first, second         = player, npc
        first_move, sec_move  = player_move_key, npc_move_key
    else:
        first, second         = npc, player
        first_move, sec_move  = npc_move_key, player_move_key

    # Primul atac
    r1 = execute_move(first, second, first_move)
    log.extend(r1['log'])

    # Al doilea atac (daca al doilea e in viata)
    r2 = {'log': [], 'damage': 0}
    if second['hp_current'] > 0:
        r2 = execute_move(second, first, sec_move)
        log.extend(r2['log'])

    # Determine winner
    winner = None
    if player['hp_current'] <= 0:
        winner = 'npc'
        log.append(f'💀 {player["name"]} a căzut!')
    elif npc['hp_current'] <= 0:
        winner = 'player'
        log.append(f'🏆 {npc["name"]} a fost înfrânt!')

    return {
        'log':          log,
        'player':       _combatant_snapshot(player),
        'npc':          _combatant_snapshot(npc),
        'winner':       winner,
        'npc_move_key': npc_move_key,
    }


def _combatant_snapshot(c: dict) -> dict:
    """Snapshot minimal pentru frontend."""
    return {
        'id':           c['id'],
        'name':         c['name'],
        'hp_current':   c['hp_current'],
        'hp_max':       c['hp_max'],
        'status':       c.get('status'),
        'shield':       c.get('shield', 0),
        'speed_mod':    c.get('speed_mod', 0),
        'attack_mod':   c.get('attack_mod', 0),
        'evasion_mod':  c.get('evasion_mod', 0),
    }


# ─────────────────────────────────────────────
# RECOMPENSE DUPA LUPTA
# ─────────────────────────────────────────────

def calculate_reward(player_level: int, npc_level: int, won: bool) -> int:
    """Calculeaza dacoins castigati."""
    if not won:
        return 0
    base   = 50 + npc_level * 10
    bonus  = max(0, npc_level - player_level) * 20
    return base + bonus + random.randint(0, 50)
