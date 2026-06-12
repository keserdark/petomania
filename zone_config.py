# ─────────────────────────────────────────────
# zone_config.py
# Pool-uri de specii si naturi per zona.
# Editeaza DOAR acest fisier pentru a modifica ce apare in fiecare zona.
# ─────────────────────────────────────────────

ZONE_POOLS = {

    'arena': {
        'species': ['dog', 'cat', 'blackcat', 'duck', 'fox', 'rhino'],
        'natures': ['fire', 'water', 'nature', 'earth', 'storm', 'ice',
                    'shadow', 'crystal', 'steel', 'light', 'dragon'],
    },

    'vanatoare': {
        'species': ['cat', 'duck', 'fox'],
        'natures': ['nature', 'water', 'earth', 'storm', 'ice'],
    },

    'padure': {
        'species': ['cat', 'duck'],
        'natures': ['nature', 'water', 'earth'],
    },

    'paduremid': {
        'species': ['cat', 'duck', 'fox'],
        'natures': ['nature', 'water', 'earth', 'storm'],
    },

    'paduredeep': {
        'species': ['cat', 'duck', 'fox', 'blackcat'],
        'natures': ['nature', 'water', 'earth', 'storm', 'shadow', 'ice'],
    },

}

# Fallback daca zona nu e definita
DEFAULT_POOL = {
    'species': ['dog', 'cat', 'blackcat', 'duck', 'fox', 'rhino'],
    'natures': ['fire', 'water', 'nature', 'earth', 'storm', 'ice',
                'shadow', 'crystal', 'steel', 'light', 'dragon'],
}


def get_zone_pool(zone: str) -> dict:
    return ZONE_POOLS.get(zone, DEFAULT_POOL)
