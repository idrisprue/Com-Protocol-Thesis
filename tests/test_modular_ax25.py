import unittest

from lib.ax25 import (
    FLAG_BYTE,
    ax25_address,
    ax25_fcs,
    bit_stuff,
    byte_to_bits_lsb_first,
    make_ax25_bitstream,
    make_ui_frame,
    nrzi_encode,
)
from lib.sample_data import SAMPLE_RECORDS, get_sample_record
from lib.ticket import make_ticket
from lib.transmitter import NonBlockingBitTransmitter


class TicketTests(unittest.TestCase):
    def test_ticket_is_16_bytes(self):
        record = get_sample_record("payload_nominal_1")
        ticket = make_ticket(
            user=record["user"],
            place=record["place"],
            sensor_id=record["sensor_id"],
            data=record["data"],
            observations=record["observations"],
            day=record["day"],
            time=record["time"],
        )
        self.assertEqual(len(ticket), 16)

    def test_out_of_range_values_raise(self):
        with self.assertRaises(ValueError):
            make_ticket(65536, 1, 1, 1, 1, b"\x01\x01\x26", b"\x00\x00\x00")
        with self.assertRaises(ValueError):
            make_ticket(1, 256, 1, 1, 1, b"\x01\x01\x26", b"\x00\x00\x00")
        with self.assertRaises(ValueError):
            make_ticket(1, 1, 256, 1, 1, b"\x01\x01\x26", b"\x00\x00\x00")
        with self.assertRaises(ValueError):
            make_ticket(1, 1, 1, 65536, 1, b"\x01\x01\x26", b"\x00\x00\x00")
        with self.assertRaises(ValueError):
            make_ticket(1, 1, 1, 1, 4294967296, b"\x01\x01\x26", b"\x00\x00\x00")

    def test_all_sample_records_build_16_byte_tickets(self):
        for record in SAMPLE_RECORDS:
            ticket = make_ticket(
                user=record["user"],
                place=record["place"],
                sensor_id=record["sensor_id"],
                data=record["data"],
                observations=record["observations"],
                day=record["day"],
                time=record["time"],
            )
            self.assertEqual(len(ticket), 16, record["name"])


class AX25Tests(unittest.TestCase):
    def test_address_length_is_7_bytes(self):
        self.assertEqual(len(ax25_address("PICO", 0, last=True)), 7)

    def test_callsign_padding_and_encoding(self):
        address = ax25_address("PICO", 0, last=True)
        self.assertEqual(address[:4], bytes([ord("P") << 1, ord("I") << 1, ord("C") << 1, ord("O") << 1]))
        self.assertEqual(address[4:6], bytes([ord(" ") << 1, ord(" ") << 1]))
        self.assertEqual(address[6] & 0x01, 0x01)

    def test_ui_frame_contains_fields_and_fcs(self):
        payload = b"0123456789ABCDEF"
        frame = make_ui_frame("GROUND", 0, "PICO", 0, payload)
        self.assertEqual(frame[:7], ax25_address("GROUND", 0, last=False))
        self.assertEqual(frame[7:14], ax25_address("PICO", 0, last=True))
        self.assertEqual(frame[14], 0x03)
        self.assertEqual(frame[15], 0xF0)
        self.assertEqual(frame[16:32], payload)
        self.assertEqual(frame[-2:], ax25_fcs(frame[:-2]))

    def test_all_sample_records_become_valid_frames(self):
        frames = []
        for record in SAMPLE_RECORDS:
            ticket = make_ticket(
                user=record["user"],
                place=record["place"],
                sensor_id=record["sensor_id"],
                data=record["data"],
                observations=record["observations"],
                day=record["day"],
                time=record["time"],
            )
            frame = make_ui_frame("GROUND", 0, "PICO", 0, ticket)
            self.assertEqual(frame[-2:], ax25_fcs(frame[:-2]))
            frames.append(frame)
        self.assertGreater(len({frame for frame in frames}), 1)

    def test_fcs_is_two_bytes(self):
        self.assertEqual(len(ax25_fcs(b"ABC")), 2)

    def test_bit_stuff_inserts_zero_after_five_ones(self):
        bits = [1, 1, 1, 1, 1, 1]
        stuffed = bit_stuff(bits)
        self.assertEqual(stuffed, [1, 1, 1, 1, 1, 0, 1])

    def test_byte_bits_are_lsb_first(self):
        self.assertEqual(byte_to_bits_lsb_first(0x96), [0, 1, 1, 0, 1, 0, 0, 1])

    def test_bitstream_adds_flags_without_stuffing_them(self):
        frame = b"\xFF"
        bitstream = make_ax25_bitstream(frame, preamble_flags=1, postamble_flags=1)
        flag_bits = byte_to_bits_lsb_first(FLAG_BYTE)
        self.assertEqual(bitstream[:8], flag_bits)
        self.assertEqual(bitstream[-8:], flag_bits)

    def test_nrzi_encoding(self):
        bits = [1, 0, 0, 1]
        self.assertEqual(nrzi_encode(bits, initial_level=1), [1, 0, 1, 1])


class TransmitterTests(unittest.TestCase):
    def test_transmitter_handles_empty_sequence(self):
        seen = []
        tx = NonBlockingBitTransmitter(seen.append, 100)
        tx.start([])
        self.assertEqual(seen, [1])
        self.assertFalse(tx.is_active())

    def test_transmitter_rejects_double_start(self):
        seen = []
        tx = NonBlockingBitTransmitter(seen.append, 1_000_000)
        tx.start([1, 0])
        with self.assertRaises(RuntimeError):
            tx.start([1])

    def test_transmitter_finishes_and_returns_to_idle_high(self):
        seen = []
        tx = NonBlockingBitTransmitter(seen.append, 1)
        tx.start([1, 0, 1])

        for _ in range(10000):
            tx.update()
            if not tx.is_active():
                break

        self.assertFalse(tx.is_active())
        self.assertEqual(seen[0], 1)
        self.assertEqual(seen[-1], 1)


if __name__ == "__main__":
    unittest.main()
