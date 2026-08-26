# Transmite un unico paquete APRS conocido para probar con Direwolf.
# Requiere la carpeta lib/ del proyecto.

try:
    from lib.ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
    from lib.mx614 import MX614
    from lib.transmitter import NonBlockingBitTransmitter
except ImportError:
    from ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
    from mx614 import MX614
    from transmitter import NonBlockingBitTransmitter

try:
    from time import sleep_ms, sleep_us
except ImportError:
    from time import sleep

    def sleep_ms(value):
        sleep(value / 1000.0)

    def sleep_us(value):
        sleep(value / 1000000.0)


BIT_RATE_BPS = 1200
BIT_TIME_US = int(1000000 / BIT_RATE_BPS)
PAYLOAD = "T#001,033,050,025,120,204,00000000"


def build_levels(payload):
    frame = make_ui_frame(
        destination="NQNGND",
        dest_ssid=0,
        source="UNCO",
        source_ssid=3,
        payload=payload.encode("ascii"),
    )
    bits = make_ax25_bitstream(frame, preamble_flags=20, postamble_flags=3)
    return nrzi_encode(bits, initial_level=1)


def transmit_once(transmitter, payload):
    print("TRANSMITIENDO:", payload)
    levels = build_levels(payload)
    transmitter.start(levels)
    while transmitter.is_active():
        transmitter.update()
        sleep_us(10)
    print("TX SOFTWARE COMPLETADA")


def main():
    print("=== PRUEBA 3: TRANSMISION DE UN PAQUETE ===")
    print("Iniciar Direwolf antes de continuar.")

    modem = MX614(
        txd_pin=8,
        rxd_pin=9,
        rdy_pin=10,
        det_pin=11,
        m0_pin=12,
        m1_pin=13,
    )
    modem.set_tx_1200()
    transmitter = NonBlockingBitTransmitter(modem.set_txd, BIT_TIME_US)

    for number in range(1, 4):
        print("--- repeticion", number, "de 3 ---")
        transmit_once(transmitter, PAYLOAD)
        if number < 3:
            sleep_ms(3000)

    print("RESULTADO LOCAL: TX terminada sin errores de software")
    print("RESULTADO REAL: mirar Direwolf")
    print("Esperado: UNCO-3>NQNGND:" + PAYLOAD)


if __name__ == "__main__":
    main()
