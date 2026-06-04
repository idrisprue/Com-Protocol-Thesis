"""Root-level compatibility copy for Pico sync tools."""


def _validate_uint(value, size_bytes, name):
    if not isinstance(value, int):
        raise TypeError("%s must be an integer" % name)

    max_value = (1 << (size_bytes * 8)) - 1
    if value < 0 or value > max_value:
        raise ValueError("%s must fit in %d bytes" % (name, size_bytes))


def _validate_three_bytes(value, name):
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError("%s must be bytes or bytearray" % name)
    if len(value) != 3:
        raise ValueError("%s must be exactly 3 bytes" % name)


def make_ticket(user, place, sensor_id, data, observations, day, time):
    _validate_uint(user, 2, "user")
    _validate_uint(place, 1, "place")
    _validate_uint(sensor_id, 1, "sensor_id")
    _validate_uint(data, 2, "data")
    _validate_uint(observations, 4, "observations")
    _validate_three_bytes(day, "day")
    _validate_three_bytes(time, "time")

    ticket = bytearray()
    ticket.extend(user.to_bytes(2, "big"))
    ticket.append(place)
    ticket.append(sensor_id)
    ticket.extend(data.to_bytes(2, "big"))
    ticket.extend(observations.to_bytes(4, "big"))
    ticket.extend(day)
    ticket.extend(time)
    return bytes(ticket)
