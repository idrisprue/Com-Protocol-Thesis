"""Servidor AX.25 conectado para responder a EasyTerm.

El programa escucha en RXD del MX614 y responde automáticamente:

    SABME -> UA
    SABM  -> UA
    I     -> RR
    DISC  -> UA

Después de recibir una trama I, muestra su payload. La captura se hace en
ventanas cortas para que la respuesta llegue dentro del tiempo de espera de la
estación remota.
"""

from machine import Pin
import gc

try:
    from time import ticks_diff, ticks_ms, ticks_us
except ImportError:
    from time import monotonic_ns

    def ticks_us():
        return monotonic_ns() // 1000

    def ticks_ms():
        return monotonic_ns() // 1000000

    def ticks_diff(new_ticks, old_ticks):
        return new_ticks - old_ticks

try:
    from lib.ax25_connected import Ax25ConnectedEndpoint, frame_to_nrzi_levels
    from lib.ax25_rx import decode_samples
    from lib.mx614 import MX614
    from lib.transmitter import NonBlockingBitTransmitter
except ImportError:
    from ax25_connected import Ax25ConnectedEndpoint, frame_to_nrzi_levels
    from ax25_rx import decode_samples
    from mx614 import MX614
    from transmitter import NonBlockingBitTransmitter


BIT_RATE = 1200
SAMPLES_PER_BIT = 8
SAMPLE_PERIOD_US = int(1000000 / (BIT_RATE * SAMPLES_PER_BIT))
WAIT_FOR_DET_MS = 5000
CAPTURE_WINDOW_MS = 700
DET_ACTIVE_LEVEL = 1
BIT_TIME_US = int(1000000 / BIT_RATE)

LOCAL_CALLSIGN = "NQNGND"
LOCAL_SSID = 0


def capture_one_frame(modem):
    """Captura una ventana corta de RXD después de detectar actividad."""
    deadline = ticks_ms() + WAIT_FOR_DET_MS
    while modem.read_det() != DET_ACTIVE_LEVEL:
        if ticks_diff(ticks_ms(), deadline) >= 0:
            return bytearray()

    max_samples = (CAPTURE_WINDOW_MS * BIT_RATE * SAMPLES_PER_BIT) // 1000
    gc.collect()
    samples = bytearray(max_samples)
    sample_count = 0
    next_tick = ticks_us()
    end_tick = next_tick + CAPTURE_WINDOW_MS * 1000
    rx_pin = Pin(9, Pin.IN)

    while ticks_diff(ticks_us(), end_tick) < 0 and sample_count < max_samples:
        while ticks_diff(ticks_us(), next_tick) < 0:
            pass
        samples[sample_count] = rx_pin.value()
        sample_count += 1
        next_tick += SAMPLE_PERIOD_US

    return samples[:sample_count]


def transmit_frame(modem, frame):
    """Transmite una respuesta AX.25 por TXD y espera a que termine."""
    levels = frame_to_nrzi_levels(frame, preamble_flags=20, postamble_flags=3)
    transmitter = NonBlockingBitTransmitter(modem.set_txd, BIT_TIME_US)
    transmitter.start(levels)
    while transmitter.is_active():
        transmitter.update()
    modem.set_txd(1)


def payload_as_text(payload):
    try:
        return payload.decode("ascii")
    except UnicodeError:
        return "<binario: {} bytes>".format(len(payload))


def main():
    print("=== AX.25 CONECTADO: RESPONDEDOR PARA EASYTERM ===")
    print("La Pico espera SABME/SABM y responde UA automaticamente")
    print("Estacion local:", LOCAL_CALLSIGN + "-" + str(LOCAL_SSID))

    modem = MX614(
        txd_pin=8,
        rxd_pin=9,
        rdy_pin=10,
        det_pin=11,
        m0_pin=12,
        m1_pin=13,
    )
    modem.set_rx_1200()
    endpoint = Ax25ConnectedEndpoint(LOCAL_CALLSIGN, LOCAL_SSID)

    while True:
        samples = capture_one_frame(modem)
        if not samples:
            print("Sin actividad DET; esperando otra trama...")
            continue

        frames = decode_samples(
            samples,
            initial_level=1,
            samples_per_bit=SAMPLES_PER_BIT,
        )
        if not frames:
            print("Señal detectada, pero no se encontró una trama AX.25 válida")
            continue

        for frame in frames:
            try:
                event, responses, payload = endpoint.handle_frame(frame)
            except Exception as error:
                print("Trama descartada:", error)
                continue

            print("FCS: OK")
            print("ORIGEN:", endpoint.remote_callsign, "-", endpoint.remote_ssid)
            print("EVENTO:", event)
            if payload:
                print("PAYLOAD:", payload_as_text(payload))

            for response in responses:
                print("Transmitiendo respuesta AX.25...")
                transmit_frame(modem, response)
                print("Respuesta transmitida")


if __name__ == "__main__":
    main()
