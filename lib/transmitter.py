"""Non-blocking bit-level transmitter for MicroPython.

This scheduler is intentionally simple. It uses software timing with
``ticks_us()`` so the rest of the main loop stays responsive. A future thesis
iteration can keep this interface and replace the backend with a more precise
PIO or timer-based implementation if needed.
"""

try:
    from time import ticks_diff, ticks_us
except ImportError:
    from time import monotonic_ns

    def ticks_us():
        return monotonic_ns() // 1000

    def ticks_diff(new_ticks, old_ticks):
        return new_ticks - old_ticks


class NonBlockingBitTransmitter:
    """Transmit logic levels with deterministic bit timing and no sleeps."""

    def __init__(self, set_level_callback, bit_time_us):
        if bit_time_us <= 0:
            raise ValueError("bit_time_us must be positive")

        self._set_level = set_level_callback
        self.bit_time_us = bit_time_us
        self._levels = []
        self._index = 0
        self._next_tick = None
        self._active = False

    def start(self, levels):
        if self._active:
            raise RuntimeError("transmitter is already active")

        self._levels = list(levels)
        self._index = 0

        if not self._levels:
            self._set_level(1)
            return

        self._active = True
        self._set_level(self._levels[0])
        self._index = 1
        self._next_tick = ticks_us() + self.bit_time_us

    def update(self):
        if not self._active:
            return False

        now = ticks_us()

        while self._active and ticks_diff(now, self._next_tick) >= 0:
            if self._index >= len(self._levels):
                self._set_level(1)
                self._active = False
                self._next_tick = None
                return True

            self._set_level(self._levels[self._index])
            self._index += 1
            self._next_tick += self.bit_time_us

        return self._active

    def is_active(self):
        return self._active
