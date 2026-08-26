"""Funciones auxiliares AX.25 para validar la tesis.

Las funciones de este módulo no dependen del hardware. Así, los pasos del
protocolo se pueden probar fácilmente en CPython y explicar en la tesis.
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
    """Codifica una entrada del campo de direcciones AX.25."""
    if not isinstance(callsign, str):
        raise TypeError("callsign debe ser un texto")
    if not isinstance(ssid, int):
        raise TypeError("ssid debe ser un entero")
    if ssid < 0 or ssid > 15:
        raise ValueError("ssid debe estar entre 0 y 15")

    normalized = _pad_callsign(callsign)
    encoded = bytearray()

    for char in normalized:
        encoded.append(ord(char) << 1)

    # Los bits 5 y 6 se establecen según el formato de direcciones AX.25.
    ssid_byte = 0x60 | ((ssid & 0x0F) << 1)
    if last:
        ssid_byte |= 0x01
    encoded.append(ssid_byte)

    return bytes(encoded)


def ax25_fcs(data):
    """Calcula el FCS de AX.25 y lo devuelve en formato little-endian."""
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
    """Construye una trama UI AX.25 sin incluir las banderas."""
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("payload debe ser bytes o bytearray")

    frame = bytearray()
    frame.extend(ax25_address(destination, dest_ssid, last=False))
    frame.extend(ax25_address(source, source_ssid, last=True))
    frame.append(CONTROL_UI)
    frame.append(PID_NO_LAYER_3)
    frame.extend(payload)
    frame.extend(ax25_fcs(frame))
    return bytes(frame)


def byte_to_bits_lsb_first(byte):
    """Devuelve un byte como bits AX.25, empezando por el menos significativo."""
    return [(byte >> bit_index) & 0x01 for bit_index in range(8)]


def bytes_to_bits_lsb_first(data):
    bits = []
    for byte in data:
        bits.extend(byte_to_bits_lsb_first(byte))
    return bits


def bit_stuff(bits):
    """Inserta un 0 después de cinco bits 1 consecutivos en el cuerpo."""
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
    """Construye el flujo transmitido con banderas y cuerpo con bit-stuffing."""
    if preamble_flags < 0 or postamble_flags < 0:
        raise ValueError("la cantidad de banderas no puede ser negativa")

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
    """NRZI AX.25: el 0 cambia el nivel y el 1 mantiene el nivel actual."""
    level = 1 if initial_level else 0
    levels = []

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("los bits solo pueden ser 0 o 1")
        if bit == 0:
            level ^= 1
        levels.append(level)

    return levels
