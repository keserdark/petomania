# ─────────────────────────────────────────────
# inventory_config.py
# Catalogul de iteme pentru sistemul Rucsac.
# Adaugă iteme noi DOAR în acest fișier.
# Codul din petgame_app.py nu trebuie modificat.
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# STRUCTURA UNUI ITEM:
#
# {
#     'key':      'nexus_simplu',      # ID unic snake_case
#     'name':     'Nexus Simplu',      # Nume afișat
#     'desc':     'Descriere scurtă',  # Afișat în popup
#     'icon':     '🔵',               # Emoji icon
#     'price':    50,                  # Preț Dacoins (0 = nu se cumpără)
#
#     # EFECTE — folosite de logica use_item()
#     # Omite cheile care nu se aplică itemului.
#     'effects': {
#         'hunger':     20,    # Mâncare — crește foamea
#         'energy':     15,    # Mâncare — crește energia
#         'hp':         30,    # Mâncare/Medical — restaurează HP luptă
#     },
#
#     # COMPORTAMENT
#     'usable_outside_battle': True,   # False = stub "doar în luptă"
#     'usable_in_zone': False,         # True = necesită zonă specifică (ofrande/capcane)
#     'quest_item': False,             # True = nu se poate arunca, nu apare "Folosește"
# }
# ─────────────────────────────────────────────

INVENTORY_ITEMS = {

    # ── NEXUS GLOBURI ────────────────────────────
    'nexus': [
        # Primul item va fi adăugat aici
    ],

    # ── MÂNCARE ──────────────────────────────────
    'mancare': [
        # Primul item va fi adăugat aici
    ],

    # ── MEDICAMENTE ──────────────────────────────
    'medical': [
        # Primul item va fi adăugat aici
    ],

    # ── ESENȚE ───────────────────────────────────
    'esente': [
        # Primul item va fi adăugat aici
    ],

    # ── POȚIUNI ──────────────────────────────────
    'potiuni': [
        # Primul item va fi adăugat aici
    ],

    # ── OFRANDE ──────────────────────────────────
    'ofrande': [
        # Primul item va fi adăugat aici
    ],

    # ── CAPCANE ──────────────────────────────────
    'capcane': [
        # Primul item va fi adăugat aici
    ],

    # ── QUEST ITEMS ──────────────────────────────
    'quest': [
        # Quest items sunt adăugate programatic, nu manual
    ],
}

# ─────────────────────────────────────────────
# CONSTANTE SISTEM
# ─────────────────────────────────────────────

CATEGORY_SLOTS = 10   # Sloturi unice per categorie
STACK_MAX      = 12   # Cantitate maximă per slot

CATEGORY_NAMES = {
    'nexus':   'Nexus Globuri',
    'mancare': 'Mâncare',
    'medical': 'Medicamente',
    'esente':  'Esențe',
    'potiuni': 'Poțiuni',
    'ofrande': 'Ofrande',
    'capcane': 'Capcane',
    'quest':   'Quest Items',
}

CATEGORY_ORDER = ['nexus', 'mancare', 'medical', 'esente', 'potiuni', 'ofrande', 'capcane', 'quest']

# Mesaje stub per categorie când efectul nu e implementat încă
USE_STUB_MESSAGES = {
    'nexus':   'Nexus Globurile se folosesc în captură.',
    'esente':  'Efectul acestei esențe va fi definit în curând.',
    'potiuni': 'Poțiunile se folosesc înainte sau în timpul luptei.',
    'ofrande': 'Această ofrandă poate fi prezentată doar în zone specifice.',
    'capcane': 'Capcanele pot fi plasate doar în zone specifice.',
}

# ─────────────────────────────────────────────
# HELPER — lookup rapid după cheie
# ─────────────────────────────────────────────

def get_item(category: str, item_key: str) -> dict | None:
    """Returnează un item după categorie și cheie."""
    for item in INVENTORY_ITEMS.get(category, []):
        if item['key'] == item_key:
            return item
    return None


def get_all_items_flat() -> dict[str, dict]:
    """Returnează toate itemele ca dict {item_key: item_data} pentru lookup rapid."""
    result = {}
    for cat_items in INVENTORY_ITEMS.values():
        for item in cat_items:
            result[item['key']] = item
    return result
