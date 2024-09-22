from ax25 import AX25

# Usage example:
if __name__ == "__main__":
    ax25 = AX25()

    # Create an AX25Struct
    ax25_struct = ax25.AX25Struct("SOURCE", 0, "DEST  ", 0, 0x03, 0xF0, "Pehuensat III", True)

    # Encode AX25 frame
    ax25_frame = ax25_struct.encode()
    print("AX25 Frame:", [ax25.to_hex(b) for b in ax25_frame])

    # Encode HDLC frame
    hdlc_frame = ax25.hdlc_encode(ax25_frame)
    print("HDLC Frame:", [ax25.to_hex(b) for b in hdlc_frame])

    # Decode HDLC frame
    decoded_ax25_frame = ax25.hdlc_decode(hdlc_frame)
    if decoded_ax25_frame is not None:
        print("Decoded AX25 Frame:", [ax25.to_hex(b) for b in decoded_ax25_frame])

        # Decode AX25 frame
        decoded_ax25_struct = ax25.AX25Struct(None, None, None, None, None, None, None, None)
        decoded_ax25_struct.decode(decoded_ax25_frame)

        print("Decoded Source:", decoded_ax25_struct.src)
        print("Decoded Destination:", decoded_ax25_struct.dst)
        print("Decoded Payload:", decoded_ax25_struct.payload)
    else:
        print("Error: HDLC decoding failed")