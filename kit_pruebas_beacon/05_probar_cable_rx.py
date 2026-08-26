# Prueba electrica basica del camino de recepcion.
# No intenta decodificar AX.25 todavia.
# Requiere conectar RXD del MX614 al GPIO9 de la Pico.

from machine import Pin

try:
    from time import sleep_ms, sleep_us
except ImportError:
    from time import sleep

    def sleep_ms(value):
        sleep(value / 1000.0)

    def sleep_us(value):
        sleep(value / 1000000.0)

try:
    from lib.mx614 import MX614
except ImportError:
    from mx614 import MX614


def main():
    print("=== PRUEBA 5: ACTIVIDAD DEL CAMINO RX ===")
    print("Transmitir un paquete desde otra radio mientras esta prueba corre.")

    modem = MX614(
        txd_pin=8,
        rxd_pin=9,
        rdy_pin=10,
        det_pin=11,
        m0_pin=12,
        m1_pin=13,
    )

    if hasattr(modem, "set_rx_1200"):
        modem.set_rx_1200()
        print("Modo RX 1200 configurado")
    else:
        print("AVISO: MX614 no expone set_rx_1200(); usar la configuracion RX existente")

    rx_pin = Pin(9, Pin.IN)
    previous_rx = rx_pin.value()
    previous_det = modem.read_det()
    previous_rdy = modem.read_rdy()
    transitions = 0
    det_changes = 0
    elapsed_ms = 0

    print("Escuchando durante 20 segundos...")
    while elapsed_ms < 20000:
        current_rx = rx_pin.value()
        if current_rx != previous_rx:
            transitions += 1
            previous_rx = current_rx

        current_det = modem.read_det()
        if current_det != previous_det:
            print("DET cambio a:", current_det)
            det_changes += 1
            previous_det = current_det

        current_rdy = modem.read_rdy()
        if current_rdy != previous_rdy:
            print("RDY cambio a:", current_rdy)
            previous_rdy = current_rdy

        sleep_us(100)
        elapsed_ms += 0.1

    print("Transiciones observadas en RXD:", transitions)
    print("Cambios observados en DET:", det_changes)

    if transitions > 0 or det_changes > 0:
        print("RESULTADO FINAL: OK - se detecto actividad en RXD/DET")
        print("NOTA: esto prueba actividad electrica, no decodificacion AX.25 completa")
    else:
        print("RESULTADO FINAL: NO CONCLUYENTE - no hubo actividad")
        print("Revisar cable RX, tierra comun, modo del MX614 y señal de radio")


if __name__ == "__main__":
    main()
