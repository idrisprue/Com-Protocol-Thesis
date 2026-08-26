# Kit de pruebas del beacon APRS/AX.25 de Pehuensat 3

Este kit está pensado para ejecutarlo desde Thonny en la Raspberry Pi Pico.
Los archivos deben quedar al mismo nivel que la carpeta `lib/` del proyecto.

## Qué prueba cada archivo

1. `01_verificar_payload_aprs.py`
   No transmite. Verifica el formato de los payloads APRS.

2. `02_verificar_codificador_ax25.py`
   No transmite. Ejecuta `make_ui_frame`, `make_ax25_bitstream` y `nrzi_encode`, y muestra si generan datos coherentes.

3. `03_transmitir_un_paquete.py`
   Transmite solamente un paquete `T#` conocido tres veces. Direwolf debe mostrar exactamente el payload esperado.

4. `04_transmitir_beacon_completo.py`
   Transmite el ciclo completo: identificación, PARM, UNIT, EQNS, BITS y T#.

5. `05_probar_cable_rx.py`
   No decodifica todavía AX.25. Verifica que el pin RXD de la Pico reciba actividad cuando llega una señal al MX614.

La prueba 3 confirma la cadena real de transmisión. La prueba 5 confirma únicamente actividad eléctrica en recepción. Para decodificar AX.25 en la Pico hace falta revisar las funciones de recepción del proyecto.

## Orden de ejecución

### Paso 1: payload

Abrir `01_verificar_payload_aprs.py` en Thonny y ejecutarlo.

Resultado esperado:

```text
RESULTADO FINAL: OK
```

### Paso 2: codificador AX.25

Ejecutar `02_verificar_codificador_ax25.py`.

Resultado esperado:

```text
RESULTADO FINAL: OK - el codificador generó la trama y el bitstream
```

Esto todavía no demuestra que la radio transmita correctamente.

### Paso 3: transmisión con Direwolf

1. Encender y preparar el receptor que está conectado a Direwolf.
2. Ejecutar `03_transmitir_un_paquete.py` en la Pico.
3. Buscar en Direwolf exactamente:

```text
UNCO-3>NQNGND:T#001,033,050,025,120,204,00000000
```

Si aparece exactamente esa línea, la transmisión real funciona: AX.25, FCS, bit-stuffing, NRZI, temporización, modulación, radio y recepción externa.

### Paso 4: beacon completo

Ejecutar `04_transmitir_beacon_completo.py` solamente después de que el paso 3 funcione.

### Paso 5: recepción de la Pico

1. Conectar el cable de audio de recepción al MX614.
2. Conectar `RXD` del MX614 al GPIO9 de la Pico.
3. Ejecutar `05_probar_cable_rx.py`.
4. Mientras se ejecuta, transmitir el paquete de prueba desde otra radio.

Resultado esperado:

```text
RESULTADO FINAL: OK - se detectó actividad en RXD
```

Esto confirma que la señal llega al pin RXD. No confirma todavía la reconstrucción completa de la trama AX.25.

## Importante

La salida `audio level` de Direwolf no alcanza por sí sola para afirmar que toda la modulación es correcta. La evidencia fuerte es que Direwolf muestre el paquete completo, sin `0x00`, sin `Unknown APRS Data Type` y sin advertencia de valores faltantes.

No conectar directamente salidas de RF entre equipos. Para una prueba por cable usar la atenuación o carga adecuada indicada por el director.
