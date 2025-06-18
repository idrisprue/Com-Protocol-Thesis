from machine import Pin, SPI
import utime
import ax25

#Me escucho desviada 175Khz

# SPI setup
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, 
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))
cs = Pin(17, Pin.OUT, value=1)
rst = Pin(14, Pin.OUT, value=1)
dio0 = Pin(15, Pin.IN)

# SX1278 Registers
REG_OP_MODE = 0x01
REG_FR_MSB = 0x06
REG_FR_MID = 0x07
REG_FR_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_FIFO = 0x00
REG_FIFO_ADDR_PTR = 0x0D
REG_FIFO_TX_BASE_ADDR = 0x0E
REG_PAYLOAD_LENGTH = 0x22
REG_BITRATE_MSB = 0x02
REG_BITRATE_LSB = 0x03
REG_FDEV_MSB = 0x04
REG_FDEV_LSB = 0x05
REG_DIO_MAPPING_1 = 0x40
REG_IRQ_FLAGS = 0x12
REG_PACKET_CONFIG1 = 0x1F
REG_PACKET_CONFIG2 = 0x20

# Global state
tx_done = True

def write_reg(reg, value):
    cs.value(0)
    spi.write(bytes([reg | 0x80]))
    spi.write(bytes([value]))
    cs.value(1)

def read_reg(reg):
    cs.value(0)
    spi.write(bytes([reg & 0x7F]))
    value = spi.read(1)[0]
    cs.value(1)
    return value

# Reset the module
rst.value(0)
utime.sleep_ms(10)
rst.value(1)
utime.sleep_ms(10)

# Configure FSK mode
write_reg(REG_OP_MODE, 0x00)
utime.sleep_ms(10)
write_reg(REG_OP_MODE, 0x01)
write_reg(REG_IRQ_FLAGS, 0xFF)
print(f"[{utime.time()}] Module initialized: SX1278 in FSK Standby Mode (Op Mode: 0x{read_reg(REG_OP_MODE):02X})")

write_reg(REG_FR_MSB, 0x6C)
write_reg(REG_FR_MID, 0xCC)
write_reg(REG_FR_LSB, 0xCC)
print(f"[{utime.time()}] Carrier frequency configured: 435.000 MHz")

write_reg(REG_BITRATE_MSB, 0x68)
write_reg(REG_BITRATE_LSB, 0x3A)
print(f"[{utime.time()}] Modulation bitrate set: 1200 bps")

write_reg(REG_FDEV_MSB, 0x00)
write_reg(REG_FDEV_LSB, 0x28)  # 2.5 kHz deviation
print(f"[{utime.time()}] FSK deviation configured: 2.5 kHz")

write_reg(REG_PA_CONFIG, 0x84)
print(f"[{utime.time()}] RF output power set: 14 dBm")

write_reg(REG_FIFO_TX_BASE_ADDR, 0x00)

write_reg(REG_PACKET_CONFIG1, 0x00)
write_reg(REG_PACKET_CONFIG2, 0x40)
print(f"[{utime.time()}] Packet configuration: Variable length packets, FSK mode")

write_reg(REG_DIO_MAPPING_1, 0x00)

# Send an AX.25 message
def send_message(message, dest="DA1", source="P123"):
    global tx_done
    tx_done = False
    
    ax25_packet = ax25.AX25(dest, source, message.encode('utf-8'))
    packet = ax25_packet.create_frame()
    crc = ax25_packet.crc_calculator.calculate(ax25_packet.dest_address + ax25_packet.source_address + ax25_packet.control + ax25_packet.pid + ax25_packet.payload)
    
    write_reg(REG_FIFO_ADDR_PTR, 0x00)
    write_reg(REG_PAYLOAD_LENGTH, len(packet))
    
    cs.value(0)
    spi.write(bytes([REG_FIFO | 0x80]))
    spi.write(packet)
    cs.value(1)
    
    print(f"[{utime.time()}] TX comienza: {message[:20]}... | DEST: {dest} | SRC: {source} | Length: {len(packet)} bytes | CRC: 0x{crc:04X}")
    write_reg(REG_OP_MODE, 0x03)

# Main loop
print(f"[{utime.time()}] Starting AX.25 FSK transmission: 435 MHz, 1200 bps, 3-second beacon interval")
counter = 0
last_tx_time = utime.ticks_ms()
tx_interval = 3000  # Adjusted to 4s to fit 3x ~1s bursts + gaps

while True:
    current_time = utime.ticks_ms()
    elapsed = current_time - last_tx_time
    
    if elapsed >= tx_interval and tx_done:
        message = f"Test {counter} - mensajito a ver si funciona con esto para probar con Ax.25 y el handy test test test " + "X" * 55
        for _ in range(3):  # Three ~1s bursts
            send_message(message, dest="DA1", source="P123")
            utime.sleep_ms(150)  # 150 ms gap between bursts
        counter += 1
        last_tx_time = current_time
    
    # Polling
    irq_flags = read_reg(REG_IRQ_FLAGS)
    if (irq_flags & 0x08) and not tx_done:
        tx_done = True
        write_reg(REG_IRQ_FLAGS, 0x08)
        write_reg(REG_OP_MODE, 0x01)
        print(f"[{utime.time()}] TX completado: Test {counter-1} enviado correctamente! ALEGRÍA")
    
    utime.sleep_ms(10)