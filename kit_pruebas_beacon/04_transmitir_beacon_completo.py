# Transmite un ciclo completo de beacon APRS/telemetria.
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


BIT_TIME_US = int(1000000 / 1200)
SOURCE = "UNCO-3"


def message(body):
    return ":" + SOURCE.ljust(9) + ":" + body


PAYLOADS = [
    ">PEHUENSAT 3",
    message("PARM.VOLTAGE,CURRENT,TEMP,RADIATION,CPU"),
    message("UNIT.V,mA,C,CPM,%"),
    message("EQNS.0,0.1,0,0,1,0,0,1,0,0,1,0,0,0.392,0"),
    message("BITS.11111111,PEHUENSAT 3"),
    "T#001,033,050,025,120,204,00000000",
]


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
    transmitter.start(build_levels(payload))
    while transmitter.is_active():
        transmitter.update()
        sleep_us(10)


def main():
    print("=== PRUEBA 4: BEACON APRS COMPLETO ===")
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

    for index, payload in enumerate(PAYLOADS):
        print("--- paquete", index + 1, "de", len(PAYLOADS), "---")
        transmit_once(transmitter, payload)
        sleep_ms(1000)

    print("RESULTADO LOCAL: ciclo completo transmitido")
    print("Revisar Direwolf para confirmar cada payload.")


if __name__ == "__main__":
    main()
