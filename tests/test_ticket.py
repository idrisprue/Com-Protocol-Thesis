from ticket import Ticket

ticket = Ticket(
    user=12345,
    place=1,
    sensor_id=2,
    data=56789,
    observations="Pehuensat III",
    day="220924",  # DDMMYY
    hour="200900"  # HHMMSS
)

ticket_data = ticket.to_bytes()
print("User:", ticket.user)
print("Place:", ticket.place)
print("Sensor ID:", ticket.sensor_id)
print("Data:", ticket.data)
print("Obs:", ticket.observations)
print("Day:", ticket.day)
print("Hour:", ticket.hour)