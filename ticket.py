## Ticket creation 16 bytes ##
## 2 bytes - user ##
## 1 byte - place ##
## 1 byte - sensor ID ##
## 2 bytes - data ##
## 4 bytes - observations ##
## 3 bytes - day (DDMMYY) ##
## 3 bytes - time (HHMMSS) ##

# ustruct -> > big-endian, MSB se almacenan primero
# H -> entero sin signo de 2 bytes
# B -> entero sin signo de 1 byte
# 4s o 3s -> cadena de 4 o 3 bytes

## Ticket creation 16 bytes ##
## 2 bytes - user ##
## 1 byte - place ##
## 1 byte - sensor ID ##
## 2 bytes - data ##
## 4 bytes - observations ##
## 3 bytes - day (DDMMYY) ##
## 3 bytes - time (HHMMSS) ##

# ustruct -> > big-endian, MSB se almacenan primero
# H -> entero sin signo de 2 bytes
# B -> entero sin signo de 1 byte
# 4s o 3s -> cadena de 4 o 3 bytes

import ustruct

class Ticket:
    """Clase para crear un ticket de información de 16 bytes."""

    def __init__(self, user: int, place: int, sensor_id: int, data: int, observations: str, day: str, hour: str):
        self.user = self._validate_user(user)
        self.place = self._validate_place(place)
        self.sensor_id = self._validate_sensor_id(sensor_id)
        self.data = data
        self.observations = observations
        self.day = day
        self.hour = hour

    def _validate_user(self, user: int) -> int:
        if not (0 <= user <= 65535):  # Valida el rango para 2 bytes
            raise ValueError("User must be between 0 and 65535")
        return user

    def _validate_place(self, place: int) -> int:
        if not (0 <= place <= 255):  # Valida el rango para 1 byte
            raise ValueError("Place must be between 0 and 255")
        return place

    def _validate_sensor_id(self, sensor_id: int) -> int:
        if not (0 <= sensor_id <= 255):  # Valida el rango para 1 byte
            raise ValueError("Sensor ID must be between 0 and 255")
        return sensor_id

    def to_bytes(self) -> bytearray:
        """Crea un ticket de información de 16 bytes."""
        ticket = bytearray()

        # Agrega los datos al ticket
        ticket.extend(ustruct.pack('>H', self.user))  # Usuario (2 bytes)
        ticket.extend(ustruct.pack('>B', self.place))  # Lugar (1 byte)
        ticket.extend(ustruct.pack('>B', self.sensor_id))  # Sensor ID (1 byte)
        ticket.extend(ustruct.pack('>H', self.data))  # Datos (2 bytes)

        obs_bytes = self._truncate_observations(self.observations)
        ticket.extend(obs_bytes)  # Agrega las observaciones al ticket

        ticket.extend(ustruct.pack('>3s', self.day.encode('utf-8')))  # Día (3 bytes)
        ticket.extend(ustruct.pack('>3s', self.hour.encode('utf-8')))  # Hora (3 bytes)

        return ticket

    def _truncate_observations(self, observations: str) -> bytearray:
        """Trunca las observaciones a 4 bytes y rellena con ceros."""
        obs_bytes = observations.encode('utf-8')[:4]  # Trunca a 4 bytes
        obs_bytes += b'\x00' * (4 - len(obs_bytes))  # Rellena con ceros si es necesario
        
        return bytearray(obs_bytes)
    
    