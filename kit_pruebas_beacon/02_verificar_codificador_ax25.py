# Verificacion del codificador AX.25/NRZI.
# No transmite. Requiere la carpeta lib/ del proyecto.

try:
    from lib.ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
except ImportError:
    from ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode


SOURCE = "UNCO"
SOURCE_SSID = 3
DESTINATION = "NQNGND"
DESTINATION_SSID = 0
PAYLOAD = "T#001,033,050,025,120,204,00000000"


def as_bytes(value):
    try:
        return bytes(value)
    except Exception:
        return bytes(bytearray(value))


def hex_bytes(value):
    raw = as_bytes(value)
    try:
        return raw.hex()
    except AttributeError:
        result = ""
        for item in raw:
            result += "%02x" % item
        return result


def only_binary(values):
    for value in values:
        if value not in (0, 1):
            return False
    return True


def main():
    print("=== PRUEBA 2: CODIFICADOR AX.25/NRZI ===")
    payload_bytes = PAYLOAD.encode("ascii")

    frame = make_ui_frame(
        destination=DESTINATION,
        dest_ssid=DESTINATION_SSID,
        source=SOURCE,
        source_ssid=SOURCE_SSID,
        payload=payload_bytes,
    )
    frame_bytes = as_bytes(frame)

    bitstream = list(
        make_ax25_bitstream(
            frame,
            preamble_flags=20,
            postamble_flags=3,
        )
    )
    levels = list(nrzi_encode(bitstream, initial_level=1))

    print("Payload:", PAYLOAD)
    print("Trama AX.25 en hexadecimal:")
    print(hex_bytes(frame_bytes))
    print("Bytes de la trama:", len(frame_bytes))
    print("Bits con flags y bit-stuffing:", len(bitstream))
    print("Niveles NRZI:", len(levels))

    ok = True
    if payload_bytes not in frame_bytes:
        print("ERROR: el payload no aparece dentro de la trama")
        ok = False
    else:
        print("OK: el payload aparece dentro de la trama")

    if len(bitstream) == 0:
        print("ERROR: no se genero bitstream")
        ok = False
    elif not only_binary(bitstream):
        print("ERROR: el bitstream contiene valores distintos de 0 y 1")
        ok = False
    else:
        print("OK: bitstream generado con valores binarios")

    if len(levels) != len(bitstream):
        print("ERROR: NRZI cambio la cantidad de bits")
        ok = False
    elif not only_binary(levels):
        print("ERROR: NRZI genero niveles distintos de 0 y 1")
        ok = False
    else:
        print("OK: NRZI genero niveles binarios de igual longitud")

    if bytes([0x03]) in frame_bytes:
        print("OK: aparece el control UI 0x03")
    else:
        print("AVISO: no se encontro 0x03; revisar implementacion")

    if bytes([0xF0]) in frame_bytes:
        print("OK: aparece el PID 0xF0")
    else:
        print("AVISO: no se encontro 0xF0; revisar implementacion")

    if ok:
        print("RESULTADO FINAL: OK - el codificador genero la trama y el bitstream")
    else:
        print("RESULTADO FINAL: ERROR")
    print("NOTA: esta prueba no reemplaza la recepcion con Direwolf.")


if __name__ == "__main__":
    main()
