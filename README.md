# Diseño y desarrollo de un protocolo de comunicaciones para Pehuensat III

Este repositorio contiene el código de mi proyecto de tesis: **Diseño y desarrollo de un protocolo de comunicaciones para el picosatélite Pehuensat III**, que forma parte del programa espacial de la Universidad Nacional del Comahue, en Neuquén, Argentina.

El proyecto se desarrolla como parte de los requisitos para obtener el título de Ingeniera Electrónica en la Facultad de Ingeniería de la Universidad Nacional del Comahue.

En este repositorio comparto el código del proyecto y, más adelante, también compartiré el documento final de la tesis para dejar registrado el proceso y los resultados de forma clara y verificable.

Actualmente, el repositorio está enfocado en validar la etapa Raspberry Pi Pico + módem MX614 antes de integrar el módulo de radio completo.

## Estado actual del proyecto

En esta etapa se está trabajando principalmente sobre el lado de transmisión del protocolo.

El objetivo es:

- construir un paquete de telemetría de 16 bytes;
- encapsularlo en una trama AX.25 UI;
- calcular el FCS;
- convertir la trama a bits según el orden de AX.25;
- aplicar bit-stuffing;
- aplicar codificación NRZI;
- enviar la señal digital desde la Raspberry Pi Pico al MX614;
- observar la salida analógica del módem con un osciloscopio;
- validar posteriormente la transmisión y recepción mediante un equipo externo.

El código está organizado como una biblioteca modular para que sea más fácil de entender, explicar durante la defensa de la tesis y probar en una computadora normal cuando sea posible.

## Hardware utilizado actualmente

- Raspberry Pi Pico / RP2040
- Módem FSK MX614 Bell 202
- Osciloscopio

En esta etapa de validación, el objetivo principal es verificar primero la cadena Pico + MX614. La integración con el módulo de radio completo se realiza posteriormente.

## Conexión actual entre la Raspberry Pi Pico y el MX614

- GP8  -> MX614 TXD
- GP9  <- MX614 RXD
- GP10 <- MX614 RDY
- GP11 <- MX614 DET
- GP12 -> MX614 M0
- GP13 -> MX614 M1

## Supuestos importantes

Por el momento, el código utiliza los siguientes supuestos:

- M0 = 1;
- M1 = 0;
- esta combinación selecciona el modo de transmisión previsto de 1200 baudios;
- TXD = 1 debería generar aproximadamente 1200 Hz;
- TXD = 0 debería generar aproximadamente 2200 Hz.

Estos supuestos aparecen explícitamente en el código porque todavía deben confirmarse sobre el hardware real mediante el osciloscopio.

La placa de circuito impreso fue diseñada utilizando los valores de referencia del circuito analógico indicados en la hoja de datos. Sin embargo, el comportamiento completo debe verificarse experimentalmente; no se considera validado solamente por haber sido diseñado según el datasheet.

## Estructura del proyecto

~~~text
Com-Protocol-Thesis/
├── README.md
├── main.py
├── lib/
│   ├── __init__.py
│   ├── ax25.py
│   ├── mx614.py
│   ├── sample_data.py
│   ├── ticket.py
│   └── transmitter.py
└── tests/
~~~

## Función de cada componente

- lib/mx614.py: controla los pines del MX614 desde MicroPython.
- lib/ticket.py: construye el paquete fijo de telemetría de 16 bytes.
- lib/ax25.py: contiene la lógica de construcción y codificación de tramas AX.25.
- lib/transmitter.py: transmite los bits de forma no bloqueante utilizando ticks_us().
- lib/sample_data.py: contiene registros de telemetría de prueba deterministas.
- main.py: integra los componentes para realizar las pruebas actuales con la Raspberry Pi Pico.

## Conjunto de datos de telemetría

El proyecto incluye un pequeño conjunto de datos de telemetría creado manualmente. De esta manera, las pruebas no dependen de un único ejemplo escrito directamente en el programa.

Estos registros sirven para:

- probar la lógica del protocolo en CPython;
- validar varios casos de telemetría;
- mantener ejemplos repetibles;
- facilitar la explicación del funcionamiento del sistema.

Los registros se encuentran en lib/sample_data.py.

## Funcionamiento actual de main.py

El archivo main.py está destinado a la etapa de validación de transmisión mediante el MX614.

Sus funciones principales son:

1. configurar el modo de transmisión del MX614;
2. construir un paquete de telemetría de prueba;
3. crear una trama AX.25;
4. convertirla en un flujo de bits;
5. aplicar la codificación NRZI;
6. transmitir el resultado mediante el pin TXD sin bloquear el ciclo principal;
7. continuar monitoreando las señales DET y RDY.

También incluye modos de prueba para:

- TXD = 1 fijo;
- TXD = 0 fijo;
- patrón alternado;
- transmisión completa de una trama AX.25.

## Qué medir con el osciloscopio

Los puntos de medición más importantes son:

- señal digital TXD en el pin GP8 de la Pico / entrada TXD del MX614;
- salida analógica en MX614 TXOUT;
- salida analógica en AUDIO_TX de RADIO_IF1, si ese recorrido está disponible en el hardware utilizado.

Para las pruebas más simples se espera observar:

- TXD = 1 -> aproximadamente 1200 Hz;
- TXD = 0 -> aproximadamente 2200 Hz.

Durante la transmisión AX.25, se espera observar el cambio entre ambas frecuencias de acuerdo con los bits codificados de la trama.

La medición con osciloscopio permite validar la modulación del MX614. La recepción de la trama por Direwolf permite validar además la cadena completa de transmisión y recepción externa.

## Ejecución de las pruebas en una computadora

La parte modular ubicada en lib/ está preparada para que la lógica del protocolo pueda probarse también con Python normal.

Desde la raíz del repositorio:

~~~bash
python3 -m unittest discover -s tests -v
~~~

## Copiar los archivos a la Raspberry Pi Pico

Este proyecto utiliza la extensión MicroPico para Visual Studio Code, también conocida como Pico-W-Go, para escribir, cargar y ejecutar código MicroPython en la Raspberry Pi Pico.

Los archivos .vscode y .micropico se mantienen en el repositorio porque forman parte del flujo de trabajo utilizado para conectarse a la placa desde Visual Studio Code.

Si la Pico todavía no tiene MicroPython instalado:

1. descargar el firmware .uf2 correspondiente desde:
   https://micropython.org/download/rp2-pico/
2. mantener presionado el botón BOOTSEL de la Pico y conectarla mediante USB;
3. esperar a que aparezca una unidad de almacenamiento USB;
4. copiar el archivo .uf2 dentro de esa unidad.

Para trabajar con la placa desde Visual Studio Code:

1. instalar la extensión MicroPico;
2. configurar el puerto serie;
3. abrir la carpeta de este repositorio;
4. utilizar los comandos de MicroPico para sincronizar y ejecutar main.py.

También es posible utilizar mpremote:

~~~bash
mpremote connect auto fs cp -r lib :
mpremote connect auto fs cp main.py :
~~~

## Nota final

Este repositorio no pretende presentarse como un producto final completamente terminado desde el primer día. También funciona como registro del desarrollo real de la tesis, incluyendo los cambios de dirección, las pruebas de hardware y las iteraciones del proyecto.

El objetivo actual más importante es lograr que la cadena de validación Pico + MX614 sea sólida, legible, reproducible y fácil de explicar.
