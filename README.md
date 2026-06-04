# Design and Development of a Communications Protocol for Pehuensat III

Welcome to the repository for my thesis project: **Design and Development of a Communications Protocol for the Pehuensat III picosatellite**, which is part of the ongoing space program at the Universidad Nacional del Comahue in Neuquén, Argentina.

This thesis project is being conducted to fulfill the requirements for the Electronic Engineering degree at the Faculty of Engineering, Universidad Nacional del Comahue.

Here, I share the project's code, and later I will also share the final thesis document, so I can document both the process and the results in an honest way.

Right now, the repository is focused on validating the **Raspberry Pi Pico + MX614 modem** stage before integrating a full radio module.

## Current status of the project

At this stage, I am working on the transmit side of the protocol.

The idea is to:

- build a 16-byte telemetry ticket
- wrap it into an AX.25 UI frame
- calculate the FCS
- convert the frame to bits in AX.25 order
- apply bit stuffing
- apply NRZI encoding
- send the resulting digital signal from the Raspberry Pi Pico to the MX614
- observe the analog modem output with an oscilloscope

The code is now organized as a small modular library because I want it to be easier to understand, explain during the thesis defense, and test on a normal computer where possible.

## Hardware being used right now

- Raspberry Pi Pico / RP2040
- MX614 Bell 202 FSK modem
- Oscilloscope

For this validation stage, the objective is to verify the Pico + MX614 chain first. The radio module is not the priority yet.

## Current Raspberry Pi Pico to MX614 pin mapping

- `GP8`  -> `MX614 TXD`
- `GP9`  <- `MX614 RXD`
- `GP10` <- `MX614 RDY`
- `GP11` <- `MX614 DET`
- `GP12` -> `MX614 M0`
- `GP13` -> `MX614 M1`

## Important note about assumptions

At the moment, the code assumes:

- `M0 = 1`
- `M1 = 0`
- this selects the intended `1200 bps` transmit mode
- `TXD = 1` should give approximately `1200 Hz`
- `TXD = 0` should give approximately `2200 Hz`

These assumptions are written explicitly in the code on purpose, but they still need to be confirmed on the bench with the oscilloscope.

The PCB was designed following the datasheet reference values for the analog section, but I still want to confirm the full behavior on the real hardware instead of pretending it is already fully verified.

## Project structure

```text
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
```

## What each part does

- `lib/mx614.py`: handles the MX614 pins from MicroPython
- `lib/ticket.py`: builds the fixed 16-byte telemetry ticket
- `lib/ax25.py`: contains the AX.25 framing logic
- `lib/transmitter.py`: sends bits in a non-blocking way using `ticks_us()`
- `lib/sample_data.py`: contains a small deterministic set of sample telemetry records
- `main.py`: integrates everything on the Raspberry Pi Pico for the current hardware test

## Telemetry dataset

I added a small handcrafted telemetry dataset so the project does not depend on a single hardcoded example anymore.

This dataset is useful for:

- testing the protocol logic on CPython
- validating several realistic telemetry cases
- keeping the examples repeatable and easier to explain

The sample records are in `lib/sample_data.py`.

## What `main.py` is doing now

The current `main.py` is intended for the MX614 transmit validation stage.

It:

1. configures the MX614 transmit mode
2. builds a sample telemetry ticket
3. creates an AX.25 frame
4. converts it into a bitstream
5. applies NRZI encoding
6. transmits the result through `TXD` without blocking the main loop
7. keeps monitoring `DET` and `RDY`

It also includes simple test modes for:

- fixed `TXD = 1`
- fixed `TXD = 0`
- alternating pattern
- full AX.25 transmission

## What to measure with the oscilloscope

Useful measurement points are:

- digital `TXD` at Pico `GP8` / MX614 `TXD`
- analog output at `MX614 TXOUT`
- analog output at `AUDIO_TX` in `RADIO_IF1`, if that path is available in the current hardware

Expected result for the simplest tests:

- `TXD = 1` -> approximately `1200 Hz`
- `TXD = 0` -> approximately `2200 Hz`

For the AX.25 transmission, I expect to see the tones changing according to the encoded frame.

## Running tests on the computer

The modular path under `lib/` is written so the protocol parts can be tested with normal Python too.

From the repository root:

```bash
python3 -m unittest discover -s tests -v
```

## Copying files to the Raspberry Pi Pico

This project uses the **MicroPico Visual Studio Code Extension** (also known as Pico-W-Go) to write, upload, and run MicroPython code on the Raspberry Pi Pico.

> I keep the `.vscode` and `.micropico` files in the repository because they are part of the real workflow I use to connect and work with the board from VS Code.

If your Pico doesn’t have MicroPython installed yet:

1. Download the latest `.uf2` firmware from:
   https://micropython.org/download/rp2-pico/
2. Hold down the **BOOTSEL** button on your Pico and connect it by USB.
3. A USB drive will appear.
4. Drag and drop the `.uf2` file into it.

To work with the board from VS Code:

1. Install the **MicroPico** extension
2. Configure the serial device path
3. Open this project folder
4. Use the MicroPico commands to sync and run `main.py`

You can also use `mpremote` if you prefer:

```bash
mpremote connect auto fs cp -r lib :
mpremote connect auto fs cp main.py :
```

## Final note

This repository is not meant to look like a perfectly polished final product from day one. It is also a record of the actual thesis development process, including changes of direction, hardware experiments, and iterations.

Right now, the most important goal is to make the Pico + MX614 validation path solid, readable, and explainable.
