"""Root-level compatibility copy for Pico sync tools."""

from machine import Pin


class MX614:
    def __init__(self, txd_pin, rxd_pin, rdy_pin, det_pin, m0_pin, m1_pin):
        self.txd = Pin(txd_pin, Pin.OUT, value=1)
        self.rxd = Pin(rxd_pin, Pin.IN)
        self.rdy = Pin(rdy_pin, Pin.IN)
        self.det = Pin(det_pin, Pin.IN)
        self.m0 = Pin(m0_pin, Pin.OUT, value=0)
        self.m1 = Pin(m1_pin, Pin.OUT, value=0)

    def set_tx_1200(self):
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
