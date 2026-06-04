"""Small bench demo for sending one repeating AX.25 transmission.

This file is intentionally separate from main.py so the oscilloscope test can
stay simple and explicit during bench bring-up.
"""

try:
    from lib.ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
    from lib.mx614 import MX614
    from lib.sample_data import get_sample_record
    from lib.ticket import make_ticket
    from lib.transmitter import NonBlockingBitTransmitter
except ImportError:
    from ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
    from mx614 import MX614
    from sample_data import get_sample_record
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


def build_levels():
    record = get_sample_record(SELECTED_RECORD_NAME)
    ticket = make_ticket(
        user=record["user"],
        place=record["place"],
        sensor_id=record["sensor_id"],
        data=record["data"],
        observations=record["observations"],
        day=record["day"],
        time=record["time"],
    )

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

    return levels, {
        "record_name": record["name"],
        "ticket_length": len(ticket),
        "frame_length": len(frame),
        "bitstream_length": len(bitstream),
        "levels_length": len(levels),
    }


def main():
    mx = MX614(
        txd_pin=8,
        rxd_pin=9,
        rdy_pin=10,
        det_pin=11,
        m0_pin=12,
        m1_pin=13,
    )
    mx.set_tx_1200()

    tx = NonBlockingBitTransmitter(mx.set_txd, BIT_TIME_US)
    levels, info = build_levels()

    print("AX.25 demo ready")
    print("record:", info["record_name"])
    print("ticket bytes:", info["ticket_length"])
    print("frame bytes:", info["frame_length"])
    print("bitstream bits:", info["bitstream_length"])
    print("output levels:", info["levels_length"])
    print("RDY =", mx.read_rdy())
    print("DET =", mx.read_det())
    print("Repeating one AX.25 burst every", TX_INTERVAL_MS, "ms")

    last_start = ticks_ms() - TX_INTERVAL_MS

    while True:
        now = ticks_ms()

        if (not tx.is_active()) and ticks_diff(now, last_start) >= TX_INTERVAL_MS:
            print("starting AX.25 burst")
            tx.start(levels)
            last_start = now

        was_active = tx.is_active()
        tx.update()
        if was_active and not tx.is_active():
            print("AX.25 burst ended")


if __name__ == "__main__":
    main()
