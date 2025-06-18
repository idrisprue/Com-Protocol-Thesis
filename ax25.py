import ustruct

class CRC16:
    """Clase para calcular el CRC-16."""
    def calculate(self, data: bytes) -> int:
        crc = 0xFFFF  # Valor inicial
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001  # Polinomio
                else:
                    crc >>= 1
        return crc

class Address:
    """Clase para gestionar direcciones AX.25."""
    @staticmethod
    def prepare(addr: str) -> bytearray:
        addr_field = bytearray()  # Inicializa un array de bytes vacío
        addr = addr[:6]  # Corta a 6 caracteres
        addr += ' ' * (6 - len(addr))  # Rellena con espacios si tiene menos de 6 caracteres
        for char in addr:
            addr_field.append(ord(char) << 1)  # Convierte cada carácter en su valor ASCII y lo desplaza 1 bit a la izquierda
        addr_field.append(0x00)  # Añade un byte de SSID (generalmente es 0 en AX.25)
        return addr_field  # Retorna la dirección convertida en un array de bytes

class AX25:
    """Clase para crear tramas AX.25."""
    def __init__(self, dest_address: str, source_address: str, payload: bytes):
        self.dest_address = Address.prepare(dest_address)
        self.source_address = Address.prepare(source_address)
        self.payload = payload
        self.control = b'\x03'  # Campo de control para tramas UI
        self.pid = b'\xf0'       # Identificador de protocolo
        self.crc_calculator = CRC16()

    def append_crc(self, frame: bytearray) -> bytearray:
        crc = self.crc_calculator.calculate(frame)  # Calcula el CRC de la trama
        # Añade el CRC empaquetado en 2 bytes (little-endian)
        return frame + bytearray([(crc & 0xFF), (crc >> 8) & 0xFF])

    def create_frame(self) -> bytearray:
        """Crea la trama completa incluyendo el CRC."""
        frame = self.dest_address + self.source_address + self.control + self.pid + self.payload
        # Añade el CRC
        return self.append_crc(frame)

# Ejemplo de uso:
# ax25_frame = AX25("DESTAD", "SRCAD", b"Hello")
# frame = ax25_frame.create_frame()
