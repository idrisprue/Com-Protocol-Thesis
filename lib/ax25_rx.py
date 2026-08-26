"""Funciones auxiliares de recepción AX.25 para validar la Pico + MX614.

Este módulo no depende del hardware. Recibe niveles lógicos NRZI muestreados,
deshace NRZI y el bit-stuffing, busca banderas AX.25 y valida el FCS.
"""

try:
    from .ax25 import FLAG_BYTE, CONTROL_UI, PID_NO_LAYER_3, ax25_fcs, byte_to_bits_lsb_first
except ImportError:
    from ax25 import FLAG_BYTE, CONTROL_UI, PID_NO_LAYER_3, ax25_fcs, byte_to_bits_lsb_first


def nrzi_decode(levels, initial_level=1):
    """Convierte niveles NRZI en bits AX.25.

    Dos niveles consecutivos iguales representan un bit 1. Un cambio de nivel
    representa un bit 0.
    """
    previous = 1 if initial_level else 0
    bits = []
    for level in levels:
        level = 1 if level else 0
        bits.append(1 if level == previous else 0)
        previous = level
    return bits


def bit_unstuff(bits):
    """Elimina el cero insertado después de cada secuencia de cinco unos."""
    result = []
    consecutive_ones = 0
    index = 0
    while index < len(bits):
        bit = bits[index]
        result.append(bit)
        if bit == 1:
            consecutive_ones += 1
            if consecutive_ones == 5:
                index += 1
                if index >= len(bits) or bits[index] != 0:
                    raise ValueError("bit-stuffing AX.25 inválido")
                consecutive_ones = 0
        else:
            consecutive_ones = 0
        index += 1
    return result


def bits_to_bytes_lsb_first(bits):
    """Convierte grupos completos de ocho bits LSB-first en bytes."""
    if len(bits) % 8 != 0:
        raise ValueError("la trama AX.25 no contiene bytes completos")
    result = bytearray()
    for start in range(0, len(bits), 8):
        value = 0
        for offset in range(8):
            value |= (bits[start + offset] & 1) << offset
        result.append(value)
    return bytes(result)


def _find_flag(bits, start):
    flag_bits = byte_to_bits_lsb_first(FLAG_BYTE)
    last = len(bits) - len(flag_bits)
    for index in range(start, last + 1):
        if bits[index:index + 8] == flag_bits:
            return index
    return -1


def _candidate_frames(bits):
    """Genera candidatos de bits del cuerpo entre banderas consecutivas."""
    start = _find_flag(bits, 0)
    while start >= 0:
        end = _find_flag(bits, start + 8)
        if end < 0:
            return
        body = bits[start + 8:end]
        if body:
            yield body
        start = end


def decode_levels(levels, initial_level=1):
    """Devuelve las tramas AX.25 válidas encontradas en niveles NRZI.

    Las tramas se devuelven sin banderas, como bytes crudos e incluyendo el FCS.
    """
    bits = nrzi_decode(levels, initial_level=initial_level)
    frames = []
    for candidate in _candidate_frames(bits):
        try:
            body_bits = bit_unstuff(candidate)
            frame = bits_to_bytes_lsb_first(body_bits)
        except ValueError:
            continue

        if len(frame) < 18:
            continue
        if frame[-2:] != ax25_fcs(frame[:-2]):
            continue
        frames.append(frame)
    return frames


def parse_ui_frame(frame):
    """Analiza dirección, control, PID, información y FCS de una trama UI."""
    if len(frame) < 18:
        raise ValueError("la trama AX.25 es demasiado corta")
    if frame[-2:] != ax25_fcs(frame[:-2]):
        raise ValueError("FCS invalido")

    addresses = []
    index = 0
    while index + 7 <= len(frame):
        address = frame[index:index + 7]
        addresses.append(address)
        index += 7
        if address[6] & 0x01:
            break

    if len(addresses) < 2 or index + 4 > len(frame):
        raise ValueError("campos de direccion AX.25 incompletos")
    if frame[index] != CONTROL_UI:
        raise ValueError("no es una trama UI")
    if frame[index + 1] != PID_NO_LAYER_3:
        raise ValueError("PID AX.25 no soportado")

    def decode_address(address):
        callsign = "".join(chr(value >> 1) for value in address[:6]).rstrip()
        ssid = (address[6] >> 1) & 0x0F
        return callsign, ssid

    source, source_ssid = decode_address(addresses[1])
    destination, destination_ssid = decode_address(addresses[0])
    info_start = index + 2
    return {
        "source": source,
        "source_ssid": source_ssid,
        "destination": destination,
        "destination_ssid": destination_ssid,
        "control": frame[index],
        "pid": frame[index + 1],
        "information": frame[info_start:-2],
        "fcs": frame[-2:],
    }


def sampled_levels(samples, samples_per_bit=8):
    """Prueba cada fase de muestreo y devuelve secuencias candidatas."""
    candidates = []
    for phase in range(samples_per_bit):
        levels = []
        index = phase + (samples_per_bit // 2)
        while index < len(samples):
            levels.append(1 if samples[index] else 0)
            index += samples_per_bit
        candidates.append(levels)
    return candidates


def decode_samples(samples, initial_level=1, samples_per_bit=8):
    """Decodifica RXD sobremuestreado probando todas las fases."""
    for levels in sampled_levels(samples, samples_per_bit=samples_per_bit):
        frames = decode_levels(levels, initial_level=initial_level)
        if frames:
            return frames
    return []
