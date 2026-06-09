"""
Regnum Dacorum — Petomania Web
================================
Flask app independent pe portul 5002.
OAuth Discord propriu — redirect URI: http://204.168.179.80:5002/joc/petomania/callback
                                  sau: https://regnum-dacorum.ro/joc/petomania/callback

Rulare:
    python3 petgame_app.py

In productie:
    screen -dmS petomania python3 petgame_app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, abort, Response
)
import sqlite3
import secrets
import requests
import time
import json
import threading
import io
import urllib.request
import concurrent.futures
from functools import wraps
from datetime import datetime, timezone
from dotenv import load_dotenv

from cogs.petgame_config import SPECIES
from petgame_room_config import ROOM_ITEMS, get_item, get_default, resolve_file
from cogs.petgame_natures import NATURES
from cogs.petgame_stats import get_stats_at_level, FORM_MULTIPLIERS
from inventory_config import (
    INVENTORY_ITEMS, CATEGORY_SLOTS, STACK_MAX,
    CATEGORY_NAMES, CATEGORY_ORDER, USE_STUB_MESSAGES,
    get_item as inv_get_item,
)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder='templates_site',
    static_folder='static_site',
    static_url_path='/static'
)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv('PETOMANIA_SECRET_KEY', secrets.token_hex(32))

DB_PATH = '/root/village-bot/village-bot/stats.db'
DISCORD_CLIENT_ID     = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_API           = 'https://discord.com/api/v10'
DISCORD_OAUTH_AUTHORIZE = 'https://discord.com/oauth2/authorize'
DISCORD_OAUTH_TOKEN     = f'{DISCORD_API}/oauth2/token'
REDIRECT_URI = os.getenv(
    'PETOMANIA_REDIRECT_URI',
    'http://204.168.179.80:5002/joc/petomania/callback'
)

BOT_TOKEN = os.getenv('TOKEN')
GUILD_ID  = os.getenv('GUILD_ID', '1499052609523986535')

# Role IDs pentru dialog Lunara Silvermist
ROLE_NEW      = '1499053171656495224'
ROLES_VETERAN = ['1499053556383350945','1499053668769726617','1499053737178828991',
                 '1499053813414236270','1499053921459765479','1499053999436071053']
ROLES_CHAMPION = ['1511642120862302270','1500078293721022655']

# Nume roluri pentru afisare
ROLE_NAMES = {
    '1499053556383350945': ('Explorator', '#71c9f8'),
    '1499053668769726617': ('Veteran',    '#5865f2'),
    '1499053737178828991': ('Erou',       '#57f287'),
    '1499053813414236270': ('Maestru',    '#fee75c'),
    '1499053921459765479': ('Legend',     '#f47fff'),
    '1499053999436071053': ('Mitic',      '#eb459e'),
    '1511642120862302270': ('Campion',    '#ffd700'),
    '1500078293721022655': ('Mare Campion','#ffd700'),
}

GITHUB_BASE = 'https://raw.githubusercontent.com/keserdark/village-bot/main/PetGame/static'

# ─────────────────────────────────────────────
# TOKEN STORE — URL temporare (expira in 10s)
# ─────────────────────────────────────────────

TOKEN_TTL   = 10  # secunde
_token_store = {}  # {token: {'url': str, 'expires': float}}
_token_lock  = threading.Lock()

def _cleanup_tokens():
    now = time.time()
    with _token_lock:
        expired = [k for k, v in _token_store.items() if v['expires'] < now]
        for k in expired:
            del _token_store[k]

def make_token(url: str) -> str:
    """Genereaza un token temporar pentru un URL de imagine."""
    _cleanup_tokens()
    token = secrets.token_urlsafe(24)
    with _token_lock:
        _token_store[token] = {
            'url':     url,
            'expires': time.time() + TOKEN_TTL,
        }
    return token

def get_signed_url(url: str) -> str:
    """Returneaza URL-ul semnat pentru template."""
    token = make_token(url)
    return f"/joc/petomania/img/{token}"


# Constante bot
DECAY_INTERVAL   = 120
SLEEP_REGEN      = 2
FEED_AMOUNT      = 10
WASH_AMOUNT      = 10
PLAY_HAPPINESS   = 10
PLAY_ENERGY_COST = 5
PLAY_HUNGER_COST = 5
XP_PER_MINUTE    = 1
XP_TICK          = 60

# ─────────────────────────────────────────────
# CATALOG IMBUNATATIRI
# Editeaza petgame_room_config.py — nu acest fisier
# ─────────────────────────────────────────────

# SHOP_ITEMS pastrat pentru compatibilitate API — generat din ROOM_ITEMS
SHOP_ITEMS = {
    cat: {item['key']: item for item in items}
    for cat, items in ROOM_ITEMS.items()
}

# ─────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Dacoins
    c.execute('''
        CREATE TABLE IF NOT EXISTS dacoins (
            user_id    INTEGER PRIMARY KEY,
            balance    INTEGER NOT NULL DEFAULT 300,
            updated_at TEXT
        )
    ''')

    # Room config per user
    c.execute('''
        CREATE TABLE IF NOT EXISTS room_config (
            user_id INTEGER PRIMARY KEY,
            wall    TEXT NOT NULL DEFAULT "Wall1-Wood",
            floor   TEXT NOT NULL DEFAULT "Floor1-Wood",
            chimney TEXT NOT NULL DEFAULT "Chimney1-Stone",
            items   TEXT NOT NULL DEFAULT "{}"
        )
    ''')

    # Lady interactions
    c.execute('''
        CREATE TABLE IF NOT EXISTS lady_interactions (
            user_id           INTEGER PRIMARY KEY,
            first_interaction INTEGER NOT NULL DEFAULT 1,
            player_name       TEXT,
            has_companicon    INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # Migrare — adauga has_companicon daca lipseste
    try:
        c.execute('ALTER TABLE lady_interactions ADD COLUMN has_companicon INTEGER NOT NULL DEFAULT 0')
    except Exception:
        pass

    # ── INVENTORY (Rucsac) ───────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            category    TEXT NOT NULL,
            item_key    TEXT NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            UNIQUE(user_id, category, item_key)
        )
    ''')

    # ── BADGES (Insigne arena) ───────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            badge_key TEXT NOT NULL,
            earned_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
            UNIQUE(user_id, badge_key)
        )
    ''')

    # ── MIGRARE hp / hp_current pe pets si menagerie ─────────────────
    for col in ('hp', 'hp_current'):
        try:
            c.execute(f'ALTER TABLE pets ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0')
        except Exception:
            pass
    for col in ('hp', 'hp_current'):
        try:
            c.execute(f'ALTER TABLE menagerie ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0')
        except Exception:
            pass

    # ── LOADOUT ──────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS loadout (
            user_id    INTEGER PRIMARY KEY,
            slot_2     INTEGER,
            slot_3     INTEGER,
            slot_4     INTEGER,
            slot_5     INTEGER
        )
    ''')

    conn.commit()
    conn.close()

def get_dacoins(user_id: int) -> int:
    conn = get_db()
    row = conn.execute('SELECT balance FROM dacoins WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    if not row:
        # Primul acces — initializeaza cu 300
        conn = get_db()
        conn.execute(
            'INSERT OR IGNORE INTO dacoins (user_id, balance, updated_at) VALUES (?, 300, ?)',
            (user_id, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return 300
    return row['balance']

def spend_dacoins(user_id: int, amount: int) -> bool:
    """Returneaza True daca tranzactia a reusit."""
    conn = get_db()
    row = conn.execute('SELECT balance FROM dacoins WHERE user_id = ?', (user_id,)).fetchone()
    if not row or row['balance'] < amount:
        conn.close()
        return False
    conn.execute(
        'UPDATE dacoins SET balance = balance - ?, updated_at = ? WHERE user_id = ?',
        (amount, datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()
    return True

def get_room_config(user_id: int) -> dict:
    conn = get_db()
    row = conn.execute('SELECT * FROM room_config WHERE user_id = ?', (user_id,)).fetchone()
    if not row:
        conn.execute(
            'INSERT OR IGNORE INTO room_config (user_id) VALUES (?)', (user_id,)
        )
        conn.commit()
        conn.close()
        return {
            'wall':    'Wall1-Wood',
            'floor':   'Floor1-Wood',
            'chimney': 'Chimney1-Stone',
            'items':   {},
        }
    conn.close()
    return {
        'wall':    row['wall'],
        'floor':   row['floor'],
        'chimney': row['chimney'],
        'items':   json.loads(row['items'] or '{}'),
    }

def save_room_config(user_id: int, wall: str, floor: str, chimney: str, items: dict):
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO room_config (user_id, wall, floor, chimney, items)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, wall, floor, chimney, json.dumps(items)))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# HELPERS PET
# ─────────────────────────────────────────────

def get_form(level: int) -> int:
    if level < 15: return 1
    if level < 30: return 2
    return 3

def xp_for_level(level: int) -> int:
    return level * 60

def get_state(hunger, happiness, cleanliness, energy, sleeping) -> str:
    if sleeping:          return 'Sleep'
    if cleanliness < 30:  return 'Dirty'
    if hunger < 30:       return 'Hungry'
    if happiness < 30:    return 'Sad'
    if energy < 30:       return 'Sleep'
    return 'Basic'

def get_image_url(species: str, form: int, state: str, gender: str = 'male') -> str:
    base = f"{GITHUB_BASE}/00transparent/{species}"
    
    # Stage 1 fara gen pentru duck
    if species == 'duck' and form == 1:
        return f"{base}/Stage{form}-{state}-Form.png"
    
    if species in ('blackcat', 'dog', 'duck'):
        gender_suffix = 'Male' if gender == 'male' else 'Female'
        return f"{base}/Stage{form}-{state}-Form-{gender_suffix}.png"
    
    # cat — fara gen
    return f"{base}/Stage{form}-{state}-Form.png"

    # Fallback — construim URL direct din naming convention
    gender_suffix = ''
    if species in ('blackcat', 'dog', 'duck'):
        gender_suffix = f"-{'Male' if gender == 'male' else 'Female'}"

    return f"{base}/Stage{form}-{state}-Form{gender_suffix}.png"

def get_room_url(category: str, key: str, room: dict = None) -> str:
    """
    Returneaza URL-ul GitHub pentru un asset de camera.
    Daca room e furnizat, aplica variantele secrete.
    """
    if room:
        filename = resolve_file(category, key, room)
    else:
        item = get_item(category, key)
        filename = item['file'] if item else f'{key}.png'
    return f"{GITHUB_BASE}/room1/{filename}"

def format_age(born_at: int) -> str:
    now  = datetime.now(timezone.utc)
    born = datetime.fromtimestamp(born_at, tz=timezone.utc)
    days = (now - born).days
    years, months = days // 365, (days % 365) // 30
    if years > 0:
        return f"{years} {'an' if years == 1 else 'ani'}, {(days % 365) // 30} luni"
    if months > 0:
        return f"{months} {'lună' if months == 1 else 'luni'}, {days % 30} zile"
    return f"{days} {'zi' if days == 1 else 'zile'}"

def get_pet(user_id: int):
    conn = get_db()
    pet  = conn.execute('SELECT * FROM pets WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return pet

def get_menagerie(user_id: int):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM menagerie WHERE user_id = ? ORDER BY stored_at DESC', (user_id,)
    ).fetchall()
    conn.close()
    return rows

def apply_decay(pet) -> dict:
    now     = int(time.time())
    elapsed = now - pet['last_decay']
    ticks   = elapsed // DECAY_INTERVAL
    if ticks <= 0:
        return dict(pet)
    p = dict(pet)
    if p['sleeping']:
        sleep_minutes    = elapsed // 60
        p['energy']      = min(100, p['energy'] + sleep_minutes * SLEEP_REGEN)
        p['hunger']      = max(0, p['hunger']      - ticks)
        p['happiness']   = max(0, p['happiness']   - ticks)
        p['cleanliness'] = max(0, p['cleanliness'] - ticks)
        if p['energy'] >= 100:
            p['sleeping']      = 0
            p['sleep_started'] = None
            p['energy']        = 100
    else:
        p['hunger']      = max(0, p['hunger']      - ticks)
        p['happiness']   = max(0, p['happiness']   - ticks)
        p['cleanliness'] = max(0, p['cleanliness'] - ticks)
        p['energy']      = max(0, p['energy']      - ticks)
    p['last_decay'] = now
    return p

def apply_xp_tick(p: dict) -> dict:
    now     = int(time.time())
    if p['sleeping']:
        p['last_xp_tick'] = now
        return p
    elapsed = now - p['last_xp_tick']
    minutes = elapsed // XP_TICK
    if minutes <= 0:
        return p
    if p['hunger'] > 30 and p['happiness'] > 30 and p['cleanliness'] > 30 and p['energy'] > 30:
        p['xp'] += minutes * XP_PER_MINUTE
        while True:
            needed = xp_for_level(p['level'])
            if p['xp'] >= needed and p['level'] < 100:
                p['xp']    -= needed
                p['level'] += 1
            else:
                break
    p['last_xp_tick'] = now
    return p

def update_pet(user_id: int, **kwargs):
    conn = get_db()
    sets = ', '.join(f'{k}=?' for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    conn.execute(f'UPDATE pets SET {sets} WHERE user_id = ?', vals)
    conn.commit()
    conn.close()

def sync_pet(user_id: int):
    pet = get_pet(user_id)
    if not pet:
        return None
    p = apply_decay(pet)
    p = apply_xp_tick(p)
    update_pet(user_id,
        hunger=p['hunger'], happiness=p['happiness'],
        cleanliness=p['cleanliness'], energy=p['energy'],
        sleeping=p['sleeping'], sleep_started=p['sleep_started'],
        level=p['level'], xp=p['xp'],
        last_decay=p['last_decay'], last_xp_tick=p['last_xp_tick']
    )
    return p

def build_pet_context(p: dict) -> dict:
    p         = dict(p)
    form      = get_form(p['level'])
    state     = get_state(p['hunger'], p['happiness'], p['cleanliness'], p['energy'], bool(p['sleeping']))
    image_url = get_image_url(p['species'], form, state, p['gender'])
    nature    = p.get('nature')
    nat_data  = NATURES.get(nature) if nature else None
    xp_needed = xp_for_level(p['level'])
    xp_pct    = round((p['xp'] / xp_needed) * 100) if xp_needed > 0 else 100
    stats     = get_stats_at_level(p['species'], nature, p['level'], form)
    bonus_stat = nat_data['bonus_stat'] if nat_data else None
    state_labels = {
        'Basic':  ('😊', 'Fericit'),
        'Hungry': ('🍖', 'Flămând'),
        'Dirty':  ('🤢', 'Murdar'),
        'Sad':    ('😢', 'Trist'),
        'Sleep':  ('😴', 'Adormit' if p['sleeping'] else 'Obosit'),
    }
    return {
        **p,
        'form':         form,
        'form_max':     len(FORM_MULTIPLIERS),
        'state':        state,
        'state_label':  state_labels.get(state, ('❓', state)),
        'image_url':    get_signed_url(image_url),
        'nat_data':     nat_data,
        'xp_needed':    xp_needed,
        'xp_pct':       xp_pct,
        'stats':        stats,
        'bonus_stat':   bonus_stat,
        'age':          format_age(p['born_at']),
        'gender_icon':  '♂️' if p['gender'] == 'male' else '♀️',
        'species_name': SPECIES.get(p['species'], {}).get('name', p['species']),
    }

# ─────────────────────────────────────────────
# INVENTORY HELPERS
# ─────────────────────────────────────────────

def inv_get_all(user_id: int) -> dict:
    """Returnează inventarul complet al unui user, grupat pe categorii."""
    conn = get_db()
    rows = conn.execute(
        'SELECT category, item_key, quantity FROM inventory WHERE user_id = ? ORDER BY rowid',
        (user_id,)
    ).fetchall()
    conn.close()
    result = {cat: [] for cat in CATEGORY_ORDER}
    for r in rows:
        cat = r['category']
        if cat in result:
            result[cat].append({'item_key': r['item_key'], 'quantity': r['quantity']})
    return result

def inv_add(user_id: int, category: str, item_key: str, qty: int = 1) -> dict:
    """
    Adaugă qty dintr-un item în inventar.
    Returnează {'ok': True} sau {'ok': False, 'error': '...'}.
    Sursa nu contează — funcționează pentru shop, drop, quest, trade.
    """
    if qty < 1:
        return {'ok': False, 'error': 'Cantitate invalidă.'}
    item_data = inv_get_item(category, item_key)
    if not item_data:
        return {'ok': False, 'error': f'Item necunoscut: {item_key}'}
    conn = get_db()
    existing = conn.execute(
        'SELECT quantity FROM inventory WHERE user_id = ? AND category = ? AND item_key = ?',
        (user_id, category, item_key)
    ).fetchone()
    if existing:
        new_qty = existing['quantity'] + qty
        if new_qty > STACK_MAX:
            conn.close()
            return {'ok': False, 'error': f'Stack plin ({STACK_MAX} max).'}
        conn.execute(
            'UPDATE inventory SET quantity = ? WHERE user_id = ? AND category = ? AND item_key = ?',
            (new_qty, user_id, category, item_key)
        )
    else:
        slot_count = conn.execute(
            'SELECT COUNT(*) as cnt FROM inventory WHERE user_id = ? AND category = ?',
            (user_id, category)
        ).fetchone()['cnt']
        if slot_count >= CATEGORY_SLOTS:
            conn.close()
            return {'ok': False, 'error': f'Categoria "{CATEGORY_NAMES.get(category, category)}" este plină (10 sloturi).'}
        if qty > STACK_MAX:
            conn.close()
            return {'ok': False, 'error': f'Cantitate depășește stack-ul maxim ({STACK_MAX}).'}
        conn.execute(
            'INSERT INTO inventory (user_id, category, item_key, quantity) VALUES (?, ?, ?, ?)',
            (user_id, category, item_key, qty)
        )
    conn.commit()
    conn.close()
    return {'ok': True}

def inv_remove(user_id: int, category: str, item_key: str, qty: int = 1) -> dict:
    """
    Scade qty dintr-un item. Șterge slotul dacă ajunge la 0.
    Returnează {'ok': True} sau {'ok': False, 'error': '...'}.
    """
    conn = get_db()
    existing = conn.execute(
        'SELECT quantity FROM inventory WHERE user_id = ? AND category = ? AND item_key = ?',
        (user_id, category, item_key)
    ).fetchone()
    if not existing or existing['quantity'] < qty:
        conn.close()
        return {'ok': False, 'error': 'Cantitate insuficientă.'}
    new_qty = existing['quantity'] - qty
    if new_qty == 0:
        conn.execute(
            'DELETE FROM inventory WHERE user_id = ? AND category = ? AND item_key = ?',
            (user_id, category, item_key)
        )
    else:
        conn.execute(
            'UPDATE inventory SET quantity = ? WHERE user_id = ? AND category = ? AND item_key = ?',
            (new_qty, user_id, category, item_key)
        )
    conn.commit()
    conn.close()
    return {'ok': True}

def inv_build_context(user_id: int) -> list:
    """Construiește contextul complet al inventarului pentru template."""
    raw = inv_get_all(user_id)
    categories = []
    for cat_key in CATEGORY_ORDER:
        items_in_cat = raw.get(cat_key, [])
        slots = []
        for slot_data in items_in_cat:
            item_cfg = inv_get_item(cat_key, slot_data['item_key'])
            if item_cfg:
                slots.append({
                    'item_key':              slot_data['item_key'],
                    'quantity':              slot_data['quantity'],
                    'name':                  item_cfg['name'],
                    'desc':                  item_cfg['desc'],
                    'icon':                  item_cfg['icon'],
                    'quest_item':            item_cfg.get('quest_item', False),
                    'usable_outside_battle': item_cfg.get('usable_outside_battle', True),
                    'usable_in_zone':        item_cfg.get('usable_in_zone', False),
                })
        while len(slots) < CATEGORY_SLOTS:
            slots.append(None)
        categories.append({
            'key':        cat_key,
            'name':       CATEGORY_NAMES[cat_key],
            'slots':      slots,
            'slots_used': len(items_in_cat),
        })
    return categories

def _get_hp_max(p: dict) -> int:
    """Calculează HP max al petului din stats."""
    form  = get_form(p['level'])
    stats = get_stats_at_level(p['species'], p.get('nature'), p['level'], form)
    return stats['hp']

def sync_pet_hp(user_id: int):
    """
    Sincronizează hp (max) pe petul activ.
    Apelat după sync_pet() pentru a ține hp-ul max actualizat cu levelup-urile.
    hp_current nu are decay — nu se modifică automat.
    """
    pet = get_pet(user_id)
    if not pet:
        return
    p      = dict(pet)
    hp_max = _get_hp_max(p)
    hp_cur = p['hp_current'] if p['hp_current'] > 0 else hp_max
    hp_cur = min(hp_cur, hp_max)
    conn = get_db()
    conn.execute(
        'UPDATE pets SET hp = ?, hp_current = ? WHERE user_id = ?',
        (hp_max, hp_cur, user_id)
    )
    conn.commit()
    conn.close()

def use_item(user_id: int, category: str, item_key: str) -> dict:
    """
    Aplică efectul unui item pe petul activ al userului.
    Returnează {'ok': True/False, 'msg': '...'}.
    """
    item_cfg = inv_get_item(category, item_key)
    if not item_cfg:
        return {'ok': False, 'msg': 'Item necunoscut.'}

    # Quest items — fără "Folosește"
    if item_cfg.get('quest_item'):
        return {'ok': False, 'msg': 'Acest item nu poate fi folosit direct.'}

    # Items care necesită zonă specifică
    if item_cfg.get('usable_in_zone'):
        return {'ok': False, 'msg': USE_STUB_MESSAGES.get(category, 'Necesită zonă specifică.')}

    # Stub pentru categorii fără logică implementată încă
    if category in USE_STUB_MESSAGES and category not in ('mancare', 'medical'):
        return {'ok': False, 'msg': USE_STUB_MESSAGES[category]}

    pet = get_pet(user_id)
    if not pet:
        return {'ok': False, 'msg': 'Nu ai un companion activ.'}

    p       = dict(pet)
    effects = item_cfg.get('effects', {})
    changed = []

    # ── MÂNCARE ──────────────────────────────────────────────────────
    if category == 'mancare':
        if 'hunger' in effects:
            p['hunger'] = min(100, p['hunger'] + effects['hunger'])
            changed.append(f"Foame +{effects['hunger']}")
        if 'energy' in effects:
            p['energy'] = min(100, p['energy'] + effects['energy'])
            changed.append(f"Energie +{effects['energy']}")
        if 'hp' in effects:
            hp_max      = _get_hp_max(p)
            new_hp      = min(hp_max, p['hp_current'] + effects['hp'])
            p['hp_current'] = new_hp
            changed.append(f"HP +{effects['hp']}")

    # ── MEDICAL ──────────────────────────────────────────────────────
    elif category == 'medical':
        if 'hp' in effects:
            hp_max  = _get_hp_max(p)
            old_hp  = p['hp_current']
            new_hp  = min(hp_max, old_hp + effects['hp'])
            healed  = new_hp - old_hp
            if healed <= 0:
                return {'ok': False, 'msg': 'HP-ul companionului este deja plin.'}
            p['hp_current'] = new_hp
            changed.append(f"HP +{healed}")

    if not changed:
        return {'ok': False, 'msg': 'Acest item nu are efect momentan.'}

    # Aplică modificările în DB
    conn = get_db()
    conn.execute(
        'UPDATE pets SET hunger = ?, energy = ?, hp_current = ? WHERE user_id = ?',
        (p['hunger'], p['energy'], p['hp_current'], user_id)
    )
    conn.commit()
    conn.close()

    inv_remove(user_id, category, item_key, 1)

    return {'ok': True, 'msg': '✅ ' + ' · '.join(changed)}

def rename_pet(user_id: int, new_name: str) -> dict:
    """Redenumește petul activ al userului."""
    new_name = new_name.strip()[:24]
    if len(new_name) < 2:
        return {'ok': False, 'error': 'Numele trebuie să aibă cel puțin 2 caractere.'}
    pet = get_pet(user_id)
    if not pet:
        return {'ok': False, 'error': 'Nu ai un companion activ.'}
    conn = get_db()
    conn.execute('UPDATE pets SET name = ? WHERE user_id = ?', (new_name, user_id))
    conn.commit()
    conn.close()
    return {'ok': True, 'name': new_name}

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

def get_current_user():
    if 'user_id' not in session:
        return None
    return {
        'id':       session['user_id'],
        'username': session.get('username', ''),
        'avatar':   session.get('avatar'),
    }

def avatar_url(user_id, avatar, size=64):
    if avatar:
        ext = 'gif' if avatar.startswith('a_') else 'png'
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}?size={size}"
    default = (int(user_id) >> 22) % 6
    return f"https://cdn.discordapp.com/embed/avatars/{default}.png"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            session['next_url'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# CONTEXT PROCESSOR
# ─────────────────────────────────────────────

@app.context_processor
def inject_globals():
    user = get_current_user()
    if user:
        user['avatar_url']     = avatar_url(user['id'], user['avatar'])
        user['dacoins']        = get_dacoins(int(user['id']))
        interaction            = get_lady_interaction(int(user['id']))
        user['has_companicon'] = interaction['has_companicon']
    return {
        'current_user': user,
        'now':          datetime.now(),
    }

# ─────────────────────────────────────────────
# OAUTH
# ─────────────────────────────────────────────

@app.route('/joc/petomania/login')
def login():
    state = secrets.token_urlsafe(24)
    session['oauth_state'] = state
    params = {
        'client_id':     DISCORD_CLIENT_ID,
        'redirect_uri':  REDIRECT_URI,
        'response_type': 'code',
        'scope':         'identify',
        'state':         state,
        'prompt':        'none',
    }
    query = '&'.join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    return redirect(f"{DISCORD_OAUTH_AUTHORIZE}?{query}")

@app.route('/joc/petomania/callback')
def oauth_callback():
    state          = request.args.get('state')
    expected_state = session.pop('oauth_state', None)
    if not state or state != expected_state:
        return render_template('petomania/error.html', error="State OAuth invalid.")
    code = request.args.get('code')
    if not code:
        return render_template('petomania/error.html', error="Nu am primit codul OAuth.")
    try:
        token_resp = requests.post(
            DISCORD_OAUTH_TOKEN,
            data={
                'client_id':     DISCORD_CLIENT_ID,
                'client_secret': DISCORD_CLIENT_SECRET,
                'grant_type':    'authorization_code',
                'code':          code,
                'redirect_uri':  REDIRECT_URI,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10,
        )
    except requests.RequestException as e:
        return render_template('petomania/error.html', error=f"Eroare conexiune Discord: {e}")
    if token_resp.status_code != 200:
        return render_template('petomania/error.html', error="Discord a respins codul OAuth.")
    token_data   = token_resp.json()
    access_token = token_data['access_token']
    try:
        user_resp = requests.get(
            f"{DISCORD_API}/users/@me",
            headers={'Authorization': f"Bearer {access_token}"},
            timeout=10,
        )
        user_resp.raise_for_status()
    except requests.RequestException:
        return render_template('petomania/error.html', error="Nu am putut prelua datele tale Discord.")
    user_data           = user_resp.json()
    session['user_id']  = user_data['id']
    session['username'] = user_data.get('global_name') or user_data['username']
    session['avatar']   = user_data.get('avatar')

    # Initializeaza dacoins si room config la primul login
    uid = int(user_data['id'])
    get_dacoins(uid)
    get_room_config(uid)

    next_url = session.pop('next_url', url_for('acasa'))
    return redirect(next_url)

@app.route('/joc/petomania/logout')
def logout():
    session.clear()
    return redirect(url_for('acasa'))

@app.route('/joc/petomania/img/<token>')
@login_required
def serve_img(token):
    now = time.time()
    with _token_lock:
        entry = _token_store.get(token)
        if not entry or entry['expires'] < now:
            abort(403)
        url = entry['url']
        # Token single-use — sterge dupa prima folosire
        del _token_store[token]
    return redirect(url)

# ─────────────────────────────────────────────
# PAGINI
# ─────────────────────────────────────────────

@app.route('/joc/petomania/')
@app.route('/joc/petomania')
@login_required
def acasa():
    user = get_current_user()
    uid  = int(user['id'])
    p    = sync_pet(uid)
    pet  = build_pet_context(p) if p else None
    room = get_room_config(uid)

    # Construim URL-urile pentru layerele camerei (cu variante secrete)
    room_urls = {
        'wall':    get_signed_url(get_room_url('wall',    room['wall'],    room)),
        'floor':   get_signed_url(get_room_url('floor',   room['floor'],   room)),
        'chimney': get_signed_url(get_room_url('chimney', room['chimney'], room)),
    }

    # Construim lista obiectelor cumparate pentru rendering in camera
    owned_items = room.get('items', {})
    room_objects = []
    for obj_key, obj_cfg in SHOP_ITEMS.get('obiecte', {}).items():
        if obj_key in owned_items:
            room_objects.append({
                'key':       obj_key,
                'file':      obj_cfg.get('file', ''),
                'url':       get_signed_url(f"{GITHUB_BASE}/room1/{obj_cfg.get('file', '')}"),
                'clickable': obj_cfg.get('clickable', False),
                'action':    obj_cfg.get('action'),
                'pos_x':     obj_cfg.get('pos_x', 50),
                'pos_y':     obj_cfg.get('pos_y', 50),
                'width':     obj_cfg.get('width', 15),
                'z_index':   obj_cfg.get('z_index', 5),
                'name':      obj_cfg.get('name', ''),
            })

    return render_template('petomania/acasa.html',
                           pet=pet,
                           room=room,
                           room_urls=room_urls,
                           room_objects=room_objects)

@app.route('/joc/petomania/menajerie')
@login_required
def menajerie():
    user     = get_current_user()
    uid      = int(user['id'])
    active   = sync_pet(uid)
    active_ctx = build_pet_context(active) if active else None
    rows     = get_menagerie(uid)
    men_pets = [build_pet_context(dict(r)) for r in rows]
    return render_template('petomania/menajerie.html',
                           active=active_ctx,
                           men_pets=men_pets)

@app.route('/joc/petomania/imbunatatiri')
@login_required
def imbunatatiri():
    user    = get_current_user()
    uid     = int(user['id'])
    room    = get_room_config(uid)
    dacoins = get_dacoins(uid)
    return render_template('petomania/imbunatatiri.html',
                           room=room,
                           dacoins=dacoins,
                           shop=ROOM_ITEMS)

# ─────────────────────────────────────────────
# API — actiuni ingrijire
# ─────────────────────────────────────────────

@app.route('/joc/petomania/api/action', methods=['POST'])
@login_required
def api_action():
    user   = get_current_user()
    uid    = int(user['id'])
    action = request.json.get('action')
    p      = sync_pet(uid)
    if not p:
        return jsonify({'ok': False, 'error': 'Nu ai un animal activ.'})
    now = int(time.time())
    msg = ''
    if action == 'feed':
        if p['hunger'] >= 100:
            return jsonify({'ok': False, 'error': 'Animalul nu e flămând!'})
        update_pet(uid, hunger=min(100, p['hunger'] + FEED_AMOUNT), last_action=now)
        msg = f"🍖 Ai hrănit {p['name']}!"
    elif action == 'wash':
        if p['cleanliness'] >= 100:
            return jsonify({'ok': False, 'error': 'Animalul e deja curat!'})
        update_pet(uid, cleanliness=min(100, p['cleanliness'] + WASH_AMOUNT), last_action=now)
        msg = f"🧼 Ai spălat {p['name']}!"
    elif action == 'play':
        state = get_state(p['hunger'], p['happiness'], p['cleanliness'], p['energy'], bool(p['sleeping']))
        if p['energy'] <= 30 or state == 'Hungry' or p['happiness'] >= 100:
            return jsonify({'ok': False, 'error': 'Nu poți juca acum!'})
        update_pet(uid,
            happiness=min(100, p['happiness'] + PLAY_HAPPINESS),
            energy=max(0, p['energy'] - PLAY_ENERGY_COST),
            hunger=max(0, p['hunger'] - PLAY_HUNGER_COST),
            last_action=now,
        )
        msg = f"🎮 Te-ai jucat cu {p['name']}!"
    elif action == 'sleep':
        state = get_state(p['hunger'], p['happiness'], p['cleanliness'], p['energy'], bool(p['sleeping']))
        if state == 'Dirty':
            return jsonify({'ok': False, 'error': 'Trebuie să-l speli înainte!'})
        if p['sleeping']:
            return jsonify({'ok': False, 'error': 'Doarme deja!'})
        update_pet(uid, sleeping=1, sleep_started=now, last_action=now, last_decay=now)
        msg = f"😴 {p['name']} doarme acum."
    elif action == 'wake':
        if not p['sleeping']:
            return jsonify({'ok': False, 'error': 'Nu doarme!'})
        if p['energy'] < 50:
            return jsonify({'ok': False, 'error': 'Are nevoie de cel puțin 50 energie!'})
        update_pet(uid, sleeping=0, sleep_started=None, last_action=now)
        msg = f"☀️ {p['name']} s-a trezit!"
    else:
        return jsonify({'ok': False, 'error': 'Acțiune necunoscută.'})
    p_new = sync_pet(uid)
    ctx   = build_pet_context(p_new)
    # Genera token nou pentru imaginea updatata
    raw_url = get_image_url(p_new['species'], get_form(p_new['level']),
                            get_state(p_new['hunger'], p_new['happiness'],
                                      p_new['cleanliness'], p_new['energy'],
                                      bool(p_new['sleeping'])), p_new['gender'])
    ctx['image_url'] = get_signed_url(raw_url)
    return jsonify({'ok': True, 'msg': msg, 'pet': ctx})

# ─────────────────────────────────────────────
# API — activeaza pet din menajerie
# ─────────────────────────────────────────────

@app.route('/joc/petomania/api/activa', methods=['POST'])
@login_required
def api_activa():
    user         = get_current_user()
    uid          = int(user['id'])
    menagerie_id = request.json.get('id')
    if not menagerie_id:
        return jsonify({'ok': False, 'error': 'ID lipsă.'})
    conn    = get_db()
    pet_men = conn.execute(
        'SELECT * FROM menagerie WHERE id = ? AND user_id = ?',
        (menagerie_id, uid)
    ).fetchone()
    if not pet_men:
        conn.close()
        return jsonify({'ok': False, 'error': 'Animal negăsit.'})
    active = conn.execute('SELECT * FROM pets WHERE user_id = ?', (uid,)).fetchone()
    if active:
        conn.execute('''
            INSERT INTO menagerie
            (user_id, name, gender, species, nature, level, xp, hunger, happiness,
             cleanliness, energy, sleeping, sleep_started, last_decay, last_xp_tick,
             born_at, stored_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            active['user_id'], active['name'], active['gender'], active['species'],
            active['nature'], active['level'], active['xp'], active['hunger'],
            active['happiness'], active['cleanliness'], active['energy'],
            active['sleeping'], active['sleep_started'], active['last_decay'],
            active['last_xp_tick'], active['born_at'], int(time.time())
        ))
        conn.execute('DELETE FROM pets WHERE user_id = ?', (uid,))
    now = int(time.time())
    conn.execute('''
        INSERT OR REPLACE INTO pets
        (user_id, name, gender, species, nature, level, xp, hunger, happiness,
         cleanliness, energy, sleeping, sleep_started, last_decay, last_action,
         last_xp_tick, born_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    ''', (
        uid, pet_men['name'], pet_men['gender'], pet_men['species'], pet_men['nature'],
        pet_men['level'], pet_men['xp'], pet_men['hunger'], pet_men['happiness'],
        pet_men['cleanliness'], pet_men['energy'], pet_men['sleeping'],
        pet_men['sleep_started'], now, now, pet_men['born_at']
    ))
    conn.execute('DELETE FROM menagerie WHERE id = ?', (menagerie_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'msg': f"{pet_men['name']} este acum activ!"})

# ─────────────────────────────────────────────
# API — cumpara imbunatatire
# ─────────────────────────────────────────────

@app.route('/joc/petomania/api/cumpara', methods=['POST'])
@login_required
def api_cumpara():
    user     = get_current_user()
    uid      = int(user['id'])
    category = request.json.get('category')  # 'wall', 'floor', 'chimney', 'obiecte'
    key      = request.json.get('key')

    if category not in SHOP_ITEMS:
        return jsonify({'ok': False, 'error': 'Categorie invalida.'})
    if key not in SHOP_ITEMS[category]:
        return jsonify({'ok': False, 'error': 'Item inexistent.'})

    item  = SHOP_ITEMS[category][key]
    price = item.get('price', 0)
    room  = get_room_config(uid)

    # ── OBIECTE — logica separata (stocate in room['items'] ca dict) ──
    if category == 'obiecte':
        owned_objects = room.get('items', {})
        if key in owned_objects:
            return jsonify({'ok': False, 'error': 'Ai deja acest obiect!'})
        if price > 0 and not spend_dacoins(uid, price):
            return jsonify({'ok': False, 'error': 'Dacoins insuficienti!'})
        owned_objects[key] = True
        save_room_config(uid, room['wall'], room['floor'], room['chimney'], owned_objects)
        return jsonify({
            'ok':          True,
            'msg':         f"✅ {item['name']} plasat în cameră!",
            'new_balance': get_dacoins(uid),
            'category':    category,
            'key':         key,
            'obj_data': {
                'file':      item.get('file', ''),
                'clickable': item.get('clickable', False),
                'action':    item.get('action'),
                'pos_x':     item.get('pos_x', 50),
                'pos_y':     item.get('pos_y', 50),
                'width':     item.get('width', 15),
                'z_index':   item.get('z_index', 5),
            },
        })

    # ── CAMERA (wall/floor/chimney) — logica originala ──
    if room[category] == key:
        return jsonify({'ok': False, 'error': 'Ai deja acest upgrade!'})

    requires = item.get('requires')
    if requires and room[category] != requires:
        return jsonify({'ok': False, 'error': 'Trebuie sa detii upgrade-ul anterior!'})

    if price > 0 and not spend_dacoins(uid, price):
        return jsonify({'ok': False, 'error': 'Dacoins insuficienti!'})

    room[category] = key
    save_room_config(uid, room['wall'], room['floor'], room['chimney'], room['items'])

    old_url = get_room_url(category, room[category], room)
    _invalidate_cache(old_url)
    new_raw_url = get_room_url(category, key, room)
    _invalidate_cache(new_raw_url)

    new_balance = get_dacoins(uid)
    new_url     = get_room_url(category, key)

    return jsonify({
        'ok':          True,
        'msg':         f"✅ {item['name']} aplicat!",
        'new_balance': new_balance,
        'new_url':     new_url,
        'category':    category,
    })

# ─────────────────────────────────────────────
# RENDER — compositing imagine pentru Discord embed
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# DISK CACHE — imagini camera cachete pe disk
# TTL: 5 minute. Invalidare automata la upgrade.
# ─────────────────────────────────────────────

CACHE_DIR = '/tmp/petomania_imgcache'
CACHE_TTL  = 300  # 5 minute

os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_key(url: str) -> str:
    """Genereaza un nume de fisier safe din URL."""
    import hashlib
    return hashlib.md5(url.encode()).hexdigest() + '.png'

def _cache_path(url: str) -> str:
    return os.path.join(CACHE_DIR, _cache_key(url))

def _invalidate_cache(url: str):
    """Sterge cache-ul pentru un URL specific."""
    path = _cache_path(url)
    if os.path.exists(path):
        os.remove(path)
        print(f"🗑️ Cache invalidat: {url}")

def _fetch_image(url: str):
    """Descarca o imagine de la URL si returneaza PIL Image."""
    try:
        from PIL import Image
        req = urllib.request.Request(url, headers={'User-Agent': 'PetomaniaBotRender/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert('RGBA')
    except Exception as e:
        print(f"⚠️ _fetch_image error {url}: {e}")
        return None

def _fetch_image_cached(url: str, ttl: int = CACHE_TTL, resize: tuple = (1280, 720)):
    """
    Descarca si cacheza o imagine pe disk.
    ttl:    durata cache in secunde
    resize: tuple (w, h) pentru resize inainte de salvare, sau None pentru a pastra originalul
    """
    from PIL import Image
    cache_file = _cache_path(url)
    now = time.time()

    if os.path.exists(cache_file):
        age = now - os.path.getmtime(cache_file)
        if age < ttl:
            try:
                return Image.open(cache_file).convert('RGBA')
            except Exception:
                pass

    img = _fetch_image(url)
    if img:
        if resize:
            img = img.resize(resize, Image.LANCZOS)
        try:
            img.save(cache_file, format='PNG')
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")
    return img

def _fetch_pet_cached(url: str):
    """
    Cacheza imaginea petului pe disk fara resize (60s TTL).
    Resize-ul se face dupa compozitare, per forma.
    """
    return _fetch_image_cached(url, ttl=60, resize=None)

@app.route('/joc/petomania/render/<int:user_id>')
def render_pet(user_id: int):
    """
    Genereaza in-memory o imagine PNG compozitata (camera + pet).
    Folosita de botul Discord in embed-ul /pet.
    Fara autentificare — accesibila public.
    """
    try:
        from PIL import Image
    except ImportError:
        return Response('Pillow not installed', status=500)

    # Dimensiune finala
    W, H = 1280, 720

    # Obtine config camera userului
    room = get_room_config(user_id)

    # Obtine petul
    pet_row = get_pet(user_id)
    if not pet_row:
        # Returneaza imagine goala cu camera daca nu are pet
        pet_row = None

    # Calculeaza state si form
    if pet_row:
        p       = dict(pet_row)
        form    = get_form(p['level'])
        state   = get_state(p['hunger'], p['happiness'], p['cleanliness'],
                            p['energy'], bool(p['sleeping']))
        gender  = p.get('gender', 'male')
        species = p['species']
        pet_url = get_image_url(species, form, state, gender)
    else:
        form    = 1
        pet_url = None

    # URL-uri layere camera (fara token — render intern)
    wall_url    = get_room_url('wall',    room['wall'],    room)
    floor_url   = get_room_url('floor',   room['floor'],   room)
    chimney_url = get_room_url('chimney', room['chimney'], room)

    # Canvas de baza
    canvas = Image.new('RGBA', (W, H), (10, 10, 16, 255))

    # Descarca toate imaginile in paralel
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_wall    = executor.submit(_fetch_image_cached, wall_url)
        f_floor   = executor.submit(_fetch_image_cached, floor_url)
        f_chimney = executor.submit(_fetch_image_cached, chimney_url)
        f_pet     = executor.submit(_fetch_pet_cached, pet_url) if pet_url else None

        wall_img    = f_wall.result()
        floor_img   = f_floor.result()
        chimney_img = f_chimney.result()
        pet_img     = f_pet.result() if f_pet else None

    # Layer 1: Perete
    if wall_img:
        canvas.paste(wall_img, (0, 0), wall_img)

    # Layer 2: Pardoseala
    if floor_img:
        canvas.paste(floor_img, (0, 0), floor_img)

    # Layer 3: Semineu
    if chimney_img:
        canvas.paste(chimney_img, (0, 0), chimney_img)

    # Layer 4: Pet — centrat jos, marime per forma
    if pet_img:
        pct = {1: 0.22, 2: 0.32, 3: 0.46}.get(form, 0.28)
        pet_w = int(W * pct)
        orig_w, orig_h = pet_img.size
        pet_h = int(pet_w * orig_h / orig_w)
        pet_img = pet_img.resize((pet_w, pet_h), Image.LANCZOS)
        x = (W - pet_w) // 2
        y = H - pet_h
        canvas.paste(pet_img, (x, y), pet_img)

    # Converteste la RGB si servi ca PNG
    output = io.BytesIO()
    canvas.convert('RGB').save(output, format='PNG', optimize=True)
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='image/png',
        headers={
            'Cache-Control': 'no-store, no-cache, must-revalidate',
            'Pragma':        'no-cache',
        }
    )

# ─────────────────────────────────────────────
# ORAS
# ─────────────────────────────────────────────

GITHUB_CITY = 'https://raw.githubusercontent.com/keserdark/village-bot/main/PetGame/static/city'

@app.route('/joc/petomania/oras')
@login_required
def oras():
    return render_template('petomania/oras.html',
        city_url     = get_signed_url(f"{GITHUB_CITY}/city.png"),
        castel_url   = get_signed_url(f"{GITHUB_CITY}/castel.png"),
        biserica_url = get_signed_url(f"{GITHUB_CITY}/biserica.png"),
        piata_url    = get_signed_url(f"{GITHUB_CITY}/piata.png"),
        aventura_url = get_signed_url(f"{GITHUB_CITY}/aventura.png"),
    )

@app.route('/joc/petomania/castel')
@login_required
def castel():
    return render_template('petomania/castel.html')

@app.route('/joc/petomania/biserica')
@login_required
def biserica():
    return render_template('petomania/biserica.html')

@app.route('/joc/petomania/piata')
@login_required
def piata():
    return render_template('petomania/piata.html')

@app.route('/joc/petomania/aventura')
@login_required
def aventura():
    return render_template('petomania/aventura.html')

@app.route('/joc/petomania/city/<filename>')
@login_required  
def city_img(filename):
    import urllib.request
    url = f"{GITHUB_CITY}/{filename}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Petomania/1.0'})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = resp.read()
    return Response(data, mimetype='image/png', headers={'Cache-Control': 'max-age=3600'})

GITHUB_PIATA = 'https://raw.githubusercontent.com/keserdark/village-bot/main/PetGame/static/piata'

@app.route('/joc/petomania/piata/<filename>')
@login_required
def piata_img(filename):
    import urllib.request
    url = f"{GITHUB_PIATA}/{filename}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Petomania/1.0'})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = resp.read()
    return Response(data, mimetype='image/png', headers={'Cache-Control': 'max-age=3600'})

GITHUB_ASSETS = 'https://raw.githubusercontent.com/keserdark/village-bot/main/PetGame/static/Assets'

@app.route('/joc/petomania/assets-img/<filename>')
@login_required
def assets_img(filename):
    import urllib.request
    url = f"{GITHUB_ASSETS}/{filename}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Petomania/1.0'})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = resp.read()
    return Response(data, mimetype='image/png', headers={'Cache-Control': 'max-age=3600'})

@app.route('/joc/petomania/assets')
@login_required
def assets():
    return render_template('petomania/assets.html')

def get_member_roles(user_id: int) -> list:
    """Fetch rolurile unui user din serverul Discord."""
    if not BOT_TOKEN or not GUILD_ID:
        return []
    try:
        url = f"{DISCORD_API}/guilds/{GUILD_ID}/members/{user_id}"
        resp = requests.get(url, headers={
            'Authorization': f'Bot {BOT_TOKEN}'
        }, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('roles', [])
    except Exception as e:
        print(f"⚠️ get_member_roles error: {e}")
    return []

def get_lady_interaction(user_id: int) -> dict:
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM lady_interactions WHERE user_id = ?', (user_id,)
    ).fetchone()
    conn.close()
    if row:
        return {
            'first_interaction': row['first_interaction'],
            'player_name':       row['player_name'],
            'has_companicon':    row['has_companicon'],
        }
    return {'first_interaction': 1, 'player_name': None, 'has_companicon': 0}

@app.route('/joc/petomania/api/lady', methods=['GET'])
@login_required
def api_lady():
    """Returneaza dialogul Lunarei in functie de rol si istoricul interactiunii."""
    user  = get_current_user()
    uid   = int(user['id'])
    uname = user['username']

    interaction = get_lady_interaction(uid)
    first       = interaction['first_interaction']
    saved_name  = interaction['player_name']

    roles = get_member_roles(uid)

    if not first:
        # A mai fost — dialog de revenire
        name = saved_name or uname
        dialog = {
            'variant':    'return',
            'text':       f'*Lunara Silvermist își ridică privirea dintr-o carte veche și îți zâmbește când te vede intrând pe ușa magazinului.*\nAh, {name}! Bine ai revenit la „Luna Argintie". Este o plăcere să te văd din nou în umilul meu magazin. Sper că drumul ți-a fost liniștit și că stelele ți-au fost favorabile de la ultima noastră întâlnire.\nSpune-mi, cu ce te pot ajuta astăzi?',
            'show_name_btn': False,
            'player_name': name,
        }
    else:
        # Prima interactiune — detecteaza rolul
        role_info = None
        for rid in ROLES_CHAMPION:
            if rid in roles:
                rdata = ROLE_NAMES.get(rid, ('Campion', '#ffd700'))
                role_info = {'id': rid, 'name': rdata[0], 'color': rdata[1], 'type': 'champion'}
                break
        if not role_info:
            for rid in ROLES_VETERAN:
                if rid in roles:
                    rdata = ROLE_NAMES.get(rid, ('Veteran', '#5865f2'))
                    role_info = {'id': rid, 'name': rdata[0], 'color': rdata[1], 'type': 'veteran'}
                    break
        if not role_info and ROLE_NEW in roles:
            role_info = {'id': ROLE_NEW, 'name': 'Nou Venit', 'color': '#ffffff', 'type': 'new'}

        if role_info and role_info['type'] == 'champion':
            rname = role_info['name']
            text = (
                f'*O femeie cu părul argintiu își ridică privirea dintre tomurile vechi și pare pregătită să te întâmpine ca pe un simplu călător. În clipa următoare, observă însemnele tale și face o reverență respectuoasă.*\n'
                f'Pe toate stelele ce veghează acest regat... te rog să-mi ierți neatenția. Pentru o clipă am crezut că am în față un nou venit, însă abia acum am observat titlul tău de {rname}.\n'
                f'Eu sunt Lunara Silvermist, păstrătoarea magazinului magic Luna Argintie. Faptele unui Campion răsună până și între aceste rafturi pline de artefacte și grimorii. Este o adevărată onoare să te primesc în pragul modestului meu magazin.\n'
                f'Dar spune-mi, sire... cum te numești?'
            )
            variant = 'champion'
        elif role_info and role_info['type'] == 'veteran':
            rname = role_info['name']
            text = (
                f'*O femeie cu părul argintiu își ridică privirea dintre tomurile vechi și pare pregătită să te întâmpine ca pe un nou venit. După o clipă, observă însemnele rangului tău și își înclină respectuos capul.*\n'
                f'Ah... îmi cer scuze. Pentru o clipă am crezut că ești nou în Regat, însă abia acum am observat rangul tău de {rname}. Se pare că am în fața mea un aventurier cu experiență și renume.\n'
                f'Eu sunt Lunara Silvermist, păstrătoarea magazinului magic Luna Argintie. Este o onoare să te întâlnesc.\n'
                f'Spune-mi, cum te numești?'
            )
            variant = 'veteran'
        else:
            text = '*O femeie cu părul argintiu își ridică privirea dintre tomurile vechi și îți oferă un zâmbet cald.*\nBine ai venit în Regat, călătorule. Eu sunt Lunara Silvermist, păstrătoarea magazinului magic „Luna Argintie". Nu cred că ne-am mai întâlnit până acum, așa că îți urez bun venit pe aceste meleaguri. Fie ca drumul tău să fie presărat cu aventuri, comori și povești vrednice de cronicile regatului.\nSpune-mi, cum te numești?'
            variant = 'new'
            role_info = {'color': '#ffffff'}

        dialog = {
            'variant':       variant,
            'text':          text,
            'show_name_btn': True,
            'username':      uname,
            'role_color':    role_info['color'] if role_info else '#ffffff',
        }

    return jsonify({'ok': True, 'dialog': dialog})

@app.route('/joc/petomania/api/lady/pet', methods=['GET'])
@login_required
def api_lady_pet():
    """Returneaza textul dialogului cu petul + codul petului."""
    user = get_current_user()
    uid  = int(user['id'])
    interaction = get_lady_interaction(uid)
    name = interaction['player_name'] or user['username']

    p = get_pet(uid)
    if p:
        form    = get_form(p['level'])
        petcode = f"{p['species'].upper()}-{str(form).zfill(3)}"
        text    = (
            f'*Lunara Silvermist își mută privirea către companionul care te însoțește și zâmbește ușor.*\n'
            f'Ah, văd că nu călătorești singur, {name}. Ai un companion alături de tine. '
            f'Dacă nu mă înșel, este un {petcode}, nu-i așa?\n'
            f'*Își apropie privirea cu interes, studiind creatura.*\n'
            f'O alegere interesantă. Se vede că între voi există o legătură puternică.'
        )
    else:
        petcode = '???'
        text    = (
            f'*Lunara Silvermist privește în jur cu curiozitate.*\n'
            f'Hmm, {name}... Nu văd niciun companion lângă tine. '
            f'Poate vei găsi unul curând pe aceste meleaguri.'
        )

    return jsonify({'ok': True, 'text': text})

@app.route('/joc/petomania/api/lady/companicon', methods=['POST'])
@login_required
def api_lady_companicon():
    """Marcheaza userul ca avand Companicon."""
    user = get_current_user()
    uid  = int(user['id'])
    conn = get_db()
    conn.execute('''
        INSERT INTO lady_interactions (user_id, first_interaction, has_companicon)
        VALUES (?, 0, 1)
        ON CONFLICT(user_id) DO UPDATE SET has_companicon = 1
    ''', (uid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/joc/petomania/api/lady/name', methods=['POST'])
@login_required
def api_lady_name():
    """Salveaza numele ales de user si marcheaza prima interactiune ca done."""
    user = get_current_user()
    uid  = int(user['id'])
    name = request.json.get('name', '').strip()[:50]
    if not name:
        return jsonify({'ok': False, 'error': 'Nume invalid.'})
    conn = get_db()
    conn.execute('''
        INSERT INTO lady_interactions (user_id, first_interaction, player_name)
        VALUES (?, 0, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            first_interaction = 0,
            player_name = excluded.player_name
    ''', (uid, name))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'name': name})

@app.route('/joc/petomania/consumable')
@login_required
def consumable():
    return render_template('petomania/consumable.html')


GITHUB_COMPANICON = 'https://raw.githubusercontent.com/keserdark/village-bot/main/PetGame/static'

@app.route('/joc/petomania/companicon-img/<path:filepath>')
@login_required
def companicon_img(filepath):
    import urllib.request
    url = f"{GITHUB_COMPANICON}/{filepath}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Petomania/1.0'})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = resp.read()
    return Response(data, mimetype='image/png', headers={'Cache-Control': 'max-age=3600'})

# Specii cu diferentiere de gen per forma
GENDERED_SPECIES = {
    'blackcat': [1, 2, 3],
    'dog':      [1, 2, 3],
    'duck':     [2, 3],
}

def _img_url(species, form, gender):
    if species in ('blackcat', 'dog'):
        suffix = 'Male' if gender == 'male' else 'Female'
        return f"/joc/petomania/companicon-img/00transparent/{species}/Stage{form}-Basic-Form-{suffix}.png"
    elif species == 'duck' and form > 1:
        suffix = 'Male' if gender == 'male' else 'Female'
        return f"/joc/petomania/companicon-img/00transparent/{species}/Stage{form}-Basic-Form-{suffix}.png"
    else:
        return f"/joc/petomania/companicon-img/00transparent/{species}/Stage{form}-Basic-Form.png"

def sync_companicon_discovered(user_id: int):
    conn = get_db()
    try:
        conn.execute('ALTER TABLE companicon_discovered ADD COLUMN gender TEXT NOT NULL DEFAULT "male"')
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_comp_disc ON companicon_discovered(user_id, species, form, gender)')
        conn.commit()
    except Exception:
        pass

    def insert(species, form, gender):
        conn.execute(
            'INSERT OR IGNORE INTO companicon_discovered (user_id, species, form, gender) VALUES (?,?,?,?)',
            (user_id, species, form, gender)
        )

    pet = conn.execute('SELECT species, level, gender FROM pets WHERE user_id = ?', (user_id,)).fetchone()
    if pet:
        for f in range(1, get_form(pet['level']) + 1):
            insert(pet['species'], f, pet['gender'])

    rows = conn.execute('SELECT species, level, gender FROM menagerie WHERE user_id = ?', (user_id,)).fetchall()
    for row in rows:
        for f in range(1, get_form(row['level']) + 1):
            insert(row['species'], f, row['gender'])

    conn.commit()
    conn.close()

def get_discovered(user_id: int) -> set:
    conn = get_db()
    rows = conn.execute(
        'SELECT species, form, gender FROM companicon_discovered WHERE user_id = ?', (user_id,)
    ).fetchall()
    conn.close()
    return {(r['species'], r['form'], r['gender']) for r in rows}

@app.route('/joc/petomania/api/companicon')
@login_required
def api_companicon():
    user = get_current_user()
    uid  = int(user['id'])
    sync_companicon_discovered(uid)
    discovered = get_discovered(uid)
    entries = []
    for species_key, species_data in SPECIES.items():
        species_entries = species_data.get('entries', {})
        nature_key = species_data.get('available_natures', [None])[0]
        nat_data   = NATURES.get(nature_key, {}) if nature_key else {}
        gendered_forms = GENDERED_SPECIES.get(species_key, [])

        for form, entry_data in species_entries.items():
            has_gender = form in gendered_forms
            if has_gender:
                male_disc   = (species_key, form, 'male')   in discovered
                female_disc = (species_key, form, 'female') in discovered
                is_discovered = male_disc or female_disc
            else:
                is_discovered = (species_key, form, 'male') in discovered or (species_key, form, 'female') in discovered
                male_disc = female_disc = is_discovered

            entries.append({
                'species':           species_key,
                'species_name':      species_data['name'],
                'form':              form,
                'code':              entry_data['code'],
                'name':              entry_data['name'],
                'description':       entry_data['description'],
                'lore':              entry_data.get('lore', ''),
                'discovered':        is_discovered,
                'has_gender':        has_gender,
                'male_discovered':   male_disc,
                'female_discovered': female_disc,
                'img_url_male':      _img_url(species_key, form, 'male'),
                'img_url_female':    _img_url(species_key, form, 'female') if has_gender else None,
                'nature_name':       nat_data.get('name', ''),
                'nature_icon':       nat_data.get('icon', ''),
                'nature_color':      nat_data.get('color', '#ffffff'),
            })
    return jsonify({'ok': True, 'entries': entries})

@app.route('/joc/petomania/companicon')
@login_required
def companicon():
    return render_template('petomania/companicon.html')




# ─────────────────────────────────────────────
# RUCSAC
# ─────────────────────────────────────────────

@app.route('/joc/petomania/api/rucsac/data')
@login_required
def api_rucsac_data():
    """Returneaza datele complete ale rucsacului ca JSON — apelat la fiecare deschidere a panelului."""
    user = get_current_user()
    uid  = int(user['id'])

    sync_pet(uid)
    sync_pet_hp(uid)

    pet     = get_pet(uid)
    pet_ctx = build_pet_context(pet) if pet else None
    categories = inv_build_context(uid)

    companions = [None, None, None, None, None]

    # Slot 1 — pet activ
    if pet_ctx and pet:
        p      = dict(pet)
        hp_max = pet_ctx['stats']['hp']
        hp_cur = p['hp_current'] if p['hp_current'] > 0 else hp_max
        companions[0] = {
            'name':        pet_ctx['name'],
            'species':     pet_ctx['species_name'],
            'level':       pet_ctx['level'],
            'form':        pet_ctx['form'],
            'nature':      pet_ctx['nat_data']['name']  if pet_ctx['nat_data'] else None,
            'nature_icon': pet_ctx['nat_data']['icon']  if pet_ctx['nat_data'] else None,
            'gender_icon': pet_ctx['gender_icon'],
            'species_key': p['species'],
            'hp_current':  hp_cur,
            'hp_max':      hp_max,
            'active':      True,
            'image_url':   pet_ctx['image_url'],
        }

    # Sloturile 2-5 — din loadout
    loadout = get_loadout(uid)
    conn = get_db()
    for i, slot_key in enumerate(['slot_2', 'slot_3', 'slot_4', 'slot_5'], start=1):
        men_id = loadout[slot_key]
        if men_id:
            row = conn.execute(
                'SELECT * FROM menagerie WHERE id = ? AND user_id = ?', (men_id, uid)
            ).fetchone()
            if row:
                mp       = dict(row)
                mform    = get_form(mp['level'])
                mstate   = get_state(mp['hunger'], mp['happiness'], mp['cleanliness'],
                                     mp['energy'], bool(mp['sleeping']))
                mnat     = NATURES.get(mp.get('nature')) if mp.get('nature') else None
                mhp_max  = get_stats_at_level(mp['species'], mp.get('nature'), mp['level'], mform)['hp']
                mhp_cur  = mp['hp_current'] if mp['hp_current'] > 0 else mhp_max
                companions[i] = {
                    'name':        mp['name'],
                    'species':     SPECIES.get(mp['species'], {}).get('name', mp['species']),
                    'level':       mp['level'],
                    'form':        mform,
                    'nature':      mnat['name']  if mnat else None,
                    'nature_icon': mnat['icon']  if mnat else None,
                    'gender_icon': '♂️' if mp['gender'] == 'male' else '♀️',
                    'species_key': mp['species'],
                    'hp_current':  mhp_cur,
                    'hp_max':      mhp_max,
                    'active':      False,
                    'image_url':   get_image_url(mp['species'], mform, mstate, mp['gender']),
                }
    conn.close()

    return jsonify({
        'ok':         True,
        'categories': categories,
        'companions': companions,
        'dacoins':    get_dacoins(uid),
    })


@app.route('/joc/petomania/api/rucsac/use', methods=['POST'])
@login_required
def api_rucsac_use():
    user     = get_current_user()
    uid      = int(user['id'])
    data     = request.json or {}
    category = data.get('category', '')
    item_key = data.get('item_key', '')
    if not category or not item_key:
        return jsonify({'ok': False, 'msg': 'Date lipsă.'})
    return jsonify(use_item(uid, category, item_key))


@app.route('/joc/petomania/api/rucsac/drop', methods=['POST'])
@login_required
def api_rucsac_drop():
    user     = get_current_user()
    uid      = int(user['id'])
    data     = request.json or {}
    category = data.get('category', '')
    item_key = data.get('item_key', '')
    qty      = int(data.get('qty', 1))
    if not category or not item_key:
        return jsonify({'ok': False, 'msg': 'Date lipsă.'})
    item_cfg = inv_get_item(category, item_key)
    if item_cfg and item_cfg.get('quest_item'):
        return jsonify({'ok': False, 'msg': 'Quest item-urile nu pot fi aruncate.'})
    return jsonify(inv_remove(uid, category, item_key, qty))


@app.route('/joc/petomania/api/rucsac/rename', methods=['POST'])
@login_required
def api_rucsac_rename():
    user     = get_current_user()
    uid      = int(user['id'])
    new_name = (request.json or {}).get('name', '').strip()
    return jsonify(rename_pet(uid, new_name))


@app.route('/joc/petomania/api/rucsac/comp_stats', methods=['GET'])
@login_required
def api_rucsac_comp_stats():
    """Stats complete ale petului activ pentru popup-ul din rucsac."""
    user = get_current_user()
    uid  = int(user['id'])
    pet  = get_pet(uid)
    if not pet:
        return jsonify({'ok': False, 'msg': 'Niciun companion activ.'})

    p        = dict(pet)
    form     = get_form(p['level'])
    nature   = p.get('nature')
    stats    = get_stats_at_level(p['species'], nature, p['level'], form)
    nat_data = NATURES.get(nature) if nature else None

    hp_max = stats['hp']
    hp_cur = p['hp_current'] if p['hp_current'] > 0 else hp_max

    return jsonify({
        'ok':          True,
        'name':        p['name'],
        'species':     SPECIES.get(p['species'], {}).get('name', p['species']),
        'species_key': p['species'],
        'level':       p['level'],
        'form':        form,
        'gender_icon': '♂️' if p['gender'] == 'male' else '♀️',
        'nature':      nat_data['name']  if nat_data else None,
        'nature_icon': nat_data['icon']  if nat_data else None,
        'nature_color': nat_data['color'] if nat_data else None,
        'bonus_stat':  nat_data['bonus_stat'] if nat_data else None,
        'hp_current':  hp_cur,
        'hp_max':      hp_max,
        'stats': {
            'hp':         stats['hp'],
            'attack':     stats['attack'],
            'defense':    stats['defense'],
            'speed':      stats['speed'],
            'evasion':    stats['evasion'],
            'healing':    stats['healing'],
            'control':    stats['control'],
            'reflection': stats['reflection'],
        }
    })



# ─────────────────────────────────────────────
# LOADOUT
# ─────────────────────────────────────────────

NEXUS_BASE = f"{GITHUB_BASE}/items"

def get_loadout(user_id: int) -> dict:
    """Returneaza loadout-ul unui user. Slot 1 = pet activ mereu."""
    conn = get_db()
    row  = conn.execute('SELECT * FROM loadout WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    if row:
        return {'slot_2': row['slot_2'], 'slot_3': row['slot_3'],
                'slot_4': row['slot_4'], 'slot_5': row['slot_5']}
    return {'slot_2': None, 'slot_3': None, 'slot_4': None, 'slot_5': None}

def save_loadout(user_id: int, slot_2=None, slot_3=None, slot_4=None, slot_5=None):
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO loadout (user_id, slot_2, slot_3, slot_4, slot_5)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, slot_2, slot_3, slot_4, slot_5))
    conn.commit()
    conn.close()

def build_loadout_slot(pet_row, slot_num: int) -> dict:
    """Construieste contextul unui slot pentru template."""
    if not pet_row:
        return {'empty': True, 'slot': slot_num}
    p        = dict(pet_row)
    form     = get_form(p['level'])
    state    = get_state(p['hunger'], p['happiness'], p['cleanliness'],
                         p['energy'], bool(p['sleeping']))
    nat_data = NATURES.get(p.get('nature')) if p.get('nature') else None
    return {
        'empty':       False,
        'slot':        slot_num,
        'id':          p.get('id'),           # None pentru slot 1 (pets table)
        'name':        p['name'],
        'species':     SPECIES.get(p['species'], {}).get('name', p['species']),
        'species_key': p['species'],
        'level':       p['level'],
        'form':        form,
        'gender':      p['gender'],
        'gender_icon': '♂️' if p['gender'] == 'male' else '♀️',
        'image_url':   get_image_url(p['species'], form, state, p['gender']),
        'nat_data':    nat_data,
        'hp_current':  p.get('hp_current', 0),
        'hp_max':      get_stats_at_level(p['species'], p.get('nature'), p['level'], form)['hp'],
    }

def build_loadout_context(user_id: int) -> list:
    """Construieste lista de 5 sloturi pentru template."""
    loadout = get_loadout(user_id)
    conn    = get_db()

    # Slot 1 — pet activ
    pet_row = conn.execute('SELECT * FROM pets WHERE user_id = ?', (user_id,)).fetchone()
    slots   = [build_loadout_slot(pet_row, 1)]

    # Sloturile 2-5 — menajerie
    for i, slot_key in enumerate(['slot_2', 'slot_3', 'slot_4', 'slot_5'], start=2):
        men_id = loadout[slot_key]
        if men_id:
            row = conn.execute('SELECT * FROM menagerie WHERE id = ? AND user_id = ?',
                               (men_id, user_id)).fetchone()
            slots.append(build_loadout_slot(row, i))
        else:
            slots.append({'empty': True, 'slot': i})

    conn.close()
    return slots

def build_menagerie_for_loadout(user_id: int, exclude_ids: list) -> list:
    """Lista petilor din menajerie disponibili pentru loadout (exclus cei deja in sloturi)."""
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM menagerie WHERE user_id = ? ORDER BY level DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        if row['id'] in exclude_ids:
            continue
        p        = dict(row)
        form     = get_form(p['level'])
        state    = get_state(p['hunger'], p['happiness'], p['cleanliness'],
                             p['energy'], bool(p['sleeping']))
        nat_data = NATURES.get(p.get('nature')) if p.get('nature') else None
        result.append({
            'id':          p['id'],
            'name':        p['name'],
            'species':     SPECIES.get(p['species'], {}).get('name', p['species']),
            'species_key': p['species'],
            'level':       p['level'],
            'form':        form,
            'gender_icon': '♂️' if p['gender'] == 'male' else '♀️',
            'image_url':   get_image_url(p['species'], form, state, p['gender']),
            'nat_data':    nat_data,
        })
    return result


@app.route('/joc/petomania/loadout')
@login_required
def loadout():
    user = get_current_user()
    uid  = int(user['id'])
    sync_pet(uid)
    sync_pet_hp(uid)

    slots        = build_loadout_context(uid)
    loadout_data = get_loadout(uid)
    exclude_ids  = [v for v in loadout_data.values() if v]
    menagerie    = build_menagerie_for_loadout(uid, exclude_ids)

    return render_template(
        'petomania/loadout.html',
        slots=slots,
        menagerie=menagerie,
        nexus_inferior=f"{NEXUS_BASE}/NexusInferior.png",
        nexus_superior=f"{NEXUS_BASE}/NexusSuperior.png",
    )


@app.route('/joc/petomania/api/loadout/set', methods=['POST'])
@login_required
def api_loadout_set():
    """Seteaza un pet intr-un slot din loadout."""
    user     = get_current_user()
    uid      = int(user['id'])
    data     = request.json or {}
    slot     = int(data.get('slot', 0))
    men_id   = data.get('men_id')  # None = goleste slotul

    if slot < 2 or slot > 5:
        return jsonify({'ok': False, 'error': 'Slot invalid. Slot 1 este mereu pet-ul activ.'})

    # Verifica ca men_id apartine userului
    if men_id:
        conn = get_db()
        row  = conn.execute(
            'SELECT id FROM menagerie WHERE id = ? AND user_id = ?', (men_id, uid)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({'ok': False, 'error': 'Companion negăsit.'})

    # Verifica sa nu fie deja in alt slot
    current = get_loadout(uid)
    for k, v in current.items():
        if v == men_id and men_id is not None:
            # Scoate-l din slotul vechi
            current[k] = None

    current[f'slot_{slot}'] = men_id
    save_loadout(uid, current['slot_2'], current['slot_3'],
                 current['slot_4'], current['slot_5'])

    # Returneaza contextul nou al slotului
    conn = get_db()
    row  = conn.execute('SELECT * FROM menagerie WHERE id = ?', (men_id,)).fetchone() if men_id else None
    conn.close()
    slot_ctx = build_loadout_slot(row, slot)

    return jsonify({'ok': True, 'slot': slot_ctx})


@app.route('/joc/petomania/api/loadout/clear', methods=['POST'])
@login_required
def api_loadout_clear():
    """Goleste un slot din loadout."""
    user = get_current_user()
    uid  = int(user['id'])
    slot = int((request.json or {}).get('slot', 0))

    if slot < 2 or slot > 5:
        return jsonify({'ok': False, 'error': 'Slot invalid.'})

    current = get_loadout(uid)
    current[f'slot_{slot}'] = None
    save_loadout(uid, current['slot_2'], current['slot_3'],
                 current['slot_4'], current['slot_5'])
    return jsonify({'ok': True})

# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=False)
