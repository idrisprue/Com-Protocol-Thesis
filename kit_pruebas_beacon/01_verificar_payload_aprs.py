# Verificacion offline de payloads APRS para Pehuensat 3.
# No usa la radio ni el MX614.

SOURCE = "UNCO-3"


def telemetry_message(body):
    # Los mensajes PARM/UNIT/EQNS/BITS son mensajes APRS.
    return ":" + SOURCE.ljust(9) + ":" + body


def check(condition, ok_text, error_text):
    if condition:
        print("OK:", ok_text)
        return True
    print("ERROR:", error_text)
    return False


def main():
    payloads = [
        ">PEHUENSAT 3",
        telemetry_message("PARM.VOLTAGE,CURRENT,TEMP,RADIATION,CPU"),
        telemetry_message("UNIT.V,mA,C,CPM,%"),
        telemetry_message("EQNS.0,0.1,0,0,1,0,0,1,0,0,1,0,0,0.392,0"),
        telemetry_message("BITS.11111111,PEHUENSAT 3"),
        "T#001,033,050,025,120,204,00000000",
    ]

    all_ok = True
    print("=== PRUEBA 1: PAYLOADS APRS ===")

    for payload in payloads:
        print("PAYLOAD:", payload)
        try:
            payload.encode("ascii")
            result = True
        except Exception:
            result = False
        all_ok = check(result, "ASCII valido", "el payload no es ASCII") and all_ok

    all_ok = check(
        payloads[0][0] == ">",
        "identificacion APRS comienza con >",
        "identificacion incorrecta",
    ) and all_ok

    for payload in payloads[1:5]:
        all_ok = check(
            payload.startswith(":"),
            "mensaje de telemetria comienza con :",
            "falta el : inicial del mensaje APRS",
        ) and all_ok
        all_ok = check(
            len(payload[1:10]) == 9 and payload[10] == ":",
            "destinatario APRS tiene 9 caracteres",
            "el destinatario APRS no tiene 9 caracteres",
        ) and all_ok

    telemetry = payloads[5]
    fields = telemetry[2:].split(",")
    all_ok = check(
        telemetry.startswith("T#") and len(fields) == 7,
        "T# contiene secuencia, 5 canales analogicos y 8 bits",
        "T# no tiene la cantidad completa de campos",
    ) and all_ok
    all_ok = check(
        len(fields[-1]) == 8 and all(c in "01" for c in fields[-1]),
        "campo digital tiene 8 bits",
        "campo digital incorrecto",
    ) and all_ok

    if all_ok:
        print("RESULTADO FINAL: OK")
    else:
        print("RESULTADO FINAL: ERROR")


if __name__ == "__main__":
    main()
