import utime
from machine import Pin, SPI

class SX1278:
    # Register map
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

    def __init__(self, spi, cs_pin, rst_pin, dio0_pin):
        self.spi = spi
        self.cs = cs_pin
        self.rst = rst_pin
        self.dio0 = dio0_pin
        self.tx_done = True # Global state
        self._reset()
        self._init_registers()

    def _write_reg(self, reg, value):
        self.cs.value(0)
        self.spi.write(bytes([reg | 0x80]))
        self.spi.write(bytes([value]))
        self.cs.value(1)

    def _read_reg(self, reg):
        self.cs.value(0)
        self.spi.write(bytes([reg & 0x7F]))
        val = self.spi.read(1)[0]
        self.cs.value(1)
        return val

    def _reset(self): # Reset the module
        self.rst.value(0)
        utime.sleep_ms(10)
        self.rst.value(1)
        utime.sleep_ms(10)

    def _init_registers(self):

        # Enter standby mode
        self._write_reg(self.REG_OP_MODE, 0x00)
        utime.sleep_ms(10)
        self._write_reg(self.REG_OP_MODE, 0x01)
        self._write_reg(self.REG_IRQ_FLAGS, 0xFF)

        print(f"[{utime.time()}] Module initialized: SX1278 in FSK Standby Mode (Op Mode: 0x{self._read_reg(self.REG_OP_MODE):02X})")

        # RF Frequency: F_rf = FRF / (2^19) * F_xtal
        # F_xtal = 32 MHz → default crystal frequency
        # So la cuentita es algo asi: FRF = (435000000 * 2^19) / 32_000_000 = 3548778 → 0x3627AA
        
        self._write_reg(self.REG_FR_MSB, 0x36)
        self._write_reg(self.REG_FR_MID, 0x27)
        self._write_reg(self.REG_FR_LSB, 0xAA)
        print(f"[{utime.time()}] Carrier frequency configured: 435.000 MHz")

        # Bitrate: 1200 bps
        self._write_reg(self.REG_BITRATE_MSB, 0x68)
        self._write_reg(self.REG_BITRATE_LSB, 0x3A)
        print(f"[{utime.time()}] Modulation bitrate set: 1200 bps")

        # FSK deviation: 2.5 kHz
        self._write_reg(self.REG_FDEV_MSB, 0x00)
        self._write_reg(self.REG_FDEV_LSB, 0x28)
        print(f"[{utime.time()}] FSK deviation configured: 2.5 kHz")

        # TX Power: 14 dBm
        self._write_reg(self.REG_PA_CONFIG, 0x84)
        print(f"[{utime.time()}] RF output power set: 14 dBm")

        # Packet config
        self._write_reg(self.REG_FIFO_TX_BASE_ADDR, 0x00)
        self._write_reg(self.REG_PACKET_CONFIG1, 0x00)
        self._write_reg(self.REG_PACKET_CONFIG2, 0x40)
        print(f"[{utime.time()}] Packet configuration: Variable length packets, FSK mode")

        # Map DIO0 to TX done
        self._write_reg(self.REG_DIO_MAPPING_1, 0x00)

    def send(self, packet: bytes):
        self.tx_done = False
        self._write_reg(self.REG_FIFO_ADDR_PTR, 0x00)
        self._write_reg(self.REG_PAYLOAD_LENGTH, len(packet))

        self.cs.value(0)
        self.spi.write(bytes([self.REG_FIFO | 0x80]))
        self.spi.write(packet)
        self.cs.value(1)

        self._write_reg(self.REG_OP_MODE, 0x03)  # Transmit mode

    def poll_tx_done(self):
        irq_flags = self._read_reg(self.REG_IRQ_FLAGS)
        if (irq_flags & 0x08) and not self.tx_done:
            self._write_reg(self.REG_IRQ_FLAGS, 0x08)
            self._write_reg(self.REG_OP_MODE, 0x01)  # Back to standby
            self.tx_done = True
            return True
        return False
