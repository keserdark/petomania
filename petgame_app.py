"""
Regnum Dacorum — Petomania Web
================================
Flask app independent pe portul 5002.
OAuth Discord propriu — redirect URI: https://regnum-dacorum.ro/joc/petomania/callback

Rulare:
    python3 petgame_app.py

In productie:
    screen -dmS petomania python3 petgame_app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import secrets
import requests
import time
import io
import threading
import urllib.request
import concurrent.futures
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, abort, Response
)
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# ── MODULES ──────────────────────────────────────────────────────────
from modules.db       import get_db, init_db, get_dacoins, spend_dacoins, get_room_config, save_room_config, bump_room_version
from modules.pets     import (get_pet, get_menagerie, get_form, get_state, get_image_url,
                               get_room_url, sync_pet, sync_pet_hp, sync_menagerie_hp, update_pet, build_pet_context,
                               format_age, xp_for_level,
                               DECAY_INTERVAL, FEED_AMOUNT, WASH_AMOUNT,
                               PLAY_HAPPINESS, PLAY_ENERGY_COST, PLAY_HUNGER_COST)
from modules.inventory    import (inv_build_context, inv_add, inv_remove, use_item, rename_pet)
from modules.loadout      import (get_loadout, save_loadout, build_loadout_slot,
                                   build_loadout_context, build_menagerie_for_loadout)
from modules.companicon   import build_companicon_entries, _img_url as companicon_img_url
from modules.discord_helpers import (get_member_roles, get_lady_interaction,
                                      build_lady_dialog, build_lady_pet_text)
from inventory_config     import get_item as inv_get_item
from shop_config          import get_shop
from modules.shop         import build_shop_context, shop_buy
from petgame_room_config  import ROOM_ITEMS
from cogs.petgame_config  import SPECIES
from cogs.petgame_natures import NATURES
from cogs.petgame_stats   import get_stats_at_level

# ── FLASK APP ─────────────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv('PETOMANIA_SECRET_KEY', secrets.token_hex(32))

# ── CONFIG ────────────────────────────────────────────────────────────

DISCORD_CLIENT_ID     = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_API           = 'https://discord.com/api/v10'
DISCORD_OAUTH_AUTHORIZE = 'https://discord.com/oauth2/authorize'
DISCORD_OAUTH_TOKEN     = f'{DISCORD_API}/oauth2/token'
REDIRECT_URI = os.getenv('PETOMANIA_REDIRECT_URI', 'http://204.168.179.80:5002/joc/petomania/callback')

STATIC_BASE = '/static'

SHOP_ITEMS = {cat: {item['key']: item for item in items} for cat, items in ROOM_ITEMS.items()}

# ── TOKEN STORE (signed image URLs) ──────────────────────────────────

def get_static_url(path: str) -> str:
    """Converteste un path relativ la static URL direct."""
    # path poate fi 'room1/Wall1.png' sau 'static/room1/Wall1.png'
    if path.startswith('http'):
        # E un URL GitHub vechi — extragem calea relativa
        for prefix in [
            'https://raw.githubusercontent.com/keserdark/petomania/main/static/',
            'https://raw.githubusercontent.com/keserdark/village-bot/main/PetGame/static/',
        ]:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break
    if path.startswith('/static/'):
        return path
    return f'/static/{path}'


# Patch build_pet_context to use our get_static_url
def _build_pet_context(p):
    return build_pet_context(p, get_static_url)


# ── DISK CACHE (PIL render) ───────────────────────────────────────────

CACHE_DIR = '/tmp/petomania_imgcache'
CACHE_TTL  = 300
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(url: str) -> str:
    import hashlib
    return hashlib.md5(url.encode()).hexdigest() + '.png'


def _cache_path(url: str) -> str:
    return os.path.join(CACHE_DIR, _cache_key(url))


def _invalidate_cache(url: str):
    path = _cache_path(url)
    if os.path.exists(path):
        os.remove(path)


def _fetch_image(url: str):
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
        except Exception:
            pass
    return img


def _fetch_pet_cached(url: str):
    return _fetch_image_cached(url, ttl=60, resize=None)


# ── AUTH ──────────────────────────────────────────────────────────────

def get_current_user():
    if 'user_id' not in session:
        return None
    return {'id': session['user_id'], 'username': session.get('username', ''), 'avatar': session.get('avatar')}


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


@app.context_processor
def inject_globals():
    user = get_current_user()
    if user:
        from datetime import datetime
        user['avatar_url']     = avatar_url(user['id'], user['avatar'])
        user['dacoins']        = get_dacoins(int(user['id']))
        interaction            = get_lady_interaction(int(user['id']))
        user['has_companicon'] = interaction['has_companicon']
    from datetime import datetime
    return {'current_user': user, 'now': datetime.now()}


# ── OAUTH ─────────────────────────────────────────────────────────────

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
        return render_template('error.html', error="State OAuth invalid.")
    code = request.args.get('code')
    if not code:
        return render_template('error.html', error="Nu am primit codul OAuth.")
    try:
        token_resp = requests.post(
            DISCORD_OAUTH_TOKEN,
            data={'client_id': DISCORD_CLIENT_ID, 'client_secret': DISCORD_CLIENT_SECRET,
                  'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10,
        )
    except requests.RequestException as e:
        return render_template('error.html', error=f"Eroare conexiune Discord: {e}")
    if token_resp.status_code != 200:
        return render_template('error.html', error="Discord a respins codul OAuth.")
    access_token = token_resp.json()['access_token']
    try:
        user_resp = requests.get(f"{DISCORD_API}/users/@me",
                                  headers={'Authorization': f"Bearer {access_token}"}, timeout=10)
        user_resp.raise_for_status()
    except requests.RequestException:
        return render_template('error.html', error="Nu am putut prelua datele tale Discord.")
    user_data           = user_resp.json()
    session['user_id']  = user_data['id']
    session['username'] = user_data.get('global_name') or user_data['username']
    session['avatar']   = user_data.get('avatar')
    uid = int(user_data['id'])
    get_dacoins(uid)
    get_room_config(uid)
    return redirect(session.pop('next_url', url_for('acasa')))


@app.route('/joc/petomania/logout')
def logout():
    session.clear()
    return redirect(url_for('acasa'))


# serve_img nu mai e necesar — imaginile sunt servite direct din static/


# ── PAGINI ────────────────────────────────────────────────────────────

@app.route('/joc/petomania/')
@app.route('/joc/petomania')
@login_required
def acasa():
    user = get_current_user()
    uid  = int(user['id'])
    p    = sync_pet(uid)
    pet  = _build_pet_context(p) if p else None
    room = get_room_config(uid)

    v = room.get('room_version', 1)
    room_urls = {
        'wall':    get_static_url(get_room_url('wall',    room['wall'],    room)) + f'?v={v}',
        'floor':   get_static_url(get_room_url('floor',   room['floor'],   room)) + f'?v={v}',
        'chimney': get_static_url(get_room_url('chimney', room['chimney'], room)) + f'?v={v}',
    }
    owned_items  = room.get('items', {})
    room_objects = []
    for obj_key, obj_cfg in SHOP_ITEMS.get('obiecte', {}).items():
        if obj_key in owned_items:
            room_objects.append({
                'key':       obj_key,
                'file':      obj_cfg.get('file', ''),
                'url':       get_static_url(f"room1/{obj_cfg.get('file', '')}"),
                'clickable': obj_cfg.get('clickable', False),
                'action':    obj_cfg.get('action'),
                'pos_x':     obj_cfg.get('pos_x', 50),
                'pos_y':     obj_cfg.get('pos_y', 50),
                'width':     obj_cfg.get('width', 15),
                'z_index':   obj_cfg.get('z_index', 5),
                'name':      obj_cfg.get('name', ''),
            })
    return render_template('acasa.html', pet=pet, room=room, room_urls=room_urls, room_objects=room_objects)


@app.route('/joc/petomania/menajerie')
@login_required
def menajerie():
    user       = get_current_user()
    uid        = int(user['id'])
    active     = sync_pet(uid)
    active_ctx = _build_pet_context(active) if active else None
    rows          = get_menagerie(uid)
    men_pets      = [_build_pet_context(dict(r)) for r in rows]
    loadout_slots = build_loadout_context(uid)
    return render_template('menajerie.html', active=active_ctx, men_pets=men_pets, loadout_slots=loadout_slots)


@app.route('/joc/petomania/imbunatatiri')
@login_required
def imbunatatiri():
    user    = get_current_user()
    uid     = int(user['id'])
    room    = get_room_config(uid)
    dacoins = get_dacoins(uid)
    return render_template('imbunatatiri.html', room=room, dacoins=dacoins, shop=ROOM_ITEMS)


# ── API — INGRIJIRE ───────────────────────────────────────────────────

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
            last_action=now)
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
    ctx   = _build_pet_context(p_new)
    raw_url = get_image_url(p_new['species'], get_form(p_new['level']),
                             get_state(p_new['hunger'], p_new['happiness'],
                                       p_new['cleanliness'], p_new['energy'],
                                       bool(p_new['sleeping'])), p_new['gender'])
    ctx['image_url'] = get_static_url(raw_url)
    return jsonify({'ok': True, 'msg': msg, 'pet': ctx})


@app.route('/joc/petomania/api/activa', methods=['POST'])
@login_required
def api_activa():
    user         = get_current_user()
    uid          = int(user['id'])
    menagerie_id = request.json.get('id')
    if not menagerie_id:
        return jsonify({'ok': False, 'error': 'ID lipsă.'})
    conn    = get_db()
    pet_men = conn.execute('SELECT * FROM menagerie WHERE id = ? AND user_id = ?', (menagerie_id, uid)).fetchone()
    if not pet_men:
        conn.close()
        return jsonify({'ok': False, 'error': 'Animal negăsit.'})
    active = conn.execute('SELECT * FROM pets WHERE user_id = ?', (uid,)).fetchone()
    now = int(time.time())
    if active:
        conn.execute('''
            INSERT INTO menagerie
            (user_id, name, gender, species, nature, level, xp, hunger, happiness,
             cleanliness, energy, sleeping, sleep_started, last_decay, last_xp_tick, born_at, stored_at, hp_current)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (active['user_id'], active['name'], active['gender'], active['species'],
              active['nature'], active['level'], active['xp'], active['hunger'],
              active['happiness'], active['cleanliness'], active['energy'],
              active['sleeping'], active['sleep_started'], active['last_decay'],
              active['last_xp_tick'], active['born_at'], now, active.get('hp_current', 0)))
        conn.execute('DELETE FROM pets WHERE user_id = ?', (uid,))
    conn.execute('''
        INSERT OR REPLACE INTO pets
        (user_id, name, gender, species, nature, level, xp, hunger, happiness,
         cleanliness, energy, sleeping, sleep_started, last_decay, last_action, last_xp_tick, born_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    ''', (uid, pet_men['name'], pet_men['gender'], pet_men['species'], pet_men['nature'],
          pet_men['level'], pet_men['xp'], pet_men['hunger'], pet_men['happiness'],
          pet_men['cleanliness'], pet_men['energy'], pet_men['sleeping'],
          pet_men['sleep_started'], now, now, pet_men['born_at']))
    conn.execute('DELETE FROM menagerie WHERE id = ?', (menagerie_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'msg': f"{pet_men['name']} este acum activ!"})


@app.route('/joc/petomania/api/cumpara', methods=['POST'])
@login_required
def api_cumpara():
    user     = get_current_user()
    uid      = int(user['id'])
    category = request.json.get('category')
    key      = request.json.get('key')

    if category not in SHOP_ITEMS:
        return jsonify({'ok': False, 'error': 'Categorie invalida.'})
    if key not in SHOP_ITEMS[category]:
        return jsonify({'ok': False, 'error': 'Item inexistent.'})

    item  = SHOP_ITEMS[category][key]
    price = item.get('price', 0)
    room  = get_room_config(uid)

    if category == 'obiecte':
        owned_objects = room.get('items', {})
        if key in owned_objects:
            return jsonify({'ok': False, 'error': 'Ai deja acest obiect!'})
        if price > 0 and not spend_dacoins(uid, price):
            return jsonify({'ok': False, 'error': 'Dacoins insuficienti!'})
        owned_objects[key] = True
        save_room_config(uid, room['wall'], room['floor'], room['chimney'], owned_objects)
        bump_room_version(uid)
        return jsonify({
            'ok': True, 'msg': f"✅ {item['name']} plasat în cameră!",
            'new_balance': get_dacoins(uid), 'category': category, 'key': key,
            'obj_data': {
                'file': item.get('file', ''), 'clickable': item.get('clickable', False),
                'action': item.get('action'), 'pos_x': item.get('pos_x', 50),
                'pos_y': item.get('pos_y', 50), 'width': item.get('width', 15),
                'z_index': item.get('z_index', 5),
            },
        })

    if room[category] == key:
        return jsonify({'ok': False, 'error': 'Ai deja acest upgrade!'})
    requires = item.get('requires')
    if requires and room[category] != requires:
        return jsonify({'ok': False, 'error': 'Trebuie sa detii upgrade-ul anterior!'})
    if price > 0 and not spend_dacoins(uid, price):
        return jsonify({'ok': False, 'error': 'Dacoins insuficienti!'})

    room[category] = key
    save_room_config(uid, room['wall'], room['floor'], room['chimney'], room['items'])
    bump_room_version(uid)
    _invalidate_cache(get_room_url(category, room[category], room))
    _invalidate_cache(get_room_url(category, key, room))

    return jsonify({
        'ok': True, 'msg': f"✅ {item['name']} aplicat!",
        'new_balance': get_dacoins(uid), 'new_url': get_room_url(category, key), 'category': category,
    })


# ── RENDER PIL ────────────────────────────────────────────────────────

@app.route('/joc/petomania/render/<int:user_id>')
def render_pet(user_id: int):
    try:
        from PIL import Image
    except ImportError:
        return Response('Pillow not installed', status=500)
    W, H = 1280, 720
    room    = get_room_config(user_id)
    pet_row = get_pet(user_id)
    if pet_row:
        p       = dict(pet_row)
        form    = get_form(p['level'])
        state   = get_state(p['hunger'], p['happiness'], p['cleanliness'], p['energy'], bool(p['sleeping']))
        pet_url = get_image_url(p['species'], form, state, p.get('gender', 'male'))
    else:
        form    = 1
        pet_url = None
    wall_url    = get_room_url('wall',    room['wall'],    room)
    floor_url   = get_room_url('floor',   room['floor'],   room)
    chimney_url = get_room_url('chimney', room['chimney'], room)
    canvas = Image.new('RGBA', (W, H), (10, 10, 16, 255))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_wall    = executor.submit(_fetch_image_cached, wall_url)
        f_floor   = executor.submit(_fetch_image_cached, floor_url)
        f_chimney = executor.submit(_fetch_image_cached, chimney_url)
        f_pet     = executor.submit(_fetch_pet_cached, pet_url) if pet_url else None
        wall_img    = f_wall.result()
        floor_img   = f_floor.result()
        chimney_img = f_chimney.result()
        pet_img     = f_pet.result() if f_pet else None
    for img in [wall_img, floor_img, chimney_img]:
        if img:
            canvas.paste(img, (0, 0), img)
    if pet_img:
        pct   = {1: 0.22, 2: 0.32, 3: 0.46}.get(form, 0.28)
        pet_w = int(W * pct)
        pet_h = int(pet_w * pet_img.size[1] / pet_img.size[0])
        pet_img = pet_img.resize((pet_w, pet_h), Image.LANCZOS)
        canvas.paste(pet_img, ((W - pet_w) // 2, H - pet_h), pet_img)
    output = io.BytesIO()
    canvas.convert('RGB').save(output, format='PNG', optimize=True)
    output.seek(0)
    return Response(output.getvalue(), mimetype='image/png',
                    headers={'Cache-Control': 'no-store, no-cache, must-revalidate', 'Pragma': 'no-cache'})


# ── ORAS ──────────────────────────────────────────────────────────────

@app.route('/joc/petomania/oras')
@login_required
def oras():
    return render_template('oras.html',
        city_url     = f"{STATIC_BASE}/city/city.png",
        castel_url   = f"{STATIC_BASE}/city/castel.png",
        biserica_url = f"{STATIC_BASE}/city/biserica.png",
        piata_url    = f"{STATIC_BASE}/city/piata.png",
        aventura_url = f"{STATIC_BASE}/city/aventura.png",
    )


@app.route('/joc/petomania/castel')
@login_required
def castel():
    return render_template('castel.html')


@app.route('/joc/petomania/biserica')
@login_required
def biserica():
    return render_template('biserica.html')


@app.route('/joc/petomania/piata')
@login_required
def piata():
    return render_template('piata.html')


@app.route('/joc/petomania/aventura')
@login_required
def aventura():
    return render_template('aventura.html')


# city_img nu mai e necesar — fisierele sunt in static/city/


# piata_img nu mai e necesar — fisierele sunt in static/piata/


# assets_img nu mai e necesar — fisierele sunt in static/Assets/


@app.route('/joc/petomania/assets')
@login_required
def assets():
    return render_template('assets.html')


@app.route('/joc/petomania/consumable')
@login_required
def consumable():
    return render_template('consumable.html')


# ── LADY / ASSETS API ─────────────────────────────────────────────────

@app.route('/joc/petomania/api/lady', methods=['GET'])
@login_required
def api_lady():
    user = get_current_user()
    uid  = int(user['id'])
    dialog = build_lady_dialog(uid, user['username'])
    return jsonify({'ok': True, 'dialog': dialog})


@app.route('/joc/petomania/api/lady/pet', methods=['GET'])
@login_required
def api_lady_pet():
    user        = get_current_user()
    uid         = int(user['id'])
    interaction = get_lady_interaction(uid)
    name        = interaction['player_name'] or user['username']
    text        = build_lady_pet_text(uid, name)
    return jsonify({'ok': True, 'text': text})


@app.route('/joc/petomania/api/lady/companicon', methods=['POST'])
@login_required
def api_lady_companicon():
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
    user = get_current_user()
    uid  = int(user['id'])
    name = request.json.get('name', '').strip()[:50]
    if not name:
        return jsonify({'ok': False, 'error': 'Nume invalid.'})
    conn = get_db()
    conn.execute('''
        INSERT INTO lady_interactions (user_id, first_interaction, player_name)
        VALUES (?, 0, ?)
        ON CONFLICT(user_id) DO UPDATE SET first_interaction = 0, player_name = excluded.player_name
    ''', (uid, name))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'name': name})


# ── COMPANICON ────────────────────────────────────────────────────────

# companicon_img nu mai e necesar — fisierele sunt in static/


@app.route('/joc/petomania/api/companicon')
@login_required
def api_companicon():
    user    = get_current_user()
    uid     = int(user['id'])
    entries = build_companicon_entries(uid)
    return jsonify({'ok': True, 'entries': entries})


@app.route('/joc/petomania/companicon')
@login_required
def companicon():
    return render_template('companicon.html')


# ── RUCSAC ────────────────────────────────────────────────────────────

@app.route('/joc/petomania/api/rucsac/data')
@login_required
def api_rucsac_data():
    user = get_current_user()
    uid  = int(user['id'])
    sync_pet(uid)
    sync_pet_hp(uid)
    pet        = get_pet(uid)
    pet_ctx    = _build_pet_context(pet) if pet else None
    categories = inv_build_context(uid)
    companions = [None, None, None, None, None]

    if pet_ctx and pet:
        p      = dict(pet)
        hp_max = pet_ctx['stats']['hp']
        hp_cur = p['hp_current']
        companions[0] = {
            'name': pet_ctx['name'], 'species': pet_ctx['species_name'],
            'level': pet_ctx['level'], 'form': pet_ctx['form'],
            'nature': pet_ctx['nat_data']['name'] if pet_ctx['nat_data'] else None,
            'nature_icon': pet_ctx['nat_data']['icon'] if pet_ctx['nat_data'] else None,
            'gender_icon': pet_ctx['gender_icon'], 'species_key': p['species'],
            'hp_current': hp_cur, 'hp_max': hp_max, 'active': True,
            'image_url': pet_ctx['image_url'],
        }

    loadout = get_loadout(uid)
    conn = get_db()
    for i, slot_key in enumerate(['slot_2', 'slot_3', 'slot_4', 'slot_5'], start=1):
        men_id = loadout[slot_key]
        if men_id:
            row = conn.execute('SELECT * FROM menagerie WHERE id = ? AND user_id = ?', (men_id, uid)).fetchone()
            if row:
                mp    = dict(row)
                mform = get_form(mp['level'])
                mstate = get_state(mp['hunger'], mp['happiness'], mp['cleanliness'],
                                   mp['energy'], bool(mp['sleeping']))
                mnat   = NATURES.get(mp.get('nature')) if mp.get('nature') else None
                mhp_max = get_stats_at_level(mp['species'], mp.get('nature'), mp['level'], mform)['hp']
                mhp_cur = mp['hp_current']
                companions[i] = {
                    'name': mp['name'],
                    'species': SPECIES.get(mp['species'], {}).get('name', mp['species']),
                    'level': mp['level'], 'form': mform,
                    'nature': mnat['name'] if mnat else None,
                    'nature_icon': mnat['icon'] if mnat else None,
                    'gender_icon': '♂️' if mp['gender'] == 'male' else '♀️',
                    'species_key': mp['species'],
                    'hp_current': mhp_cur, 'hp_max': mhp_max, 'active': False,
                    'image_url': get_image_url(mp['species'], mform, mstate, mp['gender']),
                }
    conn.close()
    return jsonify({'ok': True, 'categories': categories, 'companions': companions, 'dacoins': get_dacoins(uid)})


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
    hp_max   = stats['hp']
    hp_cur   = p['hp_current']
    return jsonify({
        'ok': True, 'name': p['name'],
        'species': SPECIES.get(p['species'], {}).get('name', p['species']),
        'species_key': p['species'], 'level': p['level'], 'form': form,
        'gender_icon': '♂️' if p['gender'] == 'male' else '♀️',
        'nature': nat_data['name'] if nat_data else None,
        'nature_icon': nat_data['icon'] if nat_data else None,
        'nature_color': nat_data['color'] if nat_data else None,
        'bonus_stat': nat_data['bonus_stat'] if nat_data else None,
        'hp_current': hp_cur, 'hp_max': hp_max,
        'stats': {k: stats[k] for k in ['hp','attack','defense','speed','evasion','healing','control','reflection']},
    })


# ── LOADOUT ───────────────────────────────────────────────────────────

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
    return render_template('loadout.html', slots=slots, menagerie=menagerie,
                           nexus_inferior=f"{STATIC_BASE}/items/NexusInferior.png",
                           nexus_superior=f"{STATIC_BASE}/items/NexusSuperior.png")


@app.route('/joc/petomania/api/loadout/set', methods=['POST'])
@login_required
def api_loadout_set():
    user   = get_current_user()
    uid    = int(user['id'])
    data   = request.json or {}
    slot   = int(data.get('slot', 0))
    men_id = data.get('men_id')
    if slot < 2 or slot > 5:
        return jsonify({'ok': False, 'error': 'Slot invalid.'})
    if men_id:
        conn = get_db()
        row  = conn.execute('SELECT id FROM menagerie WHERE id = ? AND user_id = ?', (men_id, uid)).fetchone()
        conn.close()
        if not row:
            return jsonify({'ok': False, 'error': 'Companion negăsit.'})
    current = get_loadout(uid)
    for k, v in current.items():
        if v == men_id and men_id is not None:
            current[k] = None
    current[f'slot_{slot}'] = men_id
    save_loadout(uid, current['slot_2'], current['slot_3'], current['slot_4'], current['slot_5'])
    conn = get_db()
    row  = conn.execute('SELECT * FROM menagerie WHERE id = ?', (men_id,)).fetchone() if men_id else None
    conn.close()
    return jsonify({'ok': True, 'slot': build_loadout_slot(row, slot)})


@app.route('/joc/petomania/api/loadout/clear', methods=['POST'])
@login_required
def api_loadout_clear():
    user = get_current_user()
    uid  = int(user['id'])
    slot = int((request.json or {}).get('slot', 0))
    if slot < 2 or slot > 5:
        return jsonify({'ok': False, 'error': 'Slot invalid.'})
    current = get_loadout(uid)
    current[f'slot_{slot}'] = None
    save_loadout(uid, current['slot_2'], current['slot_3'], current['slot_4'], current['slot_5'])
    return jsonify({'ok': True})



# ── MAGAZIN ───────────────────────────────────────────────────────────

@app.route('/joc/petomania/api/shop/<shop_id>')
@login_required
def api_shop_data(shop_id):
    ctx = build_shop_context(shop_id)
    if not ctx:
        return jsonify({'ok': False, 'error': 'Magazin inexistent.'})
    user    = get_current_user()
    dacoins = get_dacoins(int(user['id']))
    return jsonify({'ok': True, 'shop': ctx, 'dacoins': dacoins})


@app.route('/joc/petomania/api/shop/<shop_id>/buy', methods=['POST'])
@login_required
def api_shop_buy(shop_id):
    user     = get_current_user()
    uid      = int(user['id'])
    data     = request.json or {}
    category = data.get('category', '')
    item_key = data.get('item_key', '')
    qty      = int(data.get('qty', 1))
    if not category or not item_key:
        return jsonify({'ok': False, 'error': 'Date lipsă.'})
    return jsonify(shop_buy(uid, shop_id, category, item_key, qty))


# ── ARENA ────────────────────────────────────────────────────────────

@app.route('/joc/petomania/arena')
@login_required
def arena():
    return render_template('arena.html')



# ── CORVIN VARGAN ─────────────────────────────────────────────────────

@app.route('/joc/petomania/api/corvin')
@login_required
def api_corvin():
    user = get_current_user()
    uid  = int(user['id'])
    conn = get_db()
    row  = conn.execute('SELECT talked FROM corvin_interactions WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    first_time = (row is None or not row['talked'])
    return jsonify({'ok': True, 'first_time': first_time})


@app.route('/joc/petomania/api/corvin/talked', methods=['POST'])
@login_required
def api_corvin_talked():
    user = get_current_user()
    uid  = int(user['id'])
    conn = get_db()
    conn.execute('''
        INSERT INTO corvin_interactions (user_id, talked)
        VALUES (?, 1)
        ON CONFLICT(user_id) DO UPDATE SET talked = 1
    ''', (uid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})



# ── BATTLE ARENA ─────────────────────────────────────────────────────


def _save_bench_hp(bench: list):
    """Salveaza HP-ul curent al pets din bench in menagerie."""
    if not bench:
        return
    conn = get_db()
    for p in bench:
        if p.get('id'):
            conn.execute('UPDATE menagerie SET hp_current = ? WHERE id = ?',
                         (max(0, p.get('hp_current', 0)), p['id']))
    conn.commit()
    conn.close()

@app.route('/joc/petomania/api/battle/start', methods=['POST'])
@login_required
def api_battle_start():
    from modules.battle import build_combatant, generate_npc
    from moves_config import get_move
    from modules.pets import sync_pet, get_form, get_state
    user = get_current_user()
    uid  = int(user['id'])

    data_req     = request.json or {}
    battle_size  = min(max(int(data_req.get('size', 1)), 1), 3)

    # Petul activ (slot 1)
    pet = sync_pet(uid)
    if not pet:
        return jsonify({'ok': False, 'error': 'Nu ai un companion activ.'})
    pet = dict(pet)

    player = build_combatant(pet)

    # Initializeaza HP in menagerie pentru pets care nu au luptat niciodata
    sync_menagerie_hp(uid)

    # Loadout complet pentru switch
    loadout_raw = build_loadout_context(uid)
    bench = []  # petii de pe bancă — max battle_size-1 pets
    for slot in loadout_raw:
        if slot.get('empty') or slot.get('slot') == 1:
            continue
        if len(bench) >= battle_size - 1:
            break
        bench.append({
            'id':        slot['id'],
            'name':      slot['name'],
            'level':     slot['level'],
            'hp_max':    slot['hp_max'],
            'hp_current':slot['hp_current'],
            'image_url': slot['image_url'],
            'species':   slot['species_key'],
            'nature':    slot['nature_key'],
            'gender':    slot.get('gender', 'male'),
        })

    # Daca petul activ e mort, inlocuieste-l cu primul din loadout cu HP > 0
    if player['hp_current'] <= 0:
        # Cauta in tot loadout-ul (nu doar in bench limitat)
        all_bench = []
        for slot in loadout_raw:
            if slot.get('empty') or slot.get('slot') == 1:
                continue
            all_bench.append(slot)
        alive_slots = [s for s in all_bench if s.get('hp_current', 0) > 0]
        if not alive_slots:
            return jsonify({'ok': False, 'error': 'Toți companionii tăi sunt KO. Vindecă-i înainte de luptă.'})
        first = alive_slots[0]
        conn_b = get_db()
        row_b  = conn_b.execute('SELECT * FROM menagerie WHERE id = ? AND user_id = ?', (first['id'], uid)).fetchone()
        conn_b.close()
        if not row_b:
            return jsonify({'ok': False, 'error': 'Companion negăsit.'})
        player = build_combatant(dict(row_b))
        # Reconstruieste bench fara noul player
        bench = []
        for slot in loadout_raw:
            if slot.get('empty') or slot.get('slot') == 1:
                continue
            if str(slot['id']) == str(first['id']):
                continue
            if len(bench) >= battle_size - 1:
                break
            bench.append({
                'id':        slot['id'],
                'name':      slot['name'],
                'level':     slot['level'],
                'hp_max':    slot['hp_max'],
                'hp_current':slot['hp_current'],
                'image_url': slot['image_url'],
                'species':   slot['species_key'],
                'nature':    slot['nature_key'],
                'gender':    slot.get('gender', 'male'),
            })

    npc = generate_npc(player['level'])

    moveset_data = []
    for mk in player['moveset']:
        m = get_move(mk)
        if m:
            moveset_data.append({'key': m['key'], 'name': m['name'], 'icon': m['icon'], 'type': m['type'], 'power': m['power']})

    session['battle_player']    = player
    session['battle_npc']       = npc
    session['battle_bench']     = bench
    session['battle_size']      = battle_size
    session['battle_npc_index'] = 1

    return jsonify({
        'ok': True,
        'player': {
            'id': player['id'], 'name': player['name'], 'species': player['species'],
            'nature': player['nature'], 'level': player['level'],
            'hp_max': player['hp_max'], 'hp_current': player['hp_current'],
            'image_url': player['image_url'], 'moveset': moveset_data,
            'status': None, 'shield': 0,
        },
        'npc': {
            'id': npc['id'], 'name': npc['name'], 'species': npc['species'],
            'nature': npc['nature'], 'level': npc['level'],
            'hp_max': npc['hp_max'], 'hp_current': npc['hp_current'],
            'image_url': npc['image_url'], 'status': None, 'shield': 0,
        },
        'bench': bench,
    })


@app.route('/joc/petomania/api/battle/turn', methods=['POST'])
@login_required
def api_battle_turn():
    from modules.battle import execute_turn, calculate_reward
    user   = get_current_user()
    uid    = int(user['id'])
    player = session.get('battle_player')
    npc    = session.get('battle_npc')
    if not player or not npc:
        return jsonify({'ok': False, 'error': 'Nicio bătălie activă.'})

    # Re-citeste HP din DB inainte de tur doar daca playerul e petul activ (id=None = din pets)
    # Daca e din menagerie (id != None), HP-ul lui e in sesiune, nu in tabela pets
    if player.get('id') is None or player.get('id') == 0:
        conn = get_db()
        fresh = conn.execute('SELECT hp_current FROM pets WHERE user_id = ?', (uid,)).fetchone()
        conn.close()
        if fresh:
            player['hp_current'] = fresh['hp_current']

    move_key = (request.json or {}).get('move_key', 'scratch')
    result   = execute_turn(player, npc, move_key)

    # Salveaza HP dupa fiecare tur in DB
    conn = get_db()
    conn.execute('UPDATE pets SET hp_current = ? WHERE user_id = ?', (max(0, player['hp_current']), uid))
    conn.commit()
    conn.close()

    session['battle_player'] = player
    session['battle_npc']    = npc

    reward = 0
    if result['winner'] == 'player':
        npc_index   = session.get('battle_npc_index', 1)
        battle_size = session.get('battle_size', 1)

        if npc_index < battle_size:
            # Mai sunt NPC-uri — genereaza urmatorul
            from modules.battle import generate_npc as _gen_npc
            new_npc = _gen_npc(player['level'])
            session['battle_npc']       = new_npc
            session['battle_npc_index'] = npc_index + 1
            session['battle_player']    = player
            return jsonify({
                'ok': True, 'log': result['log'],
                'player': result['player'],
                'npc': {
                    'id': new_npc['id'], 'name': new_npc['name'],
                    'species': new_npc['species'], 'nature': new_npc['nature'],
                    'level': new_npc['level'], 'hp_max': new_npc['hp_max'],
                    'hp_current': new_npc['hp_current'],
                    'image_url': new_npc['image_url'], 'status': None, 'shield': 0,
                },
                'winner': None,
                'next_npc': True,
                'reward': 0,
            })

        # Ultimul NPC doborat — victorie finala
        reward = calculate_reward(player['level'], npc['level'], True)
        if reward > 0:
            conn = get_db()
            conn.execute('UPDATE dacoins SET balance = balance + ? WHERE user_id = ?', (reward, uid))
            conn.commit()
            conn.close()
        _save_bench_hp(session.get('battle_bench', []))
        session.pop('battle_player', None)
        session.pop('battle_npc', None)
        session.pop('battle_size', None)
        session.pop('battle_npc_index', None)
    elif result['winner'] == 'npc':
        conn = get_db()
        conn.execute('UPDATE pets SET hp_current = 0 WHERE user_id = ?', (uid,))
        conn.commit()
        conn.close()
        bench = session.get('battle_bench', [])
        alive = [p for p in bench if p.get('hp_current', 0) > 0]
        if alive:
            # Mai sunt pets in bench — lasa sesiunea activa pentru switch
            session['battle_player'] = player
        else:
            # Niciun pet disponibil — lupta pierduta
            _save_bench_hp(bench)
            session.pop('battle_player', None)
            session.pop('battle_npc', None)
            session.pop('battle_size', None)
            session.pop('battle_npc_index', None)

    return jsonify({
        'ok': True, 'log': result['log'],
        'player': result['player'], 'npc': result['npc'],
        'winner': result['winner'], 'reward': reward,
        'bench': session.get('battle_bench', []),
    })


@app.route('/joc/petomania/api/battle/flee', methods=['POST'])
@login_required
def api_battle_flee():
    user   = get_current_user()
    uid    = int(user['id'])
    player = session.get('battle_player')
    if player:
        conn = get_db()
        conn.execute('UPDATE pets SET hp_current = ? WHERE user_id = ?', (max(1, player['hp_current']), uid))
        conn.commit()
        conn.close()
    session.pop('battle_player', None)
    session.pop('battle_npc', None)
    return jsonify({'ok': True})



# ── BATTLE PAGE ───────────────────────────────────────────────────────

@app.route('/joc/petomania/battle')
@login_required
def battle():
    return render_template('battle.html')


@app.route('/joc/petomania/api/battle/switch', methods=['POST'])
@login_required
def api_battle_switch():
    from modules.battle import build_combatant
    from moves_config import get_move
    user   = get_current_user()
    uid    = int(user['id'])
    pet_id = (request.json or {}).get('pet_id')
    bench  = session.get('battle_bench', [])

    pet_data = next((p for p in bench if str(p['id']) == str(pet_id)), None)
    if not pet_data:
        return jsonify({'ok': False, 'error': 'Pet negasit pe bancă.'})
    if pet_data['hp_current'] <= 0:
        return jsonify({'ok': False, 'error': 'Acest companion a căzut.'})

    # Construieste noul combatant
    from modules.db import get_db
    conn = get_db()
    row  = conn.execute('SELECT * FROM menagerie WHERE id = ? AND user_id = ?', (pet_data['id'], uid)).fetchone()
    conn.close()
    if not row:
        return jsonify({'ok': False, 'error': 'Pet negasit în DB.'})

    new_player = build_combatant(dict(row))
    moveset_data = []
    for mk in new_player['moveset']:
        m = get_move(mk)
        if m:
            moveset_data.append({'key': m['key'], 'name': m['name'], 'icon': m['icon'], 'type': m['type'], 'power': m['power']})

    # Salveaza HP-ul petului care iese din arena
    old_player = session.get('battle_player')
    if old_player:
        old_id = old_player.get('id', 0)
        old_hp = max(0, old_player.get('hp_current', 0))
        conn2 = get_db()
        if old_id and old_id != 0:
            # Pet din menagerie
            conn2.execute('UPDATE menagerie SET hp_current = ? WHERE id = ?', (old_hp, old_id))
        else:
            # Pet activ din pets
            conn2.execute('UPDATE pets SET hp_current = ? WHERE user_id = ?', (old_hp, uid))
        conn2.commit()
        conn2.close()
        # Actualizeaza HP si in bench daca e acolo
        updated_bench = []
        for p in bench:
            if str(p['id']) != str(pet_id):
                if str(p.get('id')) == str(old_id):
                    p = dict(p)
                    p['hp_current'] = old_hp
                updated_bench.append(p)
        bench = updated_bench

    # Scoate din bench
    session['battle_bench']  = [p for p in bench if str(p['id']) != str(pet_id)]
    session['battle_player'] = new_player

    return jsonify({
        'ok': True,
        'player': {
            'id': new_player['id'], 'name': new_player['name'],
            'species': new_player['species'], 'nature': new_player['nature'],
            'level': new_player['level'], 'hp_max': new_player['hp_max'],
            'hp_current': new_player['hp_current'], 'image_url': new_player['image_url'],
            'moveset': moveset_data, 'status': None, 'shield': 0,
        },
    })



# ── BATTLE STATE ─────────────────────────────────────────────────────

@app.route('/joc/petomania/api/battle/state')
@login_required
def api_battle_state():
    from moves_config import get_move
    player = session.get('battle_player')
    npc    = session.get('battle_npc')
    bench  = session.get('battle_bench', [])
    if not player or not npc:
        return jsonify({'ok': False, 'active': False})

    moveset_data = []
    for mk in player.get('moveset', []):
        m = get_move(mk)
        if m:
            moveset_data.append({'key': m['key'], 'name': m['name'], 'icon': m['icon'], 'type': m['type'], 'power': m['power']})

    # Re-citeste HP din DB — poate fi modificat de potiuni intre tururi
    conn = get_db()
    fresh = conn.execute('SELECT hp_current FROM pets WHERE user_id = ?', (int(get_current_user()['id']),)).fetchone()
    conn.close()
    if fresh:
        player['hp_current'] = fresh['hp_current']
        session['battle_player'] = player

    return jsonify({
        'ok': True, 'active': True,
        'player': {
            'id': player['id'], 'name': player['name'],
            'level': player.get('level', 1),
            'hp_max': player['hp_max'], 'hp_current': player['hp_current'],
            'image_url': player.get('image_url', ''),
            'moveset': moveset_data, 'status': player.get('status'), 'shield': player.get('shield', 0),
        },
        'npc': {
            'id': npc['id'], 'name': npc['name'],
            'level': npc.get('level', 1),
            'hp_max': npc['hp_max'], 'hp_current': npc['hp_current'],
            'image_url': npc.get('image_url', ''),
            'status': npc.get('status'), 'shield': npc.get('shield', 0),
        },
        'bench': bench,
    })



# ── BATTLE ABANDON ────────────────────────────────────────────────────

@app.route('/joc/petomania/api/battle/abandon', methods=['POST'])
@login_required
def api_battle_abandon():
    """Curata sesiunea de lupta fara a salva HP."""
    session.pop('battle_player', None)
    session.pop('battle_npc', None)
    session.pop('battle_bench', None)
    return jsonify({'ok': True})



# ── LOADOUT COUNT ────────────────────────────────────────────────────

@app.route('/joc/petomania/api/loadout/count')
@login_required
def api_loadout_count():
    uid   = int(get_current_user()['id'])
    slots = build_loadout_context(uid)
    count = sum(1 for s in slots if not s.get('empty'))
    return jsonify({'ok': True, 'count': count})


# ── RUN ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=False)
