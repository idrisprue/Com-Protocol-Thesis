"""Minimal MX614 hardware wrapper for MicroPython.

This module only models the digital control and status pins used during the
Pico + MX614 validation stage. The selected mode and tone mapping are kept
explicit in code, but they should be treated as provisional until oscilloscope
measurements confirm the expected behavior on the assembled hardware.
"""

from machine import Pin


class MX614:
    """Access the digital control and status pins of the MX614 modem."""

    def __init__(self, txd_pin, rxd_pin, rdy_pin, det_pin, m0_pin, m1_pin):
        self.txd = Pin(txd_pin, Pin.OUT, value=1)
        self.rxd = Pin(rxd_pin, Pin.IN)
        self.rdy = Pin(rdy_pin, Pin.IN)
        self.det = Pin(det_pin, Pin.IN)
        self.m0 = Pin(m0_pin, Pin.OUT, value=0)
        self.m1 = Pin(m1_pin, Pin.OUT, value=0)

    def set_tx_1200(self):
        """Select the provisional Bell 202 transmit mode used in this branch.

        The current implementation drives M0=1 and M1=0, following the thesis
        assumption for 1200 bps transmit validation. That mapping should still
        be checked on the bench with the MX614 datasheet and oscilloscope.
        """
        self.m0.value(1)
        self.m1.value(0)

    def set_txd(self, level):
        self.txd.value(1 if level else 0)

    def read_rxd(self):
        return self.rxd.value()

    def read_rdy(self):
        return self.rdy.value()

    def read_det(self):
        return self.det.value()
