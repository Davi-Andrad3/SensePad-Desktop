import asyncio
import bleak
import logging
from core.ble_server import iniciar_servidor_ble
from config import SERVICE_UUID, CHAR_UUID

# Configuração visual do log para o terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("="*60)
    print("Iniciando Sensepad Desktop Server...")
    print("AVISO: Certifique-se de executar este terminal como ADMINISTRADOR")
    print("para que os comandos de mouse (ctypes) funcionem corretamente.")
    print("="*60)
    
    try:
        # Inicia o loop assíncrono do servidor BLE
        asyncio.run(iniciar_servidor_ble(SERVICE_UUID, CHAR_UUID))
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário (Ctrl+C).")
    except Exception as e:
        print(f"\nOcorreu um erro fatal: {e}")
    finally:
        print("\nO programa foi finalizado.")
        input("Pressione ENTER para fechar esta janela...")