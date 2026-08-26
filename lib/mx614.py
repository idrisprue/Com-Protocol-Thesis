"""Control digital del módem MX614 para MicroPython.

La entrada CLK del MX614 no es controlada por esta clase. Para usar RXD como
salida de datos demodulados en forma directa, CLK debe estar conectado al nivel
previsto por el esquema y el datasheet.
"""

from machine import Pin


class MX614:
    """Acceso a los pines de control y estado del módem MX614."""

    def __init__(self, txd_pin, rxd_pin, rdy_pin, det_pin, m0_pin, m1_pin):
        self.txd = Pin(txd_pin, Pin.OUT, value=1)
        self.rxd = Pin(rxd_pin, Pin.IN)
        self.rdy = Pin(rdy_pin, Pin.IN)
        self.det = Pin(det_pin, Pin.IN)
        self.m0 = Pin(m0_pin, Pin.OUT, value=0)
        self.m1 = Pin(m1_pin, Pin.OUT, value=0)

    def set_tx_1200(self):
        """Selecciona transmisión Bell 202 a 1200 bit/s: M0=1, M1=0."""
        self.m0.value(1)
        self.m1.value(0)

    def set_rx_1200(self):
        """Selecciona recepción Bell 202 a 1200 bit/s: M0=0, M1=0."""
        self.m0.value(0)
        self.m1.value(0)

    def set_txd(self, level):
        self.txd.value(1 if level else 0)

    def read_rxd(self):
        return self.rxd.value()

    def read_rdy(self):
        return self.rdy.value()

    def read_det(self):
        return self.det.value()
