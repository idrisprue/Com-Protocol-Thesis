# Guía de prueba: EasyTerm ↔ Raspberry Pi Pico

Esta prueba verifica una comunicación AX.25 conectada mínima entre EasyTerm y la Pico usando el MX614.

## Qué se va a probar

La estación EasyTerm inicia la conexión y la Pico responde:

```text
EasyTerm  → SABME
Pico      → UA
EasyTerm  → I (datos)
Pico      → RR
```

`SABME` no es un beacon APRS. Es una trama de control AX.25 que solicita iniciar una conexión. El beacon de telemetría usa otra trama, `UI`.

## Cableado necesario

Debe estar conectado el camino en los dos sentidos:

1. EasyTerm/radio transmisora → entrada analógica de recepción del MX614.
2. RXD del MX614 → GP9 de la Pico.
3. GP8 de la Pico → TXD del MX614.
4. Salida de transmisión del MX614 → entrada de audio de la estación EasyTerm/radio.
5. Tierra común y CLK del MX614 según el esquema del circuito.

No conectar audio directamente al GP9. GP9 recibe la salida digital RXD del MX614.

Para una prueba por cable, utilizar la atenuación o carga indicada por el director. No conectar salidas de RF directamente.

## Archivos que hay que cargar

Copiar a la Pico:

- `connected_ax25.py`
- `lib/ax25.py`
- `lib/ax25_rx.py`
- `lib/ax25_connected.py`
- `lib/mx614.py`
- `lib/transmitter.py`

La estación local configurada en el programa es `NQNGND`. El programa cambia automáticamente el MX614 a RX para escuchar, a TX para responder y nuevamente a RX después de cada respuesta.

## Procedimiento

1. Conectar la Pico y abrir `connected_ax25.py` en Thonny.
2. Ejecutar el programa.
3. Confirmar que aparezca `RESPONDEDOR PARA EASYTERM`.
4. Desde EasyTerm iniciar una conexión AX.25 hacia `NQNGND`.
5. Observar la consola de la Pico.
6. Cuando EasyTerm indique que la conexión se estableció, enviar un texto corto, por ejemplo `PRUEBA`.

## Resultado esperado

Primero:

```text
FCS: OK
ORIGEN: UNCO - 3
EVENTO: SABME recibido: conexión módulo 128 iniciada
Transmitiendo respuesta AX.25...
Respuesta transmitida
```

Después de enviar datos:

```text
FCS: OK
EVENTO: I recibida correctamente: se responde RR
PAYLOAD: PRUEBA
Transmitiendo respuesta AX.25...
Respuesta transmitida
```

## Cómo interpretar la prueba

- `FCS: OK` + `SABME recibido`: la Pico recibió y validó una trama AX.25.
- `Respuesta transmitida`: el programa generó `UA` o `RR` y la envió al MX614.
- EasyTerm pasa a conectado: el intercambio de control funcionó en los dos sentidos.
- `I recibida` + payload visible: la Pico recibió datos de la conexión.
- EasyTerm sigue esperando después de `SABME`: revisar el camino TX de la Pico hacia EasyTerm, el modo TX del MX614 y el nivel de audio.
- Nunca aparece `FCS: OK`: revisar el camino RX hacia el MX614, RXD/GP9, DET, CLK, audio y temporización.
- Aparece `MemoryError`: volver a cargar la versión actual de `connected_ax25.py` y `lib/ax25_rx.py`.

## Aclaración del alcance

Este programa es un respondedor mínimo para validar el enlace de laboratorio. Maneja el inicio de conexión, datos básicos, confirmaciones y desconexión. Todavía no es una pila AX.25 completa con todos los temporizadores, reintentos, ventanas y retransmisiones.
