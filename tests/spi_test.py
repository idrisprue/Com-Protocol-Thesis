from machine import Pin, SPI
import utime

# SPI setup
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, 
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))
cs = Pin(17, Pin.OUT, value=1)  # Chip Select (active low)
rst = Pin(14, Pin.OUT, value=1) # Reset

# SX1278 Registers
REG_VERSION = 0x42  # Version register

# Write to a register
def write_reg(reg, value):
    cs.value(0)
    spi.write(bytes([reg | 0x80]))  # Write bit set
    spi.write(bytes([value]))
    cs.value(1)

# Read from a register
def read_reg(reg):
    cs.value(0)
    spi.write(bytes([reg & 0x7F]))  # Read bit clear
    value = spi.read(1)[0]
    cs.value(1)
    return value

# Reset the module
rst.value(0)
utime.sleep_ms(10)
rst.value(1)
utime.sleep_ms(10)

# Test SPI by reading the version register
print("Testing SPI connection to SX1278...")
version = read_reg(REG_VERSION)
print(f"Version register (0x42) value: 0x{version:02X}")

if version == 0x12:
    print("SUCCESS: SX1278 detected (version 0x12). SPI is working!")
else:
    print("FAILURE: Expected 0x12, got something else. Check wiring or module.")