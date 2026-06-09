"""
modules/inventory.py
Rucsac: inv_add, inv_remove, inv_build_context, use_item, rename_pet.
"""
from inventory_config import (
    CATEGORY_SLOTS, STACK_MAX,
    CATEGORY_NAMES, CATEGORY_ORDER, USE_STUB_MESSAGES,
    get_item as inv_get_item,
)
from cogs.petgame_stats import get_stats_at_level
from modules.db import get_db
from modules.pets import get_pet, get_form


def inv_get_all(user_id: int) -> dict:
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
            return {'ok': False, 'error': f'Categoria "{CATEGORY_NAMES.get(category, category)}" este plină.'}
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
                    'icon':                  item_cfg.get('img') or item_cfg['icon'],
                    'is_img':                bool(item_cfg.get('img')),
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
    form  = get_form(p['level'])
    stats = get_stats_at_level(p['species'], p.get('nature'), p['level'], form)
    return stats['hp']


def use_item(user_id: int, category: str, item_key: str) -> dict:
    item_cfg = inv_get_item(category, item_key)
    if not item_cfg:
        return {'ok': False, 'msg': 'Item necunoscut.'}
    if item_cfg.get('quest_item'):
        return {'ok': False, 'msg': 'Acest item nu poate fi folosit direct.'}
    if item_cfg.get('usable_in_zone'):
        return {'ok': False, 'msg': USE_STUB_MESSAGES.get(category, 'Necesită zonă specifică.')}
    if category in USE_STUB_MESSAGES and category not in ('mancare', 'medical', 'potiuni'):
        return {'ok': False, 'msg': USE_STUB_MESSAGES[category]}

    pet = get_pet(user_id)
    if not pet:
        return {'ok': False, 'msg': 'Nu ai un companion activ.'}

    p       = dict(pet)
    effects = item_cfg.get('effects', {})
    changed = []

    if category == 'mancare':
        if 'hunger' in effects:
            p['hunger'] = min(100, p['hunger'] + effects['hunger'])
            changed.append(f"Foame +{effects['hunger']}")
        if 'energy' in effects:
            p['energy'] = min(100, p['energy'] + effects['energy'])
            changed.append(f"Energie +{effects['energy']}")
        if 'hp' in effects:
            hp_max = _get_hp_max(p)
            p['hp_current'] = min(hp_max, p['hp_current'] + effects['hp'])
            changed.append(f"HP +{effects['hp']}")
    elif category == 'medical':
        if 'hp' in effects:
            hp_max = _get_hp_max(p)
            old_hp = p['hp_current']
            new_hp = min(hp_max, old_hp + effects['hp'])
            healed = new_hp - old_hp
            if healed <= 0:
                return {'ok': False, 'msg': 'HP-ul companionului este deja plin.'}
            p['hp_current'] = new_hp
            changed.append(f"HP +{healed}")

    elif category == 'potiuni':
        if 'hp' in effects:
            hp_max = _get_hp_max(p)
            old_hp = p['hp_current']
            new_hp = min(hp_max, old_hp + effects['hp'])
            healed = new_hp - old_hp
            if healed <= 0:
                return {'ok': False, 'msg': 'HP-ul companionului este deja plin.'}
            p['hp_current'] = new_hp
            changed.append(f"HP +{healed}")
        if 'hunger' in effects:
            p['hunger'] = min(100, p['hunger'] + effects['hunger'])
            changed.append(f"Foame +{effects['hunger']}")
        if 'energy' in effects:
            p['energy'] = min(100, p['energy'] + effects['energy'])
            changed.append(f"Energie +{effects['energy']}")

    if not changed:
        return {'ok': False, 'msg': 'Acest item nu are efect momentan.'}

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
