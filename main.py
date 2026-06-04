"""Non-blocking Raspberry Pi Pico test for the MX614 transmit path.

This branch makes the Pico + MX614 validation path the default executable path.

On the Pico, some sync tools upload the `lib/` modules into the filesystem root
instead of preserving the package directory. To keep bench testing simple, this
entrypoint first tries the package imports and then falls back to root-level
modules when needed.
"""

try:
    from lib.ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
    from lib.mx614 import MX614
    from lib.sample_data import SAMPLE_RECORDS, get_sample_record
    from lib.ticket import make_ticket
    from lib.transmitter import NonBlockingBitTransmitter
except ImportError:
    from ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
    from mx614 import MX614
    from sample_data import SAMPLE_RECORDS, get_sample_record
    from ticket import make_ticket
    from transmitter import NonBlockingBitTransmitter

try:
    from time import ticks_diff, ticks_ms
except ImportError:
    from time import monotonic_ns

    def ticks_ms():
        return monotonic_ns() // 1000000

    def ticks_diff(new_ticks, old_ticks):
        return new_ticks - old_ticks


BIT_RATE_BPS = 1200
BIT_TIME_US = int(1000000 / BIT_RATE_BPS)
TX_INTERVAL_MS = 5000
PREAMBLE_FLAGS = 20
POSTAMBLE_FLAGS = 3

DESTINATION_CALLSIGN = "GROUND"
DESTINATION_SSID = 0
SOURCE_CALLSIGN = "PICO"
SOURCE_SSID = 0
SELECTED_RECORD_NAME = "payload_nominal_1"
TEST_MODE = "ax25"

MX614_TX_1200_MODE = {
    "m0": 1,
    "m1": 0,
    "status": "provisional until oscilloscope validation",
}


def build_ticket_from_record(record):
    return make_ticket(
        user=record["user"],
        place=record["place"],
        sensor_id=record["sensor_id"],
        data=record["data"],
        observations=record["observations"],
        day=record["day"],
        time=record["time"],
    )


def build_ax25_levels_from_record(record):
    ticket = build_ticket_from_record(record)
    frame = make_ui_frame(
        destination=DESTINATION_CALLSIGN,
        dest_ssid=DESTINATION_SSID,
        source=SOURCE_CALLSIGN,
        source_ssid=SOURCE_SSID,
        payload=ticket,
    )
    bitstream = make_ax25_bitstream(
        frame,
        preamble_flags=PREAMBLE_FLAGS,
        postamble_flags=POSTAMBLE_FLAGS,
    )
    levels = nrzi_encode(bitstream, initial_level=1)

    diagnostics = {
        "record_name": record["name"],
        "ticket_length": len(ticket),
        "frame_length": len(frame),
        "bitstream_length": len(bitstream),
        "levels_length": len(levels),
    }
    return ticket, frame, bitstream, levels, diagnostics


def make_alternating_levels(length_bits=120):
    bits = [bit_index % 2 for bit_index in range(length_bits)]
    return nrzi_encode(bits, initial_level=1)


def build_test_levels(mode, record_name):
    if mode == "fixed_1":
        return [1] * 1200, {"mode": "fixed_1", "description": "constant TXD high"}
    if mode == "fixed_0":
        return [0] * 1200, {"mode": "fixed_0", "description": "constant TXD low"}
    if mode == "alt_0101":
        levels = make_alternating_levels(length_bits=240)
        return levels, {"mode": "alt_0101", "description": "alternating pattern at 1200 bps"}
    if mode == "ax25":
        record = get_sample_record(record_name)
        _, _, _, levels, diagnostics = build_ax25_levels_from_record(record)
        diagnostics["mode"] = "ax25"
        diagnostics["description"] = "AX.25 UI frame transmission"
        return levels, diagnostics
    raise ValueError("unsupported TEST_MODE: %s" % mode)


def main():
    modem = MX614(
        txd_pin=8,
        rxd_pin=9,
        rdy_pin=10,
        det_pin=11,
        m0_pin=12,
        m1_pin=13,
    )
    modem.set_tx_1200()

    # Digital TXD can be measured at Pico GP8 / MX614 TXD.
    # Analog FSK can be measured at MX614 TXOUT or AUDIO_TX on RADIO_IF1.
    # The current assumption is TXD=1 -> about 1200 Hz and TXD=0 -> about
    # 2200 Hz in this mode, but that should be confirmed on the bench.
    transmitter = NonBlockingBitTransmitter(modem.set_txd, BIT_TIME_US)
    levels, diagnostics = build_test_levels(TEST_MODE, SELECTED_RECORD_NAME)

    print("MX614 mode pins:", MX614_TX_1200_MODE)
    print("available records:", len(SAMPLE_RECORDS))
    print("test mode:", diagnostics["mode"])
    print("description:", diagnostics["description"])
    if diagnostics["mode"] == "ax25":
        print("selected record:", diagnostics["record_name"])
        print("ticket length:", diagnostics["ticket_length"])
        print("AX.25 frame length without flags:", diagnostics["frame_length"])
        print("bits after flags/stuffing:", diagnostics["bitstream_length"])
        print("NRZI levels:", diagnostics["levels_length"])
    else:
        print("levels for test mode:", len(levels))

    last_tx_start = ticks_ms() - TX_INTERVAL_MS
    last_det = modem.read_det()
    last_rdy = modem.read_rdy()

    print("DET initial:", last_det)
    print("RDY initial:", last_rdy)

    while True:
        now = ticks_ms()

        if (not transmitter.is_active()) and ticks_diff(now, last_tx_start) >= TX_INTERVAL_MS:
            print("starting transmission")
            transmitter.start(levels)
            last_tx_start = now

        was_active = transmitter.is_active()
        transmitter.update()
        if was_active and not transmitter.is_active():
            print("transmission ended")

        det = modem.read_det()
        if det != last_det:
            last_det = det
            print("DET changed:", det)

        rdy = modem.read_rdy()
        if rdy != last_rdy:
            last_rdy = rdy
            print("RDY changed:", rdy)


if __name__ == "__main__":
    main()
