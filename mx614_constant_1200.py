"""Simple bench test: keep TXD fixed to request the low Bell 202 tone.

This file is intentionally minimal and blocking because it is only meant for
oscilloscope bring-up. It is not part of the final non-blocking protocol path.
"""

try:
    from lib.mx614 import MX614
except ImportError:
    from mx614 import MX614

from time import sleep


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
    mx.set_txd(1)

    print("MX614 constant tone test")
    print("Mode pins: M0=1, M1=0")
    print("TXD fixed at 1")
    print("Expected tone: approximately 1200 Hz if the current assumption is correct")
    print("RDY =", mx.read_rdy())
    print("DET =", mx.read_det())

    while True:
        sleep(1)


if __name__ == "__main__":
    main()
