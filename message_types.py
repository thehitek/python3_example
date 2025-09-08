from collections import namedtuple

Message = namedtuple(
    "Message", ("date", "time", "source", "device", "sensor", "value", "checksum")
)

RequestMessage = namedtuple(
    "RequestMessage", ("command", "interval", "device", "sensor")
)
