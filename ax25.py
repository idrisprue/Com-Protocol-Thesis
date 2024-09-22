class AX25:
    def __init__(self):
        self.crc_table = self._generate_crc_table()

    def _generate_crc_table(self):
        crc_table = []
        for i in range(256):
            crc = 0
            c = i << 8
            for j in range(8):
                if (crc ^ c) & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                c = c << 1
            crc_table.append(crc & 0xFFFF)
        return crc_table

    def reverse_bits(self, byte):
        byte = ((byte >> 1) & 0x55) | ((byte & 0x55) << 1)
        byte = ((byte >> 2) & 0x33) | ((byte & 0x33) << 2)
        byte = ((byte >> 4) & 0x0F) | ((byte & 0x0F) << 4)
        return byte & 0xFF

    def crc_calculation(self, frame):
        crc = 0xFFFF
        for byte in frame:
            j = (byte ^ (crc >> 8)) & 0xFF
            crc = self.crc_table[j] ^ (crc << 8)
        crc = crc ^ 0xFFFF
        return crc & 0xFFFF

    class AX25Struct:
        def __init__(self, src, src_ssid, dst, dst_ssid, control, pid, payload, cmd_msg):
            self.cmd_msg = cmd_msg
            self.src = src
            self.src_ssid = src_ssid
            self.dst = dst
            self.dst_ssid = dst_ssid
            self.control = control
            self.pid = pid
            self.payload = payload

        def encode(self):
            frame = []

            # Add Destination Address
            for char in self.dst:
                frame.append((ord(char) & 0xFF) << 1)
            # Add Destination SSID
            frame.append(0x60 + ((self.dst_ssid & 0x0F) << 1))

            # Set Command/Response indicator bits
            if self.cmd_msg:
                frame[6] += 0x80

            # Add Source Address
            for char in self.src:
                frame.append((ord(char) & 0xFF) << 1)
            # Add Source SSID
            frame.append(0x60 + ((self.src_ssid & 0x0F) << 1))

            # Set Command or Response Message Type
            if not self.cmd_msg:
                frame[13] += 0x80

            # Set last bit to indicate end of address fields
            frame[13] += 0x01

            # Set Control Field
            frame.append(self.control & 0xFF)

            # Set PID Field
            frame.append(self.pid & 0xFF)

            # Add Payload Field
            for char in self.payload:
                frame.append(ord(char) & 0xFF)

            return frame

        def decode(self, frame):
            frame_index = 0

            # Get Destination Address
            self.dst = ''.join(chr((frame[i] & 0xFF) >> 1) for i in range(6))
            frame_index += 6
            # Get Destination SSID
            self.dst_ssid = (frame[frame_index] & 0x0F) >> 1
            frame_index += 1

            # Get Command or Response Message Type
            self.cmd_msg = (frame[6] >> 7) == 0x01

            # Get Source Address
            self.src = ''.join(chr((frame[i] & 0xFF) >> 1) for i in range(frame_index, frame_index + 6))
            frame_index += 6
            # Get Source SSID
            self.src_ssid = (frame[frame_index] & 0x0F) >> 1
            frame_index += 1

            # Get Control Field
            self.control = frame[frame_index] & 0xFF
            frame_index += 1

            # Get PID Field
            self.pid = frame[frame_index] & 0xFF
            frame_index += 1

            # Get Payload
            self.payload = ''.join(chr(frame[i] & 0xFF) for i in range(frame_index, len(frame)))

    def hdlc_encode(self, frame):
        encoded_frame = []

        # Convert from MSBit to LSBit
        frame = [self.reverse_bits(byte) for byte in frame]

        # Calculate CRC
        crc = self.crc_calculation(frame)

        # Add CRC to frame
        frame.append((crc >> 8) & 0xFF)
        frame.append(crc & 0xFF)

        # Add Start flag
        encoded_frame.append(0x7E)

        # Frame Bit processing aka the bit stuffing
        cnt = 0
        bit_index = 128
        byte = 0
        for frame_byte in frame:
            for mask in [128, 64, 32, 16, 8, 4, 2, 1]:
                if frame_byte & mask:
                    byte += bit_index
                    bit_index >>= 1
                    if bit_index == 0:
                        encoded_frame.append(byte)
                        byte = 0
                        bit_index = 128

                    cnt += 1
                    if cnt == 5:
                        bit_index >>= 1
                        if bit_index == 0:
                            encoded_frame.append(byte)
                            byte = 0
                            bit_index = 128
                        cnt = 0
                else:
                    bit_index >>= 1
                    if bit_index == 0:
                        encoded_frame.append(byte)
                        byte = 0
                        bit_index = 128
                    cnt = 0

        # Add End flag (0x7E)
        bit_index >>= 1
        if bit_index == 0:
            encoded_frame.append(byte)
            byte = 0
            bit_index = 128

        for _ in range(6):
            byte += bit_index
            bit_index >>= 1
            if bit_index == 0:
                encoded_frame.append(byte)
                byte = 0
                bit_index = 128

        bit_index >>= 1
        encoded_frame.append(byte)

        return encoded_frame

    def hdlc_decode(self, frame):
        decoded_frame = []

        start_flag_found = False
        end_flag_found = False
        cnt = 0
        bit_index = 0
        byte = 0
        shift_register = 0

        for frame_byte in frame:
            for k in range(7, -1, -1):
                bit = (frame_byte >> k) & 0x01
                shift_register = ((shift_register << 1) + bit) & 0xFF

                if not start_flag_found and shift_register == 0x7E:
                    cnt = 0
                    bit_index = 0
                    byte = 0
                    start_flag_found = True
                    break

                if start_flag_found:
                    if shift_register == 0x7E:
                        end_flag_found = True
                        break
                    else:
                        if bit == 0x01:
                            cnt += 1
                            if cnt > 6:
                                return None
                            byte = ((byte << 1) + bit) & 0xFF
                            bit_index += 1
                        elif cnt == 5:
                            cnt = 0
                        else:
                            cnt = 0
                            byte = ((byte << 1) + bit) & 0xFF
                            bit_index += 1

                        if bit_index == 8:
                            decoded_frame.append(byte)
                            byte = 0
                            bit_index = 0

            if end_flag_found:
                break

        # Remove CRC from frame
        frame_crc = decoded_frame.pop()
        frame_crc += decoded_frame.pop() << 8

        # Calculate CRC
        crc = self.crc_calculation(decoded_frame)

        # Convert from LSBit to MSBit
        decoded_frame = [self.reverse_bits(byte) for byte in decoded_frame]

        return decoded_frame

    @staticmethod
    def to_hex(d):
        return "0x{:02X}".format(d)

    @staticmethod
    def from_hex(a):
        return int(a, 16)

