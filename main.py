from machine import Pin, SPI
import utime
import ax25
from sx1278 import SX1278  # Clase separada para manejo del chip asi puedo mofidicar todo y modularizar

# Configuración de la interfaz SPI y pines de control
spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))
cs = Pin(17, Pin.OUT, value=1)
rst = Pin(14, Pin.OUT, value=1)
dio0 = Pin(15, Pin.IN)

# Inicializar objeto SX1278 en modo FSK
radio = SX1278(spi=spi, cs_pin=cs, rst_pin=rst, dio0_pin=dio0)

print(f"[{utime.time()}] Starting AX.25 FSK transmission: 435 MHz, 1200 bps, 3-second beacon interval")
counter = 0
last_tx_time = utime.ticks_ms()
tx_interval = 3000  # Intervalo de transmisión en milisegundos

# Main loop
while True:
    current_time = utime.ticks_ms()
    elapsed = current_time - last_tx_time

    if elapsed >= tx_interval and radio.tx_done:
        message = f"Test {counter} - mensajito a ver si funciona con esto para probar con Ax.25 y el handy test test test " + "X" * 55 #lo repito asi puedo alcanzar a escuchar el tono en el handy
        for _ in range(3):  # Tres ráfagas con 150 ms entre ellas
            ax25_frame = ax25.AX25("DA1", "P123", message.encode('utf-8'))
            packet = ax25_frame.create_frame()
            crc = ax25_frame.crc_calculator.calculate(
                ax25_frame.dest_address + ax25_frame.source_address + ax25_frame.control + ax25_frame.pid + ax25_frame.payload
            )
            radio.send(packet)
            print(f"[{utime.time()}] TX comienza: {message[:20]}... | DEST: DA1 | SRC: P123 | Length: {len(packet)} bytes | CRC: 0x{crc:04X}")
            utime.sleep_ms(150)
        counter += 1
        last_tx_time = current_time

    if radio.poll_tx_done():
        print(f"[{utime.time()}] TX completado: Test {counter-1} enviado correctamente! ALEGRÍA")

    utime.sleep_ms(10)
