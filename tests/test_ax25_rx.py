import unittest

from lib.ax25 import make_ax25_bitstream, make_ui_frame, nrzi_encode
from lib.ax25_rx import (
    bit_unstuff,
    decode_levels,
    nrzi_decode,
    parse_ui_frame,
)


class ReceiverTests(unittest.TestCase):
    def test_nrzi_round_trip(self):
        bits = [1, 0, 0, 1, 1, 0, 1]
        levels = nrzi_encode(bits, initial_level=1)
        self.assertEqual(nrzi_decode(levels, initial_level=1), bits)

    def test_bit_unstuff(self):
        self.assertEqual(bit_unstuff([1, 1, 1, 1, 1, 0, 1]), [1, 1, 1, 1, 1, 1])

    def test_decode_transmitted_frame_and_validate_fcs(self):
        payload = b"T#001,033,050,025,120,204,00000000"
        frame = make_ui_frame("NQNGND", 0, "UNCO", 3, payload)
        bitstream = make_ax25_bitstream(frame, preamble_flags=20, postamble_flags=3)
        levels = nrzi_encode(bitstream, initial_level=1)

        frames = decode_levels(levels, initial_level=1)
        self.assertEqual(len(frames), 1)
        packet = parse_ui_frame(frames[0])
        self.assertEqual(packet["source"], "UNCO")
        self.assertEqual(packet["source_ssid"], 3)
        self.assertEqual(packet["destination"], "NQNGND")
        self.assertEqual(packet["information"], payload)

    def test_corrupted_frame_is_rejected(self):
        payload = b"T#001,033,050,025,120,204,00000000"
        frame = bytearray(make_ui_frame("NQNGND", 0, "UNCO", 3, payload))
        frame[20] ^= 0x01
        bitstream = make_ax25_bitstream(bytes(frame), preamble_flags=20, postamble_flags=3)
        levels = nrzi_encode(bitstream, initial_level=1)
        self.assertEqual(decode_levels(levels, initial_level=1), [])


if __name__ == "__main__":
    unittest.main()
