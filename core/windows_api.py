# ============================================================
# windows_api.py  (versão expandida)
#
# Adiciona scroll, teclado e atalhos ao conjunto original.
# Tudo via ctypes (SendInput para mouse, keybd_event para teclado).
# Sem dependências externas.
# ============================================================

import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURAÇÃO DAS ESTRUTURAS CTYPES PARA SENDINPUT (MOUSE) ---
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]

# Constantes da API de input do Windows
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002

# Virtual Key Codes para modificadores
VK_CONTROL = 0x11
VK_MENU = 0x12     # Alt
VK_SHIFT = 0x10
VK_LWIN = 0x5B

# Mapa de bits de modificadores (espelha o TypeScript)
MOD_CTRL = 0x01
MOD_ALT = 0x02
MOD_SHIFT = 0x04
MOD_WIN = 0x08

WHEEL_DELTA = 120  # Unidade padrão de scroll do Windows

# ============================================================
# WHITELIST DE KEYCODES  —  Segurança BLE
# ============================================================
# Apenas estes Virtual Key Codes podem ser enviados pelo
# dispositivo móvel via Bluetooth. Qualquer keycode fora
# desta lista é rejeitado antes de chegar ao kernel do Windows.
#
# Bloqueados explicitamente (não precisam constar aqui):
#   0x5B/0x5C  — Win (esquerda/direita)           | abertura de sistema
#   0x2C        — Print Screen                       | captura de tela
#   0x13        — Pause/Break                        | controle de sistema
#   0x2D        — Insert                             | modificação de buffer
#   0xA6– 0xB7  — Teclas de browser/mídia/volu me  | controle de SO
# ============================================================
VK_WHITELIST: frozenset[int] = frozenset({
    # Alfanuméricos: 0–9 e A–Z
    *range(0x30, 0x3A),   # 0x30–0x39  →  '0'–'9'
    *range(0x41, 0x5B),   # 0x41–0x5A  →  'A'–'Z'

    # Controle e edição
    0x08,  # Backspace
    0x09,  # Tab
    0x0D,  # Enter
    0x1B,  # Escape
    0x20,  # Space
    0x2E,  # Delete
    0x24,  # Home
    0x23,  # End
    0x21,  # Page Up
    0x22,  # Page Down

    # Teclas de seta
    0x25,  # Left
    0x26,  # Up
    0x27,  # Right
    0x28,  # Down

    # Funções F1–F12
    *range(0x70, 0x7C),   # 0x70–0x7B  →  F1–F12

    # Pontuação / símbolos comuns
    0xBC,  # Vírgula        ','
    0xBE,  # Ponto          '.'
    0xBD,  # Hífen          '-'
    0xBB,  # Igual          '='
    0xC1,  # Barra          '/'
    0xBA,  # Ponto-e-vírgula ';'
    0xDB,  # Colchete esq  '['
    0xDD,  # Colchete dir  ']'
    0xDC,  # Barra inver.  '\\'
    0xDE,  # Aspas simples  "'"
    0xC0,  # Acento grave   '`'
})

# --- FUNÇÕES PÚBLICAS ---

def mover_mouse(dx: int, dy: int):
    """Move o cursor de forma incremental e relativa à posição atual usando SendInput."""
    try:
        extra = ctypes.c_ulong(0)
        ii_ = INPUT_UNION()
        ii_.mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
        command = INPUT(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
    except Exception as e:
        logger.error(f"Erro ao mover mouse: {e}")

def clique_esquerdo():
    """Executa um clique esquerdo completo (down e up) usando SendInput."""
    try:
        extra = ctypes.c_ulong(0)
        
        ii_down = INPUT_UNION()
        ii_down.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
        cmd_down = INPUT(INPUT_MOUSE, ii_down)
        
        ii_up = INPUT_UNION()
        ii_up.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
        cmd_up = INPUT(INPUT_MOUSE, ii_up)
        
        input_array = (INPUT * 2)(cmd_down, cmd_up)
        ctypes.windll.user32.SendInput(2, input_array, ctypes.sizeof(INPUT))
    except Exception as e:
        logger.error(f"Erro no clique esquerdo: {e}")

def clique_direito():
    """Executa um clique direito completo (down e up) usando SendInput."""
    try:
        extra = ctypes.c_ulong(0)
        
        ii_down = INPUT_UNION()
        ii_down.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_RIGHTDOWN, 0, ctypes.pointer(extra))
        cmd_down = INPUT(INPUT_MOUSE, ii_down)
        
        ii_up = INPUT_UNION()
        ii_up.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_RIGHTUP, 0, ctypes.pointer(extra))
        cmd_up = INPUT(INPUT_MOUSE, ii_up)
        
        input_array = (INPUT * 2)(cmd_down, cmd_up)
        ctypes.windll.user32.SendInput(2, input_array, ctypes.sizeof(INPUT))
    except Exception as e:
        logger.error(f"Erro no clique direito: {e}")

def scroll_vertical(delta: int):
    """
    Scroll vertical com o mouse usando SendInput.
    No Windows, scroll para cima necessita de valor positivo (WHEEL_DELTA positivo),
    e para baixo de valor negativo (WHEEL_DELTA negativo).
    Como dy vem como delta de scroll (positivo para cima, negativo para baixo),
    multiplicamos diretamente por WHEEL_DELTA.
    """
    try:
        amount = delta * WHEEL_DELTA
        extra = ctypes.c_ulong(0)
        ii_ = INPUT_UNION()
        ii_.mi = MOUSEINPUT(0, 0, amount, MOUSEEVENTF_WHEEL, 0, ctypes.pointer(extra))
        command = INPUT(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
    except Exception as e:
        logger.error(f"Erro no scroll vertical: {e}")

def _key_down(vk: int):
    ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYDOWN, 0)

def _key_up(vk: int):
    ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def pressionar_tecla(keycode: int, modifiers: int = 0):
    """
    Pressiona uma tecla com modificadores opcionais.
    keycode  : código ASCII / Virtual Key (ex: ord('C') = 0x43)
    modifiers: bitmask — MOD_CTRL=0x01, MOD_ALT=0x02, MOD_SHIFT=0x04, MOD_WIN=0x08

    SEGURANÇA: keycode é validado contra VK_WHITELIST antes de qualquer sys-call.
    Keycodes não listados (teclas de sistema, Win, Print Screen, etc.) são
    descartados silenciosamente e registados como aviso no log.
    """
    # ── GUARD: Whitelist de keycodes ───────────────────────────────────
    if keycode not in VK_WHITELIST:
        logger.warning(
            f"[SEGURANÇA] Keycode bloqueado pela whitelist: {keycode:#04x} "
            f"(mod={modifiers:#04x}). Comando ignorado."
        )
        return
    # ───────────────────────────────────────────────────
    try:
        # Pressiona modificadores
        if modifiers & MOD_CTRL:  _key_down(VK_CONTROL)
        if modifiers & MOD_ALT:   _key_down(VK_MENU)
        if modifiers & MOD_SHIFT: _key_down(VK_SHIFT)
        if modifiers & MOD_WIN:   _key_down(VK_LWIN)

        # Pressiona a tecla principal
        _key_down(keycode)
        _key_up(keycode)

        # Solta modificadores (ordem inversa)
        if modifiers & MOD_WIN:   _key_up(VK_LWIN)
        if modifiers & MOD_SHIFT: _key_up(VK_SHIFT)
        if modifiers & MOD_ALT:   _key_up(VK_MENU)
        if modifiers & MOD_CTRL:  _key_up(VK_CONTROL)
    except Exception as e:
        logger.error(f"Erro ao pressionar tecla {keycode} com mod {modifiers}: {e}")

# Mapa de nome de tecla → Virtual Key Code
# Usado por executar_atalho() para aceitar strings legíveis
_VK_MAP = {
    'ctrl': VK_CONTROL, 'alt': VK_MENU, 'shift': VK_SHIFT, 'win': VK_LWIN,
    'tab': 0x09, 'enter': 0x0D, 'esc': 0x1B, 'backspace': 0x08,
    'delete': 0x2E, 'home': 0x24, 'end': 0x23,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'space': 0x20,
}

def executar_atalho(*teclas: str):
    """
    Executa uma combinação de teclas por nome.
    Exemplo: executar_atalho('ctrl', 'c')
             executar_atalho('alt', 'tab')
             executar_atalho('ctrl', 'shift', 'z')
    """
    # 🔒 BAIXA-2: Valida cada token contra a allowlist de teclas conhecidas.
    # O fallback `ord(k_lower.upper())` pode resolver qualquer caractere ASCII,
    # incluindo teclas de sistema (0x5B=Win, 0x00=NUL, etc.) se uma entrada
    # desconhecida for passada. A allowlist rejeita a combinação inteira se
    # qualquer tecla não estiver explicitamente mapeada, prevenindo comandos
    # não intencionais mesmo que o SHORTCUT_MAP seja expandido no futuro.
    TECLAS_PERMITIDAS: set[str] = (
        set(_VK_MAP.keys()) |
        # Letras a–z
        {chr(c) for c in range(ord('a'), ord('z') + 1)} |
        # Dígitos 0–9
        {str(d) for d in range(10)}
    )

    for t in teclas:
        if t.lower() not in TECLAS_PERMITIDAS:
            logger.warning(
                f"[SEGURANÇA] Tecla '{t}' bloqueada em executar_atalho(): "
                f"não está na allowlist. Combinação inteira rejeitada."
            )
            return  # Rejeita a combinação completa — nenhuma tecla é pressionada

    try:
        MODIFICADORES = {'ctrl', 'alt', 'shift', 'win'}
        mods = [t for t in teclas if t.lower() in MODIFICADORES]
        main_keys = [t for t in teclas if t.lower() not in MODIFICADORES]

        # Pressiona modificadores
        for m in mods:
            _key_down(_VK_MAP[m.lower()])

        # Pressiona e solta cada tecla principal
        for k in main_keys:
            k_lower = k.lower()
            vk = _VK_MAP.get(k_lower, ord(k_lower.upper()))
            _key_down(vk)
            _key_up(vk)

        # Solta modificadores (ordem inversa)
        for m in reversed(mods):
            _key_up(_VK_MAP[m.lower()])
    except Exception as e:
        logger.error(f"Erro ao executar atalho {teclas}: {e}")