import unittest

from ticket import Ticket


class LegacyTicketTests(unittest.TestCase):
    def test_ticket_serializes_to_16_bytes(self):
        ticket = Ticket(
            user=12345,
            place=1,
            sensor_id=2,
            data=56789,
            observations="Pehuensat III",
            day="220924",
            hour="200900",
        )

        ticket_data = ticket.to_bytes()

        self.assertEqual(ticket.user, 12345)
        self.assertEqual(ticket.place, 1)
        self.assertEqual(ticket.sensor_id, 2)
        self.assertEqual(len(ticket_data), 16)


if __name__ == "__main__":
    unittest.main()
