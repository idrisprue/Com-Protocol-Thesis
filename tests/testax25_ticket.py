from ticket import Ticket
from ax25 import AX25

def test_ax25_ticket():
    # Crear el ticket
    user = 1
    place = 2
    sensor_id = 3
    data = 1234
    observations = "Test"
    day = "010923"
    hour = "120000"

    ticket = Ticket(user=user, place=place, sensor_id=sensor_id, data=data, observations=observations, day=day, hour=hour)
    ticket_data = ticket.to_bytes()  # Asegúrate de que este método esté definido en tu clase Ticket

    # Crear la trama AX.25
    ax25 = AX25()
    ax25_struct = ax25.AX25Struct(
        src="SRCAD",      # Cambia esto según tu configuración
        src_ssid=0,
        dst="DESTAD",     # Cambia esto según tu configuración
        dst_ssid=0,
        control=0x03,     # Control para UI
        pid=0xF0,         # PID para no específico
        payload=ticket_data,
        cmd_msg=True
    )
    ax25_frame = ax25_struct.encode()

    # Codificar en HDLC
    hdlc_frame = ax25.hdlc_encode(ax25_frame)

    # Mostrar el resultado
    print("Trama AX.25 (hex):", [ax25.to_hex(byte) for byte in ax25_frame])
    print("Trama HDLC (hex):", [ax25.to_hex(byte) for byte in hdlc_frame])

if __name__ == "__main__":
    test_ax25_ticket()
