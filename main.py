import time
from si4432 import Si4432
from ticket import Ticket
from ax25 import AX25

class RadioController:
    def __init__(self, spi, cs_pin, sdn_pin, int_pin):
        self.radio = Si4432(spi=spi, cs_pin=cs_pin, sdn_pin=sdn_pin, int_pin=int_pin)
        self.ax25 = AX25()  # Instancia de AX25

    def setup_radio(self):
        """Inicializa y configura el radio SI4432."""
        try:
            self.radio.initialize()
            self.radio.configure_baud_rate(9600)
            self.radio.configure_frequency(435)
            self.radio.begin_receiving()  # Inicia modo escucha
            print("Radio configurado correctamente.")
        except Exception as e:
            print(f"Error al configurar el radio: {e}")

    def send_ticket(self, user, place, sensor_id, data, observations, day, hour):
        """Crea y envía un ticket usando tramas AX.25."""
        try:
            # Crear el ticket
            ticket = Ticket(user=user, place=place, sensor_id=sensor_id, data=data, observations=observations, day=day, hour=hour)
            ticket_data = ticket.to_bytes()  # Cambia a create_frame() según tu implementación

            # Crear la trama AX.25
            ax25_struct = self.ax25.AX25Struct(
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
            hdlc_frame = self.ax25.hdlc_encode(ax25_frame)

            # Enviar la trama
            if self.radio.transmit_packet(hdlc_frame):
                print("Paquete enviado correctamente.")
            else:
                print("Error al enviar el paquete.")
        except Exception as e:
            print(f"Error durante el envío del ticket: {e}")

    def check_for_packets(self):
        """Verifica si se ha recibido un paquete."""
        if self.radio.check_if_packet_received():
            print("Paquete recibido.")
            packet = self.radio.retrieve_received_packet()  
            print(f"Datos recibidos: {packet}")

def main():
    # Inicializa la clase controladora del radio
    controller = RadioController(spi=1, cs_pin=17, sdn_pin=2, int_pin=20)

    # Configura el radio
    controller.setup_radio()

    # Bucle principal
    while True:
        # Envía un ticket cada cierto tiempo o cuando sea necesario
        controller.send_ticket(
            user=1,
            place=2,
            sensor_id=3,
            data=1234,
            observations="Test",
            day="010923",
            hour="120000"
        )

        # Verifica si se ha recibido un paquete
        controller.check_for_packets()

        #acá debería implementar interupciones después
        time.sleep(1) 

if __name__ == "__main__":
    main()
