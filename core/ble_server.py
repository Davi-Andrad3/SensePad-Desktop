import asyncio
import logging
import uuid as _uuid_mod

from winrt.windows.devices.bluetooth.genericattributeprofile import (
    GattServiceProvider,
    GattServiceProviderAdvertisingParameters,
    GattLocalCharacteristicParameters,
    GattCharacteristicProperties,
    GattProtectionLevel,
)
from winrt.windows.storage.streams import DataReader

from core.protocol import processar_payload
from config import SERVER_NAME, SERVICE_UUID, CHAR_UUID

logger = logging.getLogger(__name__)


def _ler_ibuffer(ibuffer) -> bytes:
    """Lê todos os bytes de um IBuffer WinRT."""
    reader = DataReader.from_buffer(ibuffer)
    count = ibuffer.length
    
    # 1. Cria um array de bytes vazio com o tamanho exato da mensagem
    buffer_vazio = bytearray(count)
    
    # 2. Pede ao leitor para preencher esse espaço vazio com os dados recebidos
    reader.read_bytes(buffer_vazio)
    
    # 3. Converte e devolve o resultado final
    return bytes(buffer_vazio)


async def iniciar_servidor_ble(service_uuid: str, char_uuid: str):

    loop = asyncio.get_running_loop()

    # ── 1. Cria o Serviço GATT ──────────────────────────────
    logger.info("Criando serviço GATT...")
    resultado_servico = await GattServiceProvider.create_async(
        _uuid_mod.UUID(service_uuid)
    )

    if resultado_servico.error != 0:
        logger.error(f"Falha ao criar serviço GATT. Código de erro: {resultado_servico.error}")
        logger.error("Verifique se o Bluetooth está ligado e se o terminal está como Administrador.")
        return

    service_provider = resultado_servico.service_provider

    # ── 2. Define a Característica de Escrita ───────────────
    params = GattLocalCharacteristicParameters()
    # Restaurado WRITE_WITHOUT_RESPONSE para permitir o envio de alta frequência do mouse
    params.characteristic_properties = (
        GattCharacteristicProperties.WRITE
        | GattCharacteristicProperties.WRITE_WITHOUT_RESPONSE
        | GattCharacteristicProperties.READ
    )
    # SEGURANÇA: Força o emparelhamento nativo do Windows antes de aceitar dados.
    # Um dispositivo não pareado não consegue nem ler nem escrever na característica.
    # O utilizador verá o diálogo de PIN/confirmação do Windows na primeira ligação.
    params.read_protection_level  = GattProtectionLevel.ENCRYPTION_AND_AUTHENTICATION_REQUIRED
    params.write_protection_level = GattProtectionLevel.ENCRYPTION_AND_AUTHENTICATION_REQUIRED

    resultado_char = await service_provider.service.create_characteristic_async(
        _uuid_mod.UUID(char_uuid), params
    )

    if resultado_char.error != 0:
        logger.error(f"Falha ao criar característica. Código de erro: {resultado_char.error}")
        return

    characteristic = resultado_char.characteristic

    # ── 3. Registra o Callback de Escrita ───────────────────
    def on_write_requested(sender, args):
        deferral = args.get_deferral()

        async def _processar():
            try:
                request = await args.get_request_async()
                if request is None:
                    return
                dados_bytes = _ler_ibuffer(request.value)
                processar_payload(dados_bytes)
                request.respond()
            except Exception as e:
                logger.error(f"Erro ao processar requisição BLE: {e}")
            finally:
                deferral.complete()

        asyncio.run_coroutine_threadsafe(_processar(), loop)

    characteristic.add_write_requested(on_write_requested)

    # ── 4. Inicia o Advertising ─────────────────────────────
    # No winrt 3.2.1, start_advertising() não aceita parâmetros.
    # Os defaults já são: is_connectable=True, is_discoverable=True.
# ── 4. Inicia o Advertising ─────────────────────────────
    adv_parameters = GattServiceProviderAdvertisingParameters()
    adv_parameters.is_discoverable = True
    adv_parameters.is_connectable = True

    service_provider.start_advertising_with_parameters(adv_parameters)
    # ── 5. Mantém o servidor rodando ────────────────────────
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        service_provider.stop_advertising()
        logger.info("Servidor BLE encerrado.")
