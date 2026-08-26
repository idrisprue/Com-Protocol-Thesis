"""Receive and decode one AX.25 frame using the MX614 RX path.

Run this on the Raspberry Pi Pico while another station transmits the known
test packet. The program captures RXD, decodes NRZI/bit-stuffing and validates
the AX.25 FCS.
"""

from machine import Pin

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
    from lib.mx614 import MX614
    from lib.ax25_rx import decode_samples, parse_ui_frame
except ImportError:
    from mx614 import MX614
    from ax25_rx import decode_samples, parse_ui_frame


BIT_RATE = 1200
SAMPLES_PER_BIT = 8
SAMPLE_PERIOD_US = int(1000000 / (BIT_RATE * SAMPLES_PER_BIT))
CAPTURE_TIMEOUT_MS = 5000
DET_ACTIVE_LEVEL = 1


def capture_samples(modem):
    """Capture RXD while DET indicates received energy."""
    print("Esperando DET activo...")
    deadline = ticks_ms() + CAPTURE_TIMEOUT_MS
    while modem.read_det() != DET_ACTIVE_LEVEL:
        if ticks_diff(ticks_ms(), deadline) >= 0:
            return []

    print("DET activo: capturando RXD")
    samples = []
    next_tick = ticks_us()
    end_tick = next_tick + (CAPTURE_TIMEOUT_MS * 1000)
    rx_pin = Pin(9, Pin.IN)

    while ticks_diff(ticks_us(), end_tick) < 0:
        while ticks_diff(ticks_us(), next_tick) < 0:
            pass
        samples.append(rx_pin.value())
        next_tick += SAMPLE_PERIOD_US

    return samples


def main():
    print("=== RECEPCION AX.25 CON MX614 ===")
    print("Transmitir desde otra radio el paquete de prueba durante esta ejecucion:")
    print("T#001,033,050,025,120,204,00000000")

    modem = MX614(
        txd_pin=8,
        rxd_pin=9,
        rdy_pin=10,
        det_pin=11,
        m0_pin=12,
        m1_pin=13,
    )
    modem.set_rx_1200()

    samples = capture_samples(modem)
    print("Muestras capturadas:", len(samples))
    if not samples:
        print("RESULTADO: NO CONCLUYENTE - no se activo DET")
        return

    frames = decode_samples(samples, initial_level=1, samples_per_bit=SAMPLES_PER_BIT)
    if not frames:
        print("RESULTADO: ERROR - no se encontro una trama AX.25 con FCS valido")
        print("Revisar CLK del MX614, modo RX, audio de entrada, fase de muestreo y cableado")
        return

    try:
        packet = parse_ui_frame(frames[0])
        payload = packet["information"].decode("ascii")
    except Exception as error:
        print("RESULTADO: ERROR - trama encontrada pero no se pudo interpretar:", error)
        return

    print("FCS: OK")
    print("ORIGEN:", packet["source"] + "-" + str(packet["source_ssid"]))
    print("DESTINO:", packet["destination"] + "-" + str(packet["destination_ssid"]))
    print("PAYLOAD:", payload)
    print("RESULTADO: OK - recepcion y decodificacion AX.25 correctas")


if __name__ == "__main__":
    main()
