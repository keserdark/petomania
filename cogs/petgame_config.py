# ─────────────────────────────────────────────
# petgame_config.py
# Adauga animale noi doar aici — fara sa modifici petgame_cog.py
# ─────────────────────────────────────────────

GITHUB_BASE = "https://raw.githubusercontent.com/keserdark/village-bot/main/PetGame/static/00transparent"

NATURES = {
    'fire': {
        'name': 'Foc', 'icon': '🔥', 'color': '#f97316',
        'flavor': 'Agresiv, energie înaltă, arde scurt și puternic.',
        'bonus_stat': 'Atac',
        'strong_against': ['nature', 'ice', 'steel', 'shadow'],
        'weak_against': ['water', 'earth', 'storm'],
        'vulnerable_to': ['water', 'earth'],
        'resists_from': ['fire', 'nature', 'ice', 'steel'],
        'immune_to': [], 'evo_line': ['Flăcărică', 'Ignar', 'Volcadon'],
    },
    'water': {
        'name': 'Apă', 'icon': '💧', 'color': '#3b82f6',
        'flavor': 'Adaptabil, rezistent, controlează fluxul luptei.',
        'bonus_stat': 'Viteză',
        'strong_against': ['fire', 'earth', 'crystal'],
        'weak_against': ['storm', 'nature'],
        'vulnerable_to': ['storm', 'nature'],
        'resists_from': ['fire', 'water', 'ice'],
        'immune_to': [], 'evo_line': ['Stropel', 'Curentix', 'Abismara'],
    },
    'nature': {
        'name': 'Natură', 'icon': '🌿', 'color': '#22c55e',
        'flavor': 'Răbdător, regenerativ, câștigă prin uzură.',
        'bonus_stat': 'Viață',
        'strong_against': ['water', 'earth', 'crystal'],
        'weak_against': ['fire', 'ice', 'shadow', 'storm'],
        'vulnerable_to': ['fire', 'ice'],
        'resists_from': ['water', 'earth', 'nature'],
        'immune_to': [], 'evo_line': ['Mugur', 'Florun', 'Dendrix'],
    },
    'earth': {
        'name': 'Pământ', 'icon': '🪨', 'color': '#a16207',
        'flavor': 'Stabil, apărare ridicată, lent dar implacabil.',
        'bonus_stat': 'Apărare',
        'strong_against': ['fire', 'storm', 'steel', 'shadow'],
        'weak_against': ['water', 'nature', 'ice'],
        'vulnerable_to': ['water', 'nature'],
        'resists_from': ['fire', 'steel', 'earth'],
        'immune_to': ['storm'], 'evo_line': ['Bolovan', 'Stânex', 'Tectoran'],
    },
    'storm': {
        'name': 'Furtună', 'icon': '⚡', 'color': '#eab308',
        'flavor': 'Rapid, imprevizibil, combo-uri electrizante.',
        'bonus_stat': 'Viteză',
        'strong_against': ['water', 'nature', 'steel'],
        'weak_against': ['earth', 'crystal'],
        'vulnerable_to': ['earth'],
        'resists_from': ['storm', 'fire', 'nature'],
        'immune_to': [], 'evo_line': ['Scânteiuț', 'Fulgeran', 'Tempestix'],
    },
    'ice': {
        'name': 'Gheață', 'icon': '❄️', 'color': '#67e8f9',
        'flavor': 'Control și lentire, răcește orice amenințare.',
        'bonus_stat': 'Control',
        'strong_against': ['nature', 'water', 'crystal', 'shadow'],
        'weak_against': ['fire', 'steel', 'storm'],
        'vulnerable_to': ['fire', 'steel'],
        'resists_from': ['ice', 'crystal'],
        'immune_to': [], 'evo_line': ['Fulgușor', 'Crionar', 'Glacidra'],
    },
    'shadow': {
        'name': 'Umbră', 'icon': '🌑', 'color': '#6d28d9',
        'flavor': 'Imprevizibil, misterios, evită atacuri cu abilități psihice.',
        'bonus_stat': 'Eludare',
        'strong_against': ['crystal', 'storm', 'fire'],
        'weak_against': ['nature', 'earth', 'light'],
        'vulnerable_to': ['light', 'nature'],
        'resists_from': ['shadow', 'storm', 'fire'],
        'immune_to': ['crystal'], 'evo_line': ['Penumbrix', 'Obscuran', 'Voidmara'],
    },
    'crystal': {
        'name': 'Cristal', 'icon': '💎', 'color': '#c084fc',
        'flavor': 'Echilibrat, versatil, reflectă o parte din daune.',
        'bonus_stat': 'Reflecție',
        'strong_against': ['shadow', 'ice', 'storm'],
        'weak_against': ['fire', 'water', 'nature'],
        'vulnerable_to': ['fire', 'nature'],
        'resists_from': ['crystal', 'shadow', 'ice'],
        'immune_to': [], 'evo_line': ['Schijă', 'Prismax', 'Gemalodon'],
    },
    'steel': {
        'name': 'Metal', 'icon': '⚙️', 'color': '#94a3b8',
        'flavor': 'Tanc pur, rezistențe multiple, daune constante.',
        'bonus_stat': 'Apărare',
        'strong_against': ['ice', 'crystal', 'nature'],
        'weak_against': ['fire', 'earth', 'storm'],
        'vulnerable_to': ['fire', 'earth'],
        'resists_from': ['steel', 'ice', 'crystal', 'nature', 'shadow'],
        'immune_to': [], 'evo_line': ['Bolțar', 'Fierotex', 'Ferromax'],
    },
    'light': {
        'name': 'Lumină', 'icon': '✨', 'color': '#fbbf24',
        'flavor': 'Suport și vindecare, contracarează Umbra.',
        'bonus_stat': 'Vindecare',
        'strong_against': ['shadow', 'ice', 'crystal'],
        'weak_against': ['earth', 'steel'],
        'vulnerable_to': ['shadow', 'earth'],
        'resists_from': ['light', 'fire', 'nature'],
        'immune_to': [], 'evo_line': ['Licarix', 'Auroraan', 'Radioss'],
    },
}

# ─────────────────────────────────────────────
# SPECII
# ─────────────────────────────────────────────

SPECIES = {
    'cat': {
        'starter': True,
        'name': 'Pisică', 'emoji': '🐱', 'button_label': '🐱 Pisică',
        'codes': {1: 'CAT-001', 2: 'CAT-002', 3: 'CAT-003'},
        'available_natures': ['light'],
        'entries': {
            1: {
                'code': 'CAT-001',
                'name': 'Pisicuță',
                'description': 'O pisică tânără, curioasă și plină de energie. Prima formă a companionului de lumină.',
                'lore': 'Acesta este unul din companionii îmblânziți de regat, prin artele magice ale acestora, o pisică simplă poate evolua în forme neașteptate.\n\nAgilă, inteligentă și loială, această mică felină este mai mult decât un simplu prieten de drum. Are un simț aparte pentru magie și un instinct protector puternic față de partenerul său.\n\nDeși la început pare doar o pisică obișnuită, cu timpul își poate dezvolta abilități unice, influențate de legătura sa cu stăpânul și de experiențele trăite împreună.',
            },
            2: {
                'code': 'CAT-002',
                'name': 'Pisică',
                'description': 'Pisica a crescut și a câștigat mai multă forță. Legătura cu natura luminii devine mai puternică.',
                'lore': 'Odată o simplă pisică, acum o ființă atinsă de magia Luminii.\n\nAcesta este unul dintre companionii îmblânziți de Regat. Prin artele magice ale acestora, o pisică obișnuită poate evolua în forme neașteptate.\n\nLoială și curajoasă, își însoțește stăpânul în aventurile sale, iar puterea sa continuă să crească odată cu legătura dintre ei.',
            },
            3: {
                'code': 'CAT-003',
                'name': 'Pisică Înțeleaptă',
                'description': 'Forma finală a pisicii de lumină. O creatură maiestuoasă cu puteri de vindecare extraordinare.',
                'lore': 'O ființă legendară, întruchiparea supremă a Luminii și a legăturii dintre companion și stăpân.\n\nAcesta este unul dintre companionii îmblânziți de Regat. Prin artele magice ale acestora, o simplă pisică poate evolua în forme de neimaginat.\n\nAripile sale strălucitoare și aura sa cerească sunt pomenite în vechile cronici ale Regatului.',
            },
        },
        'images': {
            1: {
                'Basic':  f'{GITHUB_BASE}/cat/Stage1-Basic-Form.png',
                'Hungry': f'{GITHUB_BASE}/cat/Stage1-Hungry-Form.png',
                'Dirty':  f'{GITHUB_BASE}/cat/Stage1-Dirty-Form.png',
                'Sad':    f'{GITHUB_BASE}/cat/Stage1-Sad-Form.png',
                'Sleep':  f'{GITHUB_BASE}/cat/Stage1-Sleep-Form.png',
            },
            2: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/cat/Stage2-Basic-Form.png',
                    'Hungry': f'{GITHUB_BASE}/cat/Stage2-Hungry-Form.png',
                    'Dirty':  f'{GITHUB_BASE}/cat/Stage2-Dirty-Form.png',
                    'Sad':    f'{GITHUB_BASE}/cat/Stage2-Sad-Form.png',
                    'Sleep':  f'{GITHUB_BASE}/cat/Stage2-Sleep-Form.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/cat/Stage2-Basic-Form.png',
                    'Hungry': f'{GITHUB_BASE}/cat/Stage2-Hungry-Form.png',
                    'Dirty':  f'{GITHUB_BASE}/cat/Stage2-Dirty-Form.png',
                    'Sad':    f'{GITHUB_BASE}/cat/Stage2-Sad-Form.png',
                    'Sleep':  f'{GITHUB_BASE}/cat/Stage2-Sleep-Form.png',
                },
            },
            3: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/cat/Stage3-Basic-Form.png',
                    'Hungry': f'{GITHUB_BASE}/cat/Stage3-Hungry-Form.png',
                    'Dirty':  f'{GITHUB_BASE}/cat/Stage3-Dirty-Form.png',
                    'Sad':    f'{GITHUB_BASE}/cat/Stage3-Sad-Form.png',
                    'Sleep':  f'{GITHUB_BASE}/cat/Stage3-Sleep-Form.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/cat/Stage3-Basic-Form.png',
                    'Hungry': f'{GITHUB_BASE}/cat/Stage3-Hungry-Form.png',
                    'Dirty':  f'{GITHUB_BASE}/cat/Stage3-Dirty-Form.png',
                    'Sad':    f'{GITHUB_BASE}/cat/Stage3-Sad-Form.png',
                    'Sleep':  f'{GITHUB_BASE}/cat/Stage3-Sleep-Form.png',
                },
            },
        }
    },

    'duck': {
        'starter': True,
        'name': 'Rață', 'emoji': '🦆', 'button_label': '🦆 Rață',
        'codes': {1: 'DUCK-001', 2: 'DUCK-002', 3: 'DUCK-003'},
        'available_natures': ['water'],
        'entries': {
            1: {
                'code': 'DUCK-001',
                'name': 'Boboc',
                'description': 'Un boboc simpatic care abia a descoperit apa. Natura sa de Apă îl face un înotător natural.',
                'lore': 'O rățușcă tânără, curioasă și plină de energie. Prima formă a acestui companion de Apă.\n\nAcesta este unul dintre companionii îmblânziți de Regat. Prin artele magice ale acestora, o simplă rățușcă poate evolua în forme neașteptate.\n\nJucăușă și prietenoasă, își urmează stăpânul oriunde, plutind cu grație și aducând noroc în călătorii.',
            },
            2: {
                'code': 'DUCK-002',
                'name': 'Rățușcă',
                'description': 'A crescut și stăpânește acum curenții de apă cu ușurință. Diferențe clare între mascul și femelă.',
                'lore': 'Diferențele între mascul și femelă devin vizibile în această formă. Amândoi stăpânesc curenții de apă cu o ușurință fascinantă.\n\nPoate crea scuturi de apă și poate accelera vindecarea aliaților prin contact cu apa purificată de magia sa.',
            },
            3: {
                'code': 'DUCK-003',
                'name': 'Rață Maestră',
                'description': 'Forma finală. Controlează apa cu precizie extraordinară și poate prezice furtunile viitoare.',
                'lore': 'Maestrul apelor a atins forma sa perfectă. Poate controla precipitațiile într-o rază largă și prezice furtunile cu zile înainte.\n\nÎn luptă, creează torente devastatoare. În pace, poate purifica otrăvurile și tămădui răni grave prin puterea apei sacre pe care o canalizează.',
            },
        },
        'images': {
            1: {
                'Basic':  f'{GITHUB_BASE}/duck/Stage1-Basic-Form.png',
                'Hungry': f'{GITHUB_BASE}/duck/Stage1-Hungry-Form.png',
                'Dirty':  f'{GITHUB_BASE}/duck/Stage1-Dirty-Form.png',
                'Sad':    f'{GITHUB_BASE}/duck/Stage1-Sad-Form.png',
                'Sleep':  f'{GITHUB_BASE}/duck/Stage1-Sleep-Form.png',
            },
            2: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/duck/Stage2-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/duck/Stage2-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/duck/Stage2-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/duck/Stage2-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/duck/Stage2-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/duck/Stage2-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/duck/Stage2-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/duck/Stage2-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/duck/Stage2-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/duck/Stage2-Sleep-Form-Female.png',
                },
            },
            3: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/duck/Stage3-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/duck/Stage3-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/duck/Stage3-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/duck/Stage3-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/duck/Stage3-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/duck/Stage3-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/duck/Stage3-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/duck/Stage3-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/duck/Stage3-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/duck/Stage3-Sleep-Form-Female.png',
                },
            },
        }
    },

    'blackcat': {
        'starter': True,
        'name': 'Pisică Neagră', 'emoji': '🐱', 'button_label': '🐱 Pisică Neagră',
        'codes': {1: 'BLACKCAT-001', 2: 'BLACKCAT-002', 3: 'BLACKCAT-003'},
        'available_natures': ['shadow'],
        'entries': {
            1: {
                'code': 'BLACKCAT-001',
                'name': 'Pisicuță Neagră',
                'description': 'O pisică neagră misterioasă cu ochi ce strălucesc în întuneric. Natura Umbrei o face greu de detectat.',
                'lore': 'Născută din umbra lunii pline, această pisică poartă în ea secretele nopții. Ochii săi văd dincolo de aparențe, detectând magia ascunsă și intențiile ascunse ale celor din jur.\n\nEste tăcută, imprevizibilă și extrem de inteligentă. Aleargă prin umbre fără să lase urme și poate deveni aproape invizibilă în întuneric.',
            },
            2: {
                'code': 'BLACKCAT-002',
                'name': 'Pisică Neagră',
                'description': 'Stăpânește umbrele cu abilitate crescută. Se mișcă fără zgomot și poate dispărea din priviri.',
                'lore': 'Umbrele ascultă acum de voința sa. Poate crea iluzii întunecate și poate teleporta scurte distanțe prin umbra sa.\n\nPartenerii săi beneficiază de camuflaj în luptă, iar dușmanii se trezesc derutați de umbrele care par să se miște de unele singure.',
            },
            3: {
                'code': 'BLACKCAT-003',
                'name': 'Pisică Umbrelor',
                'description': 'Forma supremă a umbrei feline. Poate traversa întunericul și este imună la atacurile de cristal.',
                'lore': 'A atins forma în care granița dintre lumea fizică și tărâmul umbrelor devine fluidă. Poate traversa pereți prin umbra lor și este complet imună la atacurile de cristal.\n\nSe spune că această pisică poate chiar să fure umbrele dușmanilor, lăsându-i complet dezorientați și lipsiți de instinct de luptă.',
            },
        },
        'images': {
            1: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/blackcat/Stage1-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/blackcat/Stage1-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/blackcat/Stage1-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/blackcat/Stage1-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/blackcat/Stage1-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/blackcat/Stage1-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/blackcat/Stage1-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/blackcat/Stage1-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/blackcat/Stage1-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/blackcat/Stage1-Sleep-Form-Female.png',
                },
            },
            2: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/blackcat/Stage2-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/blackcat/Stage2-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/blackcat/Stage2-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/blackcat/Stage2-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/blackcat/Stage2-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/blackcat/Stage2-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/blackcat/Stage2-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/blackcat/Stage2-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/blackcat/Stage2-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/blackcat/Stage2-Sleep-Form-Female.png',
                },
            },
            3: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/blackcat/Stage3-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/blackcat/Stage3-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/blackcat/Stage3-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/blackcat/Stage3-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/blackcat/Stage3-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/blackcat/Stage3-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/blackcat/Stage3-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/blackcat/Stage3-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/blackcat/Stage3-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/blackcat/Stage3-Sleep-Form-Female.png',
                },
            },
        }
    },

    'dog': {
        'starter': True,
        'name': 'Câine', 'emoji': '🐶', 'button_label': '🐶 Câine',
        'codes': {1: 'DOG-001', 2: 'DOG-002', 3: 'DOG-003'},
        'available_natures': ['earth'],
        'entries': {
            1: {
                'code': 'DOG-001',
                'name': 'Cățeluș',
                'description': 'Un cățeluș loial și energic. Natura Pământului îi conferă o rezistență naturală la atacuri.',
                'lore': 'Cel mai loial dintre toți companionii, cățelușul de pământ este primul ales de mulți aventurieri. Energia sa este inepuizabilă, iar devotamentul față de stăpân este absolut.\n\nChiar și în această formă timpurie, pielea sa absoarbe loviturile cu o rezistență surprinzătoare, iar lătratele sale pot speria inamicii mai slabi.',
            },
            2: {
                'code': 'DOG-002',
                'name': 'Câine',
                'description': 'A crescut și a câștigat forță considerabilă. Un protector devotat cu apărare ridicată.',
                'lore': 'Acum un protector de temut, câinele de pământ poate crea bariere de piatră și pământ pentru a-și apăra stăpânul.\n\nForța sa fizică a crescut exponențial, iar mușcătura sa poate zdrobi armuri ușoare. Loialitatea sa transformă fiecare bătălie într-o misiune personală.',
            },
            3: {
                'code': 'DOG-003',
                'name': 'Câine Guardian',
                'description': 'Forma finală a gardianului de pământ. Imun la furtuni și capabil să respingă atacuri puternice.',
                'lore': 'Gardianul suprem al regatului. Această formă finală transformă câinele într-o fortăreață vie, imună la furtuni și capabilă să absoarbă atacuri magice puternice.\n\nPoare convoca terenul însuși în apărarea stăpânului, ridicând ziduri de piatră și creând cutremure locale. Un Câine Guardian lângă tine înseamnă că nu ești niciodată singur în fața pericolului.',
            },
        },
        'images': {
            1: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/dog/Stage1-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/dog/Stage1-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/dog/Stage1-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/dog/Stage1-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/dog/Stage1-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/dog/Stage1-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/dog/Stage1-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/dog/Stage1-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/dog/Stage1-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/dog/Stage1-Sleep-Form-Female.png',
                },
            },
            2: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/dog/Stage2-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/dog/Stage2-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/dog/Stage2-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/dog/Stage2-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/dog/Stage2-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/dog/Stage2-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/dog/Stage2-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/dog/Stage2-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/dog/Stage2-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/dog/Stage2-Sleep-Form-Female.png',
                },
            },
            3: {
                'male': {
                    'Basic':  f'{GITHUB_BASE}/dog/Stage3-Basic-Form-Male.png',
                    'Hungry': f'{GITHUB_BASE}/dog/Stage3-Hungry-Form-Male.png',
                    'Dirty':  f'{GITHUB_BASE}/dog/Stage3-Dirty-Form-Male.png',
                    'Sad':    f'{GITHUB_BASE}/dog/Stage3-Sad-Form-Male.png',
                    'Sleep':  f'{GITHUB_BASE}/dog/Stage3-Sleep-Form-Male.png',
                },
                'female': {
                    'Basic':  f'{GITHUB_BASE}/dog/Stage3-Basic-Form-Female.png',
                    'Hungry': f'{GITHUB_BASE}/dog/Stage3-Hungry-Form-Female.png',
                    'Dirty':  f'{GITHUB_BASE}/dog/Stage3-Dirty-Form-Female.png',
                    'Sad':    f'{GITHUB_BASE}/dog/Stage3-Sad-Form-Female.png',
                    'Sleep':  f'{GITHUB_BASE}/dog/Stage3-Sleep-Form-Female.png',
                },
            },
        }
    },
}
