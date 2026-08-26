"""Funciones auxiliares de recepción AX.25 para validar la Pico + MX614.

Este módulo no depende del hardware. Recibe niveles lógicos NRZI muestreados,
deshace NRZI y el bit-stuffing, busca banderas AX.25 y valida el FCS.
"""

try:
    from .ax25 import FLAG_BYTE, CONTROL_UI, PID_NO_LAYER_3, ax25_fcs, byte_to_bits_lsb_first
except ImportError:
    from ax25 import FLAG_BYTE, CONTROL_UI, PID_NO_LAYER_3, ax25_fcs, byte_to_bits_lsb_first


# Tramas de control no numeradas que pueden aparecer en una conexión AX.25.
CONTROL_SABM = 0x2F
CONTROL_SABME = 0x6F
CONTROL_DISC = 0x43
CONTROL_UA = 0x63
CONTROL_DM = 0x0F
CONTROL_FRMR = 0x87

CONTROL_NAMES = {
    CONTROL_UI: "UI",
    CONTROL_SABM: "SABM",
    CONTROL_SABME: "SABME",
    CONTROL_DISC: "DISC",
    CONTROL_UA: "UA",
    CONTROL_DM: "DM",
    CONTROL_FRMR: "FRMR",
}


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

        # Dos direcciones (14 bytes), control (1 byte) y FCS (2 bytes).
        if len(frame) < 17:
            continue
        if frame[-2:] != ax25_fcs(frame[:-2]):
            continue
        frames.append(frame)
    return frames


def _parse_addresses(frame):
    """Extrae las direcciones AX.25 y devuelve el índice del campo control."""
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

    if len(addresses) < 2 or index + 1 > len(frame) - 2:
        raise ValueError("campos de direccion AX.25 incompletos")

    return addresses, index


def _decode_address(address):
    callsign = "".join(chr(value >> 1) for value in address[:6]).rstrip()
    ssid = (address[6] >> 1) & 0x0F
    return callsign, ssid


def parse_ax25_frame(frame):
    """Analiza una trama AX.25 UI o de control y valida su FCS."""
    if len(frame) < 17:
        raise ValueError("la trama AX.25 es demasiado corta")

    addresses, index = _parse_addresses(frame)
    source, source_ssid = _decode_address(addresses[1])
    destination, destination_ssid = _decode_address(addresses[0])
    control = frame[index]
    frame_type = CONTROL_NAMES.get(control, "CONTROL_0x{:02X}".format(control))

    packet = {
        "source": source,
        "source_ssid": source_ssid,
        "destination": destination,
        "destination_ssid": destination_ssid,
        "control": control,
        "frame_type": frame_type,
        "information": b"",
        "fcs": frame[-2:],
    }

    if control == CONTROL_UI:
        if index + 4 > len(frame):
            raise ValueError("trama UI sin PID o informacion completos")
        if frame[index + 1] != PID_NO_LAYER_3:
            raise ValueError("PID AX.25 no soportado")
        packet["pid"] = frame[index + 1]
        packet["information"] = frame[index + 2:-2]

    return packet


def parse_connected_frame(frame, modulo=128):
    """Analiza tramas U, I y S de una conexión AX.25.

    SABME utiliza módulo 128, por lo que sus tramas I y S tienen un campo de
    control de dos bytes. SABM utiliza módulo 8 y un control de un byte.
    """
    if len(frame) < 17:
        raise ValueError("la trama AX.25 es demasiado corta")
    if modulo not in (8, 128):
        raise ValueError("el módulo AX.25 debe ser 8 o 128")

    addresses, index = _parse_addresses(frame)
    source, source_ssid = _decode_address(addresses[1])
    destination, destination_ssid = _decode_address(addresses[0])
    control = frame[index]

    packet = {
        "source": source,
        "source_ssid": source_ssid,
        "destination": destination,
        "destination_ssid": destination_ssid,
        "control": control,
        "control_bytes": frame[index:index + 2],
        "information": b"",
        "fcs": frame[-2:],
    }

    # Bit 0 = 0 identifica una trama de información I.
    if (control & 0x01) == 0:
        if modulo == 128:
            if index + 4 > len(frame):
                raise ValueError("trama I extendida incompleta")
            second_control = frame[index + 1]
            packet["frame_type"] = "I"
            packet["send_sequence"] = (control >> 1) & 0x7F
            packet["receive_sequence"] = (second_control >> 1) & 0x7F
            packet["poll_final"] = second_control & 0x01
            packet["information"] = frame[index + 2:-2]
        else:
            if index + 3 > len(frame):
                raise ValueError("trama I incompleta")
            packet["frame_type"] = "I"
            packet["send_sequence"] = (control >> 1) & 0x07
            packet["receive_sequence"] = (control >> 5) & 0x07
            packet["poll_final"] = (control >> 4) & 0x01
            packet["information"] = frame[index + 1:-2]
        return packet

    # Bits 0..1 = 01 identifican una trama supervisoria S.
    if (control & 0x03) == 0x01:
        subtype = (control >> 2) & 0x03
        packet["frame_type"] = ("RR", "RNR", "REJ", "SREJ")[subtype]
        if modulo == 128:
            if index + 4 > len(frame):
                raise ValueError("trama S extendida incompleta")
            second_control = frame[index + 1]
            packet["receive_sequence"] = (second_control >> 1) & 0x7F
            packet["poll_final"] = second_control & 0x01
        else:
            packet["receive_sequence"] = (control >> 5) & 0x07
            packet["poll_final"] = (control >> 4) & 0x01
        return packet

    # Las tramas U tienen un control de un byte. Se ignora P/F para reconocer
    # el tipo base de la trama.
    control_base = control & 0xEF
    packet["frame_type"] = CONTROL_NAMES.get(
        control_base, "CONTROL_0x{:02X}".format(control_base)
    )
    packet["poll_final"] = (control >> 4) & 0x01
    return packet


def parse_ui_frame(frame):
    """Analiza una trama UI y exige que no sea una trama de control."""
    packet = parse_ax25_frame(frame)
    if packet["frame_type"] != "UI":
        raise ValueError("no es una trama UI")
    return packet


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
    # Procesa una fase por vez para no reservar simultáneamente ocho listas.
    for phase in range(samples_per_bit):
        levels = []
        index = phase + (samples_per_bit // 2)
        while index < len(samples):
            levels.append(1 if samples[index] else 0)
            index += samples_per_bit
        frames = decode_levels(levels, initial_level=initial_level)
        if frames:
            return frames
    return []
