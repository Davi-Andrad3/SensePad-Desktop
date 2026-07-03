# ============================================================
# protocol.py
#
# Suporta todos os comandos do ConnectionService TypeScript:
#   CMD 1 → Mover mouse
#   CMD 2 → Clique esquerdo
#   CMD 3 → Clique direito
#   CMD 4 → Scroll vertical
#   CMD 5 → Tecla + modificadores
#   CMD 6 → Atalho por ID
# ============================================================

import struct
import logging
from core.windows_api import (
    mover_mouse,
    clique_esquerdo,
    clique_direito,
    scroll_vertical,
    pressionar_tecla,
    executar_atalho,
)

logger = logging.getLogger(__name__)

# ── Comandos (espelham CMD em ble-config.ts) ──────────────
CMD_MOVER_MOUSE     = 1
CMD_CLIQUE_ESQUERDO = 2
CMD_CLIQUE_DIREITO  = 3
CMD_SCROLL          = 4
CMD_TECLA           = 5
CMD_ATALHO          = 6

# ── Mapa de atalhos (ID → combinação de teclas) ──────────
# Mapeado num dicionário no Python para execução do CMD 6
SHORTCUT_MAP = {
    1: ('ctrl', 'c'),           # Copiar
    2: ('ctrl', 'v'),           # Colar
    3: ('ctrl', 'x'),           # Recortar
    4: ('ctrl', 'z'),           # Desfazer / Voltar
    5: ('ctrl', 'a'),           # Selecionar Tudo
    6: ('ctrl', 's'),           # Salvar
    7: ('ctrl', 'f'),           # Encontrar
    8: ('win', 'shift', 's'),   # Print
}

def processar_payload(dados_bytes: bytes):
    """
    Decodifica o payload recebido via Bluetooth e executa a ação.
    Roteia a execução de forma rápida e segura.
    Trata exceções localmente para evitar a queda do servidor em caso de pacotes inválidos.
    """
    if len(dados_bytes) == 0:
        return

    cmd = dados_bytes[0]

    try:
        if cmd == CMD_MOVER_MOUSE and len(dados_bytes) >= 3:
            dx, dy = struct.unpack('bb', dados_bytes[1:3])
            logger.info(f"Mouse MOVE: dx={dx}, dy={dy}")
            mover_mouse(dx, dy)

        elif cmd == CMD_CLIQUE_ESQUERDO:
            clique_esquerdo()
            logger.debug("Clique esquerdo")

        elif cmd == CMD_CLIQUE_DIREITO:
            clique_direito()
            logger.debug("Clique direito")

        elif cmd == CMD_SCROLL and len(dados_bytes) >= 2:
            dy, = struct.unpack('b', dados_bytes[1:2])
            scroll_vertical(dy)
            logger.debug(f"Scroll: {dy}")

        elif cmd == CMD_TECLA and len(dados_bytes) >= 3:
            keycode, modifiers = dados_bytes[1], dados_bytes[2]
            pressionar_tecla(keycode, modifiers)
            logger.debug(f"Tecla: keycode={keycode:#04x} mod={modifiers:#04x}")

        elif cmd == CMD_ATALHO and len(dados_bytes) >= 2:
            shortcut_id = dados_bytes[1]
            if shortcut_id in SHORTCUT_MAP:
                executar_atalho(*SHORTCUT_MAP[shortcut_id])
                logger.debug(f"Atalho {shortcut_id}: {SHORTCUT_MAP[shortcut_id]}")
            else:
                logger.warning(f"Atalho desconhecido: {shortcut_id}")

        else:
            logger.warning(f"Comando desconhecido: {cmd}. Dados: {dados_bytes.hex()}")

    except Exception as e:
        logger.error(f"Erro ao processar pacote: {e}. Dados: {dados_bytes.hex()}")