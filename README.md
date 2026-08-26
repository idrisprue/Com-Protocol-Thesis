# Diseño y desarrollo de un protocolo de comunicaciones para Pehuensat III

Este repositorio contiene el código del proyecto de tesis **Diseño y desarrollo de un protocolo de comunicaciones para el picosatélite Pehuensat III**, de la Universidad Nacional del Comahue.

El objetivo de esta etapa es validar la cadena Raspberry Pi Pico + módem MX614 Bell 202 antes de integrar el módulo de radio completo. El repositorio incluye transmisión de telemetría APRS/AX.25 y recepción de tramas AX.25.

## Estado actual

Se pueden probar dos modos diferentes:

- **Beacon APRS:** una trama AX.25 `UI` con información de telemetría, por ejemplo `T#001,033,050,025,120,204,00000000`.
- **Conexión AX.25 con EasyTerm:** intercambio de tramas de control y datos: `SABME → UA → I → RR`.

La Pico valida el FCS, decodifica NRZI y bit-stuffing, identifica el tipo de trama y muestra el payload cuando corresponde.

## Hardware y conexiones

- Raspberry Pi Pico / RP2040
- Módem MX614 Bell 202
- Osciloscopio
- Equipo de radio o conexión de audio cableada para la prueba

Conexiones usadas por el código:

- GP8 → TXD
- GP9 ← RXD
- GP10 ← RDY
- GP11 ← DET
- GP12 → M0
- GP13 → M1

Para transmitir se usa M0=1, M1=0. Para recibir a 1200 bit/s se usa M0=0, M1=0. La entrada CLK del MX614 debe estar conectada según el esquema y el datasheet; el código no la genera.

No conectar salidas de RF directamente entre equipos. Para una prueba cableada hay que usar la atenuación o carga adecuada indicada por el director.

## Estructura principal

```text
Com-Protocol-Thesis/
├── README.md
├── main.py
├── receive_ax25.py
├── connected_ax25.py
├── direwolf_prueba.conf
├── lib/
│   ├── ax25.py
│   ├── ax25_rx.py
│   ├── ax25_connected.py
│   ├── mx614.py
│   └── transmitter.py
├── tests/
│   └── test_ax25_connected.py
└── kit_pruebas_beacon/
    ├── 01_verificar_payload_aprs.py
    ├── 02_verificar_codificador_ax25.py
    ├── 03_transmitir_un_paquete.py
    ├── 04_transmitir_beacon_completo.py
    ├── 05_probar_cable_rx.py
    └── README.md
```

Los comentarios, docstrings y mensajes agregados para estas pruebas están en español. Se mantienen en inglés solo los nombres estándar del protocolo: AX.25, APRS, NRZI, FCS, RXD, TXD, DET, SABME, UA, I y RR.

## Qué prueba cada programa

### 1. Verificación sin hardware

Desde la carpeta del proyecto:

```bash
python3 kit_pruebas_beacon/01_verificar_payload_aprs.py
python3 kit_pruebas_beacon/02_verificar_codificador_ax25.py
python3 -m unittest discover -s tests -v
```

El primer programa comprueba que los payloads sean ASCII y tengan el formato APRS esperado. El segundo comprueba la construcción de la trama, el FCS, el bitstream y NRZI. Estas pruebas no demuestran que el MX614 module correctamente.

### 2. Transmisión de un beacon UI con Direwolf

Usar `03_transmitir_un_paquete.py` después de cargarlo en la Pico junto con `lib/`.

Direwolf debe mostrar exactamente:

```text
UNCO-3>NQNGND:T#001,033,050,025,120,204,00000000
```

Esa salida confirma la cadena completa de transmisión: AX.25, FCS, bit-stuffing, NRZI, temporización, MX614, audio/radio y demodulación externa.

Para Direwolf se incluye `direwolf_prueba.conf`. La configuración transmite el beacon inmediatamente y luego cada 60 segundos:

```text
direwolf -c direwolf_prueba.conf
```

En Windows:

```text
direwolf.exe -c direwolf_prueba.conf
```

### 3. Beacon APRS completo

Ejecutar `04_transmitir_beacon_completo.py` solo después de que funcione el paquete único. Envía identificación, `PARM`, `UNIT`, `EQNS`, `BITS` y `T#`.

En este modo el receptor remoto debe interpretar tramas **UI**. No se debe esperar un intercambio `SABME/UA`.

### 4. Recepción UI en la Pico

Cargar en la Pico:

- `receive_ax25.py`
- `lib/ax25_rx.py`
- `lib/mx614.py`

Conectar la salida de audio de la estación transmisora a la entrada analógica del receptor MX614 y conectar RXD al GP9. Ejecutar `receive_ax25.py` mientras otra estación transmite:

```text
T#001,033,050,025,120,204,00000000
```

Resultado esperado:

```text
FCS: OK
ORIGEN: UNCO-3
DESTINO: NQNGND
PAYLOAD: T#001,033,050,025,120,204,00000000
RESULTADO: OK - recepcion y decodificacion AX.25 correctas
```

Si Direwolf o EasyTerm envía `SABME`, `receive_ax25.py` puede indicar que la trama AX.25 es válida, pero no es un beacon UI/APRS. Eso no es un error de FCS: significa que se está usando el programa equivocado para ese tipo de prueba.

### 5. Prueba conectada con EasyTerm

El director indicó que EasyTerm está enviando `SABME`. Para esa prueba cargar:

- `connected_ax25.py`
- `lib/ax25_connected.py`
- `lib/ax25_rx.py`
- `lib/ax25.py`
- `lib/mx614.py`
- `lib/transmitter.py`

Ejecutar primero `connected_ax25.py` en la Pico. Después iniciar desde EasyTerm una conexión AX.25 dirigida a `NQNGND`.

La secuencia esperada es:

```text
EasyTerm  → SABME
Pico      → UA
EasyTerm  → I (datos)
Pico      → RR
```

En la consola de la Pico debería aparecer algo similar a:

```text
FCS: OK
ORIGEN: UNCO - 3
EVENTO: SABME recibido: conexión módulo 128 iniciada
Transmitiendo respuesta AX.25...
Respuesta transmitida
```

Cuando EasyTerm envíe datos:

```text
EVENTO: I recibida correctamente: se responde RR
PAYLOAD: ...
```

La recepción de `SABME` con `FCS: OK` demuestra que la Pico recibió una trama AX.25 de control válida. La respuesta `UA` demuestra que la Pico puede participar en el inicio de una conexión. La respuesta `RR` después de una trama `I` demuestra el acuse básico de datos.

Esta implementación es un respondedor mínimo de laboratorio. Incluye `SABME`, `SABM`, `UA`, `I`, `RR`, `REJ`, `DISC` y `DM`, pero todavía no es una pila AX.25 completa: no implementa todos los temporizadores, reintentos, ventanas, retransmisiones ni todas las variantes de direccionamiento. Es suficiente para verificar el enlace punto a punto inicial con EasyTerm.

## UI y SABME no son lo mismo

- `UI`: trama sin conexión. Es la que usa normalmente APRS para beacons y telemetría.
- `SABME`: trama de control. Inicia una conexión AX.25 de módulo 128 y no contiene un payload APRS.
- `UA`: respuesta afirmativa al inicio de conexión.
- `I`: trama de información dentro de la conexión.
- `RR`: confirmación de recepción.

Por eso el beacon y la prueba de EasyTerm necesitan programas distintos, aunque ambos usen AX.25.

## Problema de memoria

Si aparece:

```text
MemoryError: memory allocation failed, allocating 262144 bytes
```

la captura estaba intentando reservar demasiada memoria en la Pico. Las versiones actuales usan `bytearray`, ventanas de captura limitadas y procesamiento por fases. Hay que volver a cargar en la Pico la versión actual de `receive_ax25.py` o `connected_ax25.py` y `lib/ax25_rx.py`, reiniciar la placa y repetir.

## Kit de pruebas

La carpeta `kit_pruebas_beacon/` contiene programas numerados para que el equipo pueda ejecutar las pruebas sin modificar el código. El orden recomendado es:

1. payload APRS;
2. codificador AX.25;
3. un beacon con Direwolf;
4. beacon APRS completo;
5. camino eléctrico RX;
6. recepción UI o conexión EasyTerm, según el objetivo.

En cada prueba deben guardar la salida de la consola y anotar el cableado, modo del MX614, configuración de Direwolf/EasyTerm y si la prueba fue cableada o por radio.

## Resultado validado y pendiente

La lógica del protocolo se validó automáticamente en una computadora: pasan 7 pruebas, incluyendo FCS, NRZI, bit-stuffing, rechazo de tramas corruptas, recepción de `SABME` y respuestas `UA/RR`.

La validación del circuito, la modulación analógica y el enlace de radio todavía debe realizarse en el laboratorio.
