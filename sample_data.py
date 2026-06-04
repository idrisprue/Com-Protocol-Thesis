"""Root-level compatibility copy for Pico sync tools."""


SAMPLE_RECORDS = [
    {"name": "payload_nominal_1", "user": 25, "place": 1, "sensor_id": 3, "data": 1024, "observations": 0, "day": b"\x03\x06\x26", "time": b"\x15\x45\x00"},
    {"name": "payload_nominal_2", "user": 42, "place": 1, "sensor_id": 5, "data": 980, "observations": 1, "day": b"\x03\x06\x26", "time": b"\x15\x46\x15"},
    {"name": "payload_nominal_3", "user": 77, "place": 2, "sensor_id": 4, "data": 875, "observations": 2, "day": b"\x03\x06\x26", "time": b"\x15\x47\x30"},
    {"name": "temperature_high", "user": 101, "place": 2, "sensor_id": 1, "data": 3140, "observations": 10, "day": b"\x04\x06\x26", "time": b"\x09\x10\x05"},
    {"name": "temperature_low", "user": 102, "place": 2, "sensor_id": 1, "data": 2150, "observations": 11, "day": b"\x04\x06\x26", "time": b"\x09\x15\x10"},
    {"name": "humidity_nominal", "user": 120, "place": 3, "sensor_id": 2, "data": 563, "observations": 20, "day": b"\x04\x06\x26", "time": b"\x10\x05\x00"},
    {"name": "humidity_peak", "user": 121, "place": 3, "sensor_id": 2, "data": 899, "observations": 21, "day": b"\x04\x06\x26", "time": b"\x10\x20\x30"},
    {"name": "pressure_nominal", "user": 200, "place": 4, "sensor_id": 6, "data": 4096, "observations": 30, "day": b"\x05\x06\x26", "time": b"\x11\x00\x45"},
    {"name": "pressure_drop", "user": 201, "place": 4, "sensor_id": 6, "data": 3980, "observations": 31, "day": b"\x05\x06\x26", "time": b"\x11\x02\x10"},
    {"name": "battery_safe", "user": 300, "place": 5, "sensor_id": 7, "data": 3720, "observations": 40, "day": b"\x05\x06\x26", "time": b"\x18\x15\x20"},
    {"name": "battery_warning", "user": 301, "place": 5, "sensor_id": 7, "data": 3320, "observations": 41, "day": b"\x05\x06\x26", "time": b"\x18\x20\x25"},
    {"name": "counter_edge", "user": 65535, "place": 255, "sensor_id": 255, "data": 65535, "observations": 4294967295, "day": b"\x31\x12\x26", "time": b"\x23\x59\x59"},
]


def get_sample_record(name):
    for record in SAMPLE_RECORDS:
        if record["name"] == name:
            return dict(record)
    raise KeyError("unknown sample record: %s" % name)
