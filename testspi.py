from machine import Pin, SPI
import utime

# Code to test de SPI
# Setup de SPI
spi = SPI(0, baudrate=5000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
cs = Pin(17, Pin.OUT)

# NOTES ON THE SPI: el baudrate es en realidad el rate del SCLK: max rate 10 MHz

# Función para escribir un registo
def write_register(register, value):
    cs.value(0)  # Selecciono el dispositivo al que voy a escribir
    spi.write(bytearray([register | 0x80]))  # Poner R/W a 1 para indicar escritura
    spi.write(bytearray([value])) # Escribo la data
    cs.value(1)  # Deselect the device

# Function to read from a register
def read_register(register):
    cs.value(0)  # Selecciono a que dispositivo voy a leer
    spi.write(bytearray([register & 0x7F]))  # Poner R/W a 0 para indicar escritura
    result = spi.read(1) # Uso la funcion de la class de SPI para leer y lo storeo en result
    cs.value(1)  # Deselect the device
    return result[0]

# Config para inicializar el módulo Si4432
def initialize_si4432():
    print("Inicializando SI4432...")

    write_register(0x75, 0x53)  # Selección de banda (435 MHz)
    write_register(0x76, 0x7D)  # Frecuencia nominal (alto)
    write_register(0x77, 0x00)  # Frecuencia nominal (bajo)

    # Configuración de la velocidad de datos a 9600 baudios
    write_register(0x6E, 0x27)  # TX Data Rate 1
    write_register(0x6F, 0x52)  # TX Data Rate 0

    # Configuración de modulación
    write_register(0x70, 0x20)  # Control de modulación 1 (FSK)
    write_register(0x71, 0x23)  # Control de modulación 2 (datos sin codificación, CRC habilitado)

    print("Configuración completada.")


# Test the initialization and reading
def test_si4432():
    initialize_si4432()
    utime.sleep(1)  # Wait a bit for the settings to take effect
    
    # Verify by reading back the registers
    print(f"Reg 0x75: {read_register(0x75):02X}")
    print(f"Reg 0x76: {read_register(0x76):02X}")
    print(f"Reg 0x77: {read_register(0x77):02X}")
    print(f"Reg 0x6E: {read_register(0x6E):02X}")
    print(f"Reg 0x6F: {read_register(0x6F):02X}")
    print(f"Reg 0x70: {read_register(0x70):02X}")
    print(f"Reg 0x71: {read_register(0x71):02X}")

# Run the test
test_si4432()