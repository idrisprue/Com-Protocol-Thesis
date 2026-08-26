"""Punto final AX.25 conectado para pruebas con EasyTerm.

Implementa la parte necesaria para una prueba punto a punto:

    SABME/SABM -> UA -> trama I -> RR

También reconoce DISC y devuelve UA. No pretende ser todavía una pila AX.25
completa con reintentos, ventanas múltiples y temporizadores T1/T2/T3.
"""

try:
    from .ax25 import ax25_address, ax25_fcs, make_ax25_bitstream, nrzi_encode
    from .ax25_rx import parse_connected_frame
except ImportError:
    from ax25 import ax25_address, ax25_fcs, make_ax25_bitstream, nrzi_encode
    from ax25_rx import parse_connected_frame


CONTROL_SABM = 0x2F
CONTROL_SABME = 0x6F
CONTROL_DISC = 0x43
CONTROL_UA = 0x63
CONTROL_DM = 0x0F


class Ax25ConnectedEndpoint:
    """Estado mínimo de una estación AX.25 conectada."""

    def __init__(self, local_callsign, local_ssid=0):
        self.local_callsign = local_callsign
        self.local_ssid = local_ssid
        self.remote_callsign = None
        self.remote_ssid = 0
        self.connected = False
        self.modulo = 8
        self.send_sequence = 0
        self.receive_sequence = 0
        self.acknowledged_sequence = 0

    def _make_frame(self, control_bytes, information=b""):
        if self.remote_callsign is None:
            raise ValueError("no hay estación remota configurada")

        frame = bytearray()
        frame.extend(
            ax25_address(
                self.remote_callsign,
                self.remote_ssid,
                last=False,
            )
        )
        frame.extend(
            ax25_address(
                self.local_callsign,
                self.local_ssid,
                last=True,
            )
        )
        frame.extend(control_bytes)
        frame.extend(information)
        frame.extend(ax25_fcs(frame))
        return bytes(frame)

    def _make_ua(self, poll_final=0):
        control = CONTROL_UA | ((poll_final & 0x01) << 4)
        return self._make_frame(bytes((control,)))

    def _make_rr(self, poll_final=0):
        if self.modulo == 128:
            control = bytes((0x01, (self.receive_sequence << 1) | (poll_final & 0x01)))
        else:
            control = bytes(
                (
                    0x01
                    | ((poll_final & 0x01) << 4)
                    | ((self.receive_sequence & 0x07) << 5),
                )
            )
        return self._make_frame(control)

    def _make_rej(self, poll_final=0):
        if self.modulo == 128:
            control = bytes((0x09, (self.receive_sequence << 1) | (poll_final & 0x01)))
        else:
            control = bytes(
                (
                    0x09
                    | ((poll_final & 0x01) << 4)
                    | ((self.receive_sequence & 0x07) << 5),
                )
            )
        return self._make_frame(control)

    def handle_frame(self, frame):
        """Procesa una trama y devuelve ``(evento, respuestas, payload)``."""
        packet = parse_connected_frame(frame, modulo=self.modulo)
        self.remote_callsign = packet["source"]
        self.remote_ssid = packet["source_ssid"]
        frame_type = packet["frame_type"]
        responses = []
        payload = b""

        if frame_type == "SABME":
            self.modulo = 128
            self.connected = True
            self.send_sequence = 0
            self.receive_sequence = 0
            self.acknowledged_sequence = 0
            responses.append(self._make_ua(packet["poll_final"]))
            return "SABME recibido: conexión módulo 128 iniciada", responses, payload

        if frame_type == "SABM":
            self.modulo = 8
            self.connected = True
            self.send_sequence = 0
            self.receive_sequence = 0
            self.acknowledged_sequence = 0
            responses.append(self._make_ua(packet["poll_final"]))
            return "SABM recibido: conexión módulo 8 iniciada", responses, payload

        if frame_type == "DISC":
            responses.append(self._make_ua(packet["poll_final"]))
            self.connected = False
            return "DISC recibido: conexión finalizada", responses, payload

        if frame_type == "I":
            if not self.connected:
                responses.append(self._make_frame(bytes((CONTROL_DM,))))
                return "I recibido sin conexión: se responde DM", responses, payload

            self.acknowledged_sequence = packet["receive_sequence"]
            if packet["send_sequence"] != self.receive_sequence:
                responses.append(self._make_rej(packet["poll_final"]))
                return "I fuera de secuencia: se responde REJ", responses, payload

            payload = packet["information"]
            self.receive_sequence = (self.receive_sequence + 1) % self.modulo
            responses.append(self._make_rr(packet["poll_final"]))
            return "I recibida correctamente: se responde RR", responses, payload

        if frame_type in ("RR", "RNR", "REJ", "SREJ"):
            self.acknowledged_sequence = packet["receive_sequence"]
            if packet["poll_final"]:
                responses.append(self._make_rr(0))
            return frame_type + " recibido", responses, payload

        return frame_type + " recibido", responses, payload


def make_received_frame(destination, dest_ssid, source, source_ssid, control_bytes, information=b""):
    """Construye una trama AX.25 para pruebas del estado conectado."""
    frame = bytearray()
    frame.extend(ax25_address(destination, dest_ssid, last=False))
    frame.extend(ax25_address(source, source_ssid, last=True))
    frame.extend(control_bytes)
    frame.extend(information)
    frame.extend(ax25_fcs(frame))
    return bytes(frame)


def frame_to_nrzi_levels(frame, preamble_flags=20, postamble_flags=3):
    """Codifica una trama de respuesta para transmitirla por TXD."""
    bitstream = make_ax25_bitstream(
        frame,
        preamble_flags=preamble_flags,
        postamble_flags=postamble_flags,
    )
    return nrzi_encode(bitstream, initial_level=1)
