import unittest

from lib.ax25_connected import (
    Ax25ConnectedEndpoint,
    make_received_frame,
)
from lib.ax25_rx import parse_connected_frame


class ConnectedAx25Tests(unittest.TestCase):
    def test_sabme_gets_ua_response(self):
        endpoint = Ax25ConnectedEndpoint("NQNGND", 0)
        sabme = make_received_frame(
            destination="NQNGND",
            dest_ssid=0,
            source="UNCO",
            source_ssid=3,
            control_bytes=bytes((0x6F,)),
        )

        event, responses, payload = endpoint.handle_frame(sabme)

        self.assertIn("SABME", event)
        self.assertEqual(payload, b"")
        self.assertEqual(len(responses), 1)
        response = parse_connected_frame(responses[0], modulo=128)
        self.assertEqual(response["frame_type"], "UA")
        self.assertEqual(response["source"], "NQNGND")
        self.assertEqual(response["destination"], "UNCO")

    def test_extended_i_frame_gets_rr_response(self):
        endpoint = Ax25ConnectedEndpoint("NQNGND", 0)
        sabme = make_received_frame("NQNGND", 0, "UNCO", 3, bytes((0x6F,)))
        endpoint.handle_frame(sabme)

        information = b"mensaje de prueba"
        i_frame = make_received_frame(
            "NQNGND",
            0,
            "UNCO",
            3,
            bytes((0x00, 0x00)),
            information,
        )
        event, responses, payload = endpoint.handle_frame(i_frame)

        self.assertIn("I recibida", event)
        self.assertEqual(payload, information)
        self.assertEqual(len(responses), 1)
        response = parse_connected_frame(responses[0], modulo=128)
        self.assertEqual(response["frame_type"], "RR")
        self.assertEqual(response["receive_sequence"], 1)


if __name__ == "__main__":
    unittest.main()
