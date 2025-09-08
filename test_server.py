import pytest
import json
import os

from message_types import RequestMessage
from server import SputnikLogSystem


@pytest.fixture(scope="function")
def sputnik_system(mocker):
    log_filename = "test_server.log"
    file = open(log_filename, "w")
    file.close()

    mocker.patch("socket.socket.bind", lambda x, y: None)

    yield SputnikLogSystem(
        "127.0.0.1", 5001, "127.0.0.1", 5002, log_filename=log_filename
    )

    os.remove(log_filename)


def test_gen_log(sputnik_system):
    log = sputnik_system.generate_log_message()
    assert bool(log) == True
    assert len(log.split(" ")) == 6


def test_send_msg(sputnik_system, mocker):
    online = sputnik_system.generate_online_message()
    sputnik_system._fifo_queue.append(online)

    assert online.get("recv_time") is not None
    assert online.get("message") is not None

    mocker.patch("socket.socket.sendto")
    sputnik_system._send_msg()


@pytest.mark.parametrize(
    "command_json",
    [
        {"command": "getlog", "interval": "10", "device": "3", "sensor": "temperature"},
    ],
)
def test_receive_command(sputnik_system, mocker, command_json):
    mocker.patch(
        "socket.socket.recv",
        lambda x, y: json.dumps(command_json).encode(),
    )
    msg = sputnik_system._receive_command()
    assert isinstance(msg, RequestMessage) == True

    with open(sputnik_system.log_filename, "a") as file:
        file.write(sputnik_system.generate_log_message() + "\n")

    sputnik_system._handle_command(msg)
