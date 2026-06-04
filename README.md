# Com-Protocol-Thesis

MicroPython and CPython support code for an Electronic Engineering thesis on
the Pehuensat III pico-satellite project. The current default workflow in this
branch validates the transmit side of a low-rate AX.25 / Bell 202
communication chain using a Raspberry Pi Pico and an MX614 modem.

Older SX1278-based experiments remain in the repository as legacy reference,
but `main.py` and the `lib/` package now focus on the Pico + MX614 stage.

## Thesis context

The thesis target is a low-rate radio protocol for downloading IoT telemetry
from a pico-satellite to a ground station. The current software validates:

- AX.25 UI framing
- AX.25 FCS, bit order, bit stuffing, and NRZI encoding
- Bell 202 FSK/AFSK-style digital drive toward the MX614 at 1200 bps

The software is intentionally split into small modules so the design is easier
to explain, test, and extend during the thesis work.

## Current branch focus

This branch validates the Pico + MX614 modem stage only. It does not yet
integrate the future radio module path. The older root-level `sx1278.py`,
`ax25.py`, and `ticket.py` files are preserved as earlier thesis work and
reference material.

## Hardware used

- Raspberry Pi Pico / RP2040
- MX614 Bell 202 FSK modem
- Oscilloscope for signal validation

## Pin mapping

Current Raspberry Pi Pico to MX614 mapping:

- `GP8`  -> `MX614 TXD`
- `GP9`  <- `MX614 RXD`
- `GP10` <- `MX614 RDY`
- `GP11` <- `MX614 DET`
- `GP12` -> `MX614 M0`
- `GP13` -> `MX614 M1`

## Current assumptions pending oscilloscope confirmation

The current software keeps these assumptions explicit, but they are still
provisional until they are confirmed on the bench:

- `M0 = 1`
- `M1 = 0`
- this pin combination selects the intended `1200 bps` transmit mode
- `TXD = 1` should produce approximately `1200 Hz`
- `TXD = 0` should produce approximately `2200 Hz`

The PCB analog network may follow the datasheet design, but the complete mode
selection and tone mapping still need oscilloscope confirmation on the actual
assembled hardware.

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
├── sx1278.py                 # legacy reference
├── ax25.py                   # legacy reference
├── ticket.py                 # legacy reference
└── tests/
    ├── test_modular_ax25.py
    └── ... legacy tests ...
```

## Module overview

- `lib/mx614.py`: MicroPython wrapper for MX614 pins and mode selection
- `lib/ticket.py`: pure Python builder for the fixed 16-byte telemetry ticket
- `lib/ax25.py`: pure Python AX.25 framing, FCS, bit stuffing, and NRZI logic
- `lib/transmitter.py`: non-blocking bit-level transmitter driven by `ticks_us()`
- `lib/sample_data.py`: deterministic telemetry dataset for repeatable tests
- `main.py`: Raspberry Pi Pico integration test loop for the MX614 path

## Telemetry dataset

The repository includes a small deterministic set of handcrafted telemetry
records in `lib/sample_data.py`. This dataset is used to:

- build repeatable protocol tests on CPython
- validate more than one telemetry example
- avoid relying on one hardcoded ticket only

Each record includes:

- `name`
- `user`
- `place`
- `sensor_id`
- `data`
- `observations`
- `day`
- `time`

`day` and `time` are already stored in the 3-byte thesis wire format so the
dataset directly exercises the real ticket builder.

## Current test goal

The current validation stage is:

1. Configure the MX614 for transmit mode at 1200 bps.
2. Build a 16-byte telemetry ticket from a sample record.
3. Wrap the ticket in an AX.25 UI frame.
4. Convert the frame to an AX.25 transmit bitstream.
5. NRZI-encode the bitstream.
6. Transmit it through `TXD` without blocking the main loop.
7. Keep reading `DET` and `RDY` while transmission runs.

## How to copy files to the Raspberry Pi Pico

Use whichever MicroPython workflow you prefer. Common options are:

- Thonny: copy `main.py` and the full `lib/` directory to the board
- MicroPico: sync the repository so `main.py` and `lib/` are copied
- `mpremote`, for example:

```bash
mpremote connect auto fs cp -r lib :
mpremote connect auto fs cp main.py :
```

## How to run

### Run CPython tests on your computer

From the repository root:

```bash
python3 -m unittest discover -s tests -v
```

### Run on the Raspberry Pi Pico

Once the files are copied to the board, run:

```python
import main
main.main()
```

If `main.py` is the board entrypoint in your setup, it may also run
automatically at boot.

## Configuring `main.py`

Near the top of `main.py`, you can edit:

- callsigns and SSIDs
- transmission interval
- test mode
- selected telemetry record name

Available test modes are:

- `fixed_1`
- `fixed_0`
- `alt_0101`
- `ax25`

## Oscilloscope measurement points

- Digital input test point: Pico `GP8` / `MX614 TXD`
- Analog FSK output: `MX614 TXOUT`
- System-level analog output toward the future radio path: `AUDIO_TX` at
  `RADIO_IF1`

`AUDIO_TX` should show the audio-frequency FSK waveform that would later feed
the radio interface.

## Expected results

For fixed-level validation:

- `TXD = 1` should produce approximately `1200 Hz` at `TXOUT` / `AUDIO_TX`
- `TXD = 0` should produce approximately `2200 Hz` at `TXOUT` / `AUDIO_TX`

For protocol validation:

- an AX.25 transmission should produce an FSK waveform whose tone transitions
  follow the NRZI-encoded frame data
- the main loop should remain responsive and continue monitoring `DET` and
  `RDY` during transmission

## Notes

- No blocking `sleep_ms()` or `sleep_us()` calls are used in the main transmit
  loop.
- Hardware-specific logic is separated from protocol logic to make unit testing
  easier.
- The AX.25 and ticket modules under `lib/` are compatible with normal CPython
  for local testing and thesis documentation.
