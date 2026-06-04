"""Root-level compatibility copy for Pico sync tools.

Some MicroPico sync flows flatten `lib/` into the filesystem root on the Pico.
Keeping this module at the repository root lets `main.py` and bench tests fall
back cleanly when that happens.
"""


FLAG_BYTE = 0x7E
CONTROL_UI = 0x03
PID_NO_LAYER_3 = 0xF0


def _pad_callsign(callsign):
    normalized = callsign.upper()[:6]
    while len(normalized) < 6:
        normalized += " "
    return normalized


def ax25_address(callsign, ssid, last=False):
    if not isinstance(callsign, str):
        raise TypeError("callsign must be a string")
    if not isinstance(ssid, int):
        raise TypeError("ssid must be an integer")
    if ssid < 0 or ssid > 15:
        raise ValueError("ssid must be in range 0..15")

    normalized = _pad_callsign(callsign)
    encoded = bytearray()

    for char in normalized:
        encoded.append(ord(char) << 1)

    ssid_byte = 0x60 | ((ssid & 0x0F) << 1)
    if last:
        ssid_byte |= 0x01
    encoded.append(ssid_byte)

    return bytes(encoded)


def ax25_fcs(data):
    crc = 0xFFFF

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1

    crc ^= 0xFFFF
    return bytes((crc & 0xFF, (crc >> 8) & 0xFF))


def make_ui_frame(destination, dest_ssid, source, source_ssid, payload):
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("payload must be bytes or bytearray")

    frame = bytearray()
    frame.extend(ax25_address(destination, dest_ssid, last=False))
    frame.extend(ax25_address(source, source_ssid, last=True))
    frame.append(CONTROL_UI)
    frame.append(PID_NO_LAYER_3)
    frame.extend(payload)
    frame.extend(ax25_fcs(frame))
    return bytes(frame)


def byte_to_bits_lsb_first(byte):
    return [(byte >> bit_index) & 0x01 for bit_index in range(8)]


def bytes_to_bits_lsb_first(data):
    bits = []
    for byte in data:
        bits.extend(byte_to_bits_lsb_first(byte))
    return bits


def bit_stuff(bits):
    stuffed = []
    consecutive_ones = 0

    for bit in bits:
        stuffed.append(bit)
        if bit == 1:
            consecutive_ones += 1
            if consecutive_ones == 5:
                stuffed.append(0)
                consecutive_ones = 0
        else:
            consecutive_ones = 0

    return stuffed


def make_ax25_bitstream(frame, preamble_flags=20, postamble_flags=3):
    if preamble_flags < 0 or postamble_flags < 0:
        raise ValueError("flag counts must be non-negative")

    flag_bits = byte_to_bits_lsb_first(FLAG_BYTE)
    body_bits = bytes_to_bits_lsb_first(frame)
    stuffed_body_bits = bit_stuff(body_bits)

    bitstream = []
    for _ in range(preamble_flags):
        bitstream.extend(flag_bits)
    bitstream.extend(stuffed_body_bits)
    for _ in range(postamble_flags):
        bitstream.extend(flag_bits)
    return bitstream


def nrzi_encode(bits, initial_level=1):
    level = 1 if initial_level else 0
    levels = []

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("bits must contain only 0 or 1")
        if bit == 0:
            level ^= 1
        levels.append(level)

    return levels
