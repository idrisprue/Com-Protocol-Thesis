from machine import Pin, SPI
import time
import math

class Si4432:
    # Definiciones de tipos de modulación disponibles
    class ModulationType:
        NONE = 0x00
        OOK = 0x01
        FSK = 0x02
        GFSK = 0x03
    
    # Modos de operación del SI4432
    class OperationMode:
        StandbyMode = 0x00
        SleepMode = 0x10
        Ready = 0x01
        TuneMode = 0x02
        RXMode = 0x04
        TXMode = 0x08
        Reset = 0x80

    # Direcciones de registros del SI4432
    REG_DEV_TYPE = 0x00
    REG_DEV_VERSION = 0x01
    REG_DEV_STATUS = 0x02
    REG_INT_STATUS1 = 0x03
    REG_INT_STATUS2 = 0x04
    REG_INT_ENABLE1 = 0x05
    REG_INT_ENABLE2 = 0x06
    REG_STATE = 0x07
    REG_OPERATION_CONTROL = 0x08
    REG_GPIO0_CONF = 0x0B
    REG_GPIO1_CONF = 0x0C
    REG_GPIO2_CONF = 0x0D
    REG_IOPORT_CONF = 0x0E
    REG_IF_FILTER_BW = 0x1C
    REG_AFC_LOOP_GEARSHIFT_OVERRIDE = 0x1D
    REG_AFC_TIMING_CONTROL = 0x1E
    REG_CLOCK_RECOVERY_GEARSHIFT = 0x1F
    REG_CLOCK_RECOVERY_OVERSAMPLING = 0x20
    REG_CLOCK_RECOVERY_OFFSET2 = 0x21
    REG_CLOCK_RECOVERY_OFFSET1 = 0x22
    REG_CLOCK_RECOVERY_OFFSET0 = 0x23
    REG_CLOCK_RECOVERY_TIMING_GAIN1 = 0x24
    REG_CLOCK_RECOVERY_TIMING_GAIN0 = 0x25
    REG_RSSI = 0x26
    REG_RSSI_THRESHOLD = 0x27
    REG_AFC_LIMITER = 0x2A
    REG_AFC_CORRECTION_READ = 0x2B
    REG_DATAACCESS_CONTROL = 0x30
    REG_EZMAC_STATUS = 0x31
    REG_HEADER_CONTROL1 = 0x32
    REG_HEADER_CONTROL2 = 0x33
    REG_PREAMBLE_LENGTH = 0x34
    REG_PREAMBLE_DETECTION = 0x35
    REG_SYNC_WORD3 = 0x36
    REG_SYNC_WORD2 = 0x37
    REG_SYNC_WORD1 = 0x38
    REG_SYNC_WORD0 = 0x39
    REG_TRANSMIT_HEADER3 = 0x3A
    REG_TRANSMIT_HEADER2 = 0x3B
    REG_TRANSMIT_HEADER1 = 0x3C
    REG_TRANSMIT_HEADER0 = 0x3D
    REG_PKG_LEN = 0x3E
    REG_CHECK_HEADER3 = 0x3F
    REG_CHECK_HEADER2 = 0x40
    REG_CHECK_HEADER1 = 0x41
    REG_CHECK_HEADER0 = 0x42
    REG_RECEIVED_HEADER3 = 0x47
    REG_RECEIVED_HEADER2 = 0x48
    REG_RECEIVED_HEADER1 = 0x49
    REG_RECEIVED_HEADER0 = 0x4A
    REG_RECEIVED_LENGTH = 0x4B
    REG_CHARGEPUMP_OVERRIDE = 0x58
    REG_DIVIDER_CURRENT_TRIM = 0x59
    REG_VCO_CURRENT_TRIM = 0x5A
    REG_AGC_OVERRIDE = 0x69
    REG_TX_POWER = 0x6D
    REG_TX_DATARATE1 = 0x6E
    REG_TX_DATARATE0 = 0x6F
    REG_MODULATION_MODE1 = 0x70
    REG_MODULATION_MODE2 = 0x71
    REG_FREQ_DEVIATION = 0x72
    REG_FREQ_OFFSET1 = 0x73
    REG_FREQ_OFFSET2 = 0x74
    REG_FREQBAND = 0x75
    REG_FREQCARRIER_H = 0x76
    REG_FREQCARRIER_L = 0x77
    REG_FREQCHANNEL = 0x79
    REG_CHANNEL_STEPSIZE = 0x7A
    REG_FIFO = 0x7F

    # Constantes
    MAX_TRANSMIT_TIMEOUT = 200  # ms
    
    def __init__(self, spi, cs_pin, sdn_pin=None, int_pin=None):
         # Inicialización de pines y configuración SPI
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT) #Pin CS (CHIP SELECT) como salida
        self.cs.value(1) 
        self.sdn = Pin(sdn_pin, Pin.OUT) if sdn_pin is not None else None
        self.int_pin = Pin(int_pin, Pin.IN) if int_pin is not None else None

        # Configuración de parámetros iniciales
        self.freq_carrier = 433.0 # Frecuencia portadora en MHz
        self.kbps = 100 # Tasa de datos en kbps
        self.freq_channel = 0
        self.modulation_type = self.ModulationType.FSK # Tipo de modulación por defecto
        self.idle_mode = self.OperationMode.Ready
        self.transmit_power = 7
        # Configuraciones adicionales
        self.direct_tie = True
        self.manchester_enabled = False
        self.manchester_inverted = False
        self.packet_handling_enabled = True
        self.lsb_first = False
        self.send_blocking = True
        self.package_sign = 0xDEAD
        self.send_start = 0

    def initialize(self):
        # Inicialización del módulo SI4432
        if self.sdn:
            self.sdn.value(0)  #Activar el chip
        else:
            time.sleep_ms(50) #Esperar si no hay pin SDN

        self.reset()

        # Verificar la palabra de sincronización
        sync_word = self.burst_read(self.REG_SYNC_WORD3, 4)
        if sync_word != b'\x2D\xD4\x00\x00':
            return False # Fallo en la sincronización

        return True

    def reset(self, soft=False):
        # Reiniciar el módulo, ya sea en modo suave o duro
        if soft or self.sdn is None:
            self.set_operation_mode(self.OperationMode.Ready)
            self.set_operation_mode(self.OperationMode.Reset)
        else:
            self.turn_off()
            time.sleep_ms(1)
            self.turn_on()
            time.sleep_ms(15)

        # Esperar hasta que el reloj esté listo
        timeout = 15
        while not self.is_clock_ready() and timeout > 0:
            time.sleep_ms(1)
            timeout -= 1

        if timeout > 0:
            self.boot()
            return True
        return False

    def boot(self):
        # Configuración inicial después del reinicio
        self.write_register(self.REG_AFC_TIMING_CONTROL, 0x02)
        self.write_register(self.REG_AFC_LIMITER, 0xFF)
        self.write_register(self.REG_AGC_OVERRIDE, 0x60)
        self.write_register(self.REG_AFC_LOOP_GEARSHIFT_OVERRIDE, 0x3C)

        # Configuración de manejo de paquetes
        if self.packet_handling_enabled:
            self.write_register(self.REG_DATAACCESS_CONTROL, 0xAD | (0x40 if self.lsb_first else 0))
            self.write_register(self.REG_HEADER_CONTROL1, 0x0C)
            self.write_register(self.REG_HEADER_CONTROL2, 0x22)
            self.write_register(self.REG_PREAMBLE_LENGTH, 0x08)
            self.write_register(self.REG_PREAMBLE_DETECTION, 0x3A)
            self.set_comms_signature(self.package_sign)
        else:
            self.write_register(self.REG_DATAACCESS_CONTROL, 0x40 if self.lsb_first else 0)

        self.write_register(self.REG_CHANNEL_STEPSIZE, 0x64)

        # Configuración de frecuencia, tasa de baudios y potencia de transmisión
        self.configure_frequency(self.freq_carrier)
        self.configure_baud_rate(self.kbps)
        self.set_channel(self.freq_channel)
        self.set_transmit_power(self.transmit_power, self.direct_tie)

        self.set_operation_mode(self.idle_mode)

    def set_operation_mode(self, mode):
        # Cambiar el modo de operación del módulo
        self.write_register(self.REG_STATE, mode)

    def write_register(self, reg, value):
        # Escribir un valor en un registro específico
        self.burst_write(reg, bytes([value]))

    def burst_write(self, start_reg, data):
        #Escribir múltiples bytes en un registro (en ráfaga)
        self.cs.value(0)
        self.spi.write(bytes([start_reg | 0x80]))
        self.spi.write(data)
        self.cs.value(1)

    def burst_read(self, start_reg, length):
        #Lectura en ráfaga
        self.cs.value(0)
        self.spi.write(bytes([start_reg & 0x7F]))
        result = self.spi.read(length)
        self.cs.value(1)
        return result

    def configure_frequency(self, frequency):
        # Configurar la frecuencia portadora
        if 240 <= frequency <= 930:
            self.freq_carrier = frequency
            high_band = 1 if frequency >= 480 else 0
            f_part = frequency / (10 * (high_band + 1)) - 24
            freq_band = int(f_part)
            freq_carrier = int((f_part - freq_band) * 64000)
            
            vals = bytes([(1 << 6) | (high_band << 5) | (freq_band & 0x3F),
                          (freq_carrier >> 8) & 0xFF,
                          freq_carrier & 0xFF])
            self.burst_write(self.REG_FREQBAND, vals)

    def set_channel(self, channel):
        #Configurar el canal de operación
        self.freq_channel = channel
        self.write_register(self.REG_FREQCHANNEL, channel)

    def configure_baud_rate(self, kbps):
        #Configurar la tasa de baudios
        if 1 <= kbps <= 256:
            self.kbps = kbps
            
            modulation_mode1 = ((1 << 5) if kbps < 30 else 0) | \
                               ((1 << 2) if self.manchester_inverted else 0) | \
                               ((1 << 1) if self.manchester_enabled else 0)
            modulation_mode2 = 0x23 if self.modulation_type == self.ModulationType.GFSK else 0x21
            freq_dev = round(((15 if kbps <= 10 else 150) * 1000.0) / 625.0)
            
            self.burst_write(self.REG_MODULATION_MODE1, bytes([modulation_mode1, modulation_mode2, freq_dev]))
            
            bps_reg_val = round((kbps * (1 << 21 if kbps < 30 else 1 << 16)) / 1000)
            self.burst_write(self.REG_TX_DATARATE1, bytes([(bps_reg_val >> 8) & 0xFF, bps_reg_val & 0xFF]))
            
            # Set RX timings (simplified)
            self.write_register(self.REG_IF_FILTER_BW, 0x01)  # Placeholder value
            

    def set_transmit_power(self, level, direct_tie=True):
        #The output power is configurable in 3 dB steps from +11 dBm to +20 dBm
        # with the txpow[1:0] field in "Register6Dh. TX Power".
        #Configurar la potencia de tranmisión
        self.transmit_power = min(level, 7) #7 es la máx potencia
        self.direct_tie = direct_tie
        self.write_register(self.REG_TX_POWER, 0x10 | (0x10 if direct_tie else 0) | (level & 0x7))

    def set_comms_signature(self, signature):
        self.package_sign = signature
        self.write_register(self.REG_TRANSMIT_HEADER3, signature >> 8)
        self.write_register(self.REG_TRANSMIT_HEADER2, signature & 0xFF)
        self.write_register(self.REG_CHECK_HEADER3, signature >> 8)
        self.write_register(self.REG_CHECK_HEADER2, signature & 0xFF)

    def transmit_packet(self, data):
        if len(data) <= 64:
            self.clear_tx_fifo()
            self.write_register(self.REG_PKG_LEN, len(data))
            self.burst_write(self.REG_FIFO, data)
            
            self.enable_interrupt(0x04)  # INT_PKSENT
            self.get_int_status()  # Clear interrupts
            
            self.set_operation_mode(self.idle_mode | self.OperationMode.TXMode)
            self.send_start = time.ticks_ms()
            
            if self.send_blocking:
                return self.wait_transmit_completed()
            return True
        return False

    def wait_transmit_completed(self):
        while time.ticks_diff(time.ticks_ms(), self.send_start) < self.MAX_TRANSMIT_TIMEOUT:
            if self.int_pin and self.int_pin.value() == 0:
                continue
            
            int_status = self.get_int_status()
            if int_status & 0x04:  # INT_PKSENT
                return True
            time.sleep_ms(1)
        return False

    def begin_receiving(self):
        self.clear_rx_fifo()
        self.enable_interrupt(0x03)  # INT_PKVALID | INT_CRCERROR
        self.get_int_status()
        self.set_operation_mode(self.idle_mode | self.OperationMode.RXMode)

    def check_if_packet_received(self):
        if self.int_pin and self.int_pin.value() == 1:
            return False
        
        int_status = self.get_int_status()
        if int_status & 0x02:  # INT_PKVALID
            self.set_operation_mode(self.OperationMode.TuneMode)
            return True
        elif int_status & 0x01:  # INT_CRCERROR
            self.set_operation_mode(self.OperationMode.Ready)
            self.clear_rx_fifo()
            self.set_operation_mode(self.idle_mode | self.OperationMode.RXMode)
        return False

    def retrieve_received_packet(self):
        length = self.read_register_value(self.REG_RECEIVED_LENGTH)
        data = self.burst_read(self.REG_FIFO, length)
        self.clear_rx_fifo()
        return data

    def clear_tx_fifo(self):
        self.write_register(self.REG_OPERATION_CONTROL, 0x01)
        self.write_register(self.REG_OPERATION_CONTROL, 0x00)

    def clear_rx_fifo(self):
        self.write_register(self.REG_OPERATION_CONTROL, 0x02)
        self.write_register(self.REG_OPERATION_CONTROL, 0x00)

    def get_int_status(self):
        return int.from_bytes(self.burst_read(self.REG_INT_STATUS1, 2), 'big')

    def enable_interrupt(self, flags):
        self.burst_write(self.REG_INT_ENABLE1, flags.to_bytes(2, 'big'))

    def read_register_value(self, reg):
        return self.burst_read(reg, 1)[0]

    def turn_on(self):
        # Activar el módulo
        if self.sdn:
            self.sdn.value(0)

    def turn_off(self):
        # Desactivar el módulo
        if self.sdn:
            self.sdn.value(1)
        self.cs.value(1)

    def is_clock_ready(self):
        # Verificar si el reloj del módulo está listo
        status = self.read_register_value(self.REG_INT_STATUS2)
        return status != 0xFF and status & 0x02

    def get_device_status(self):
        return self.read_register_value(self.REG_DEV_STATUS)
    
    def set_modulation_type(self, modulation_type):
        self.modulation_type = modulation_type

    def set_packet_handling(self, enabled, lsb_first=False):
        self.packet_handling_enabled = enabled
        self.lsb_first = lsb_first

    def set_config_callback(self, callback):
        self.config_callback = callback

    def set_send_blocking(self, enabled=True):
        self.send_blocking = enabled

    def set_idle_mode(self, mode):
        self.idle_mode = mode

    def read_all(self):
        """Read all registers"""
        return self.burst_read(self.REG_DEV_TYPE, 0x7F)

    def clear_fifo(self):
        self.write_register(self.REG_OPERATION_CONTROL, 0x03)
        self.write_register(self.REG_OPERATION_CONTROL, 0x00)

