import pytest
import json
import os

from message_types import Message
from client import GroundLogSystem


@pytest.fixture(scope="module")
def ground_system():
    log_filename = "test_client.log"
    file = open(log_filename, "w")
    file.close()

    yield GroundLogSystem(
        "127.0.0.1", 5010, "127.0.0.1", 5020, log_filename=log_filename
    )

    os.remove(log_filename)


@pytest.mark.parametrize(
    "msg, output",
    [
        (
            Message("2025-08-26", "13:28:40", "log", "2", "voltage", "1.656", ""),
            {"device": "2", "sensor": "voltage", "value": "1.656"},
        ),
        (
            Message("2025-08-26", "13:28:40", "log", "2", "voltage", "ERROR", 0),
            {"device": "2", "sensor": "voltage", "failure": "ERROR"},
        ),
        (
            Message("2025-08-26", "13:28:40", "log", "2", "voltage", "WARNING", 0.0),
            {"device": "2", "sensor": "voltage", "failure": "WARNING"},
        ),
        (
            Message("2025-08-26", "13:28:40", "log", "2", "voltage", "warning", {}),
            {"device": "2", "sensor": "voltage", "failure": "warning"},
        ),
    ],
)
def test_handle_chart_recorder(ground_system, msg, output):
    assert ground_system._format_chart_recorder(msg) == output


@pytest.mark.parametrize(
    "msg, output",
    [
        (
            Message("2025-08-26", "13:28:40", "online", "3", "temp", "5", ""),
            {"device": "3", "sensor": "temp", "value": "5"},
        ),
        (
            Message("2025-08-26", "13:28:40", "online", "3", "temp", "10", 0),
            {"device": "3", "sensor": "temp", "value": "10"},
        ),
        (
            Message("2025-08-26", "13:28:40", "online", "3", "temp", "15", 0.0),
            {"device": "3", "sensor": "temp", "value": "15"},
        ),
        (
            Message("2025-08-26", "13:28:40", "online", "3", "temp", "20", {}),
            {"device": "3", "sensor": "temp", "value": "20"},
        ),
    ],
)
def test_handle_online(ground_system, msg, output):
    assert ground_system._format_online(msg) == output


@pytest.mark.parametrize(
    "message_json",
    [
        {
            "recv_time": 1756204412,
            "message": "2025-08-26 13:33:32.321327 online 2 voltage 9.123 2972",
        },
    ],
)
def test_get_msg(ground_system, mocker, message_json):
    mocker.patch(
        "socket.socket.recv",
        lambda x, y: json.dumps(message_json).encode(),
    )
    msg = ground_system._get_msg()
    assert isinstance(msg, Message) == True


@pytest.mark.parametrize(
    "message_json",
    [
        {
            "recv_time": 1756204412,
            "message": "2025-08-26 13:33:32.321327 online 2 voltage 9.123 272",
        },
        {
            "recv_time": 1756204412,
        },
        {},
    ],
)
def test_get_broken_msg(ground_system, mocker, message_json):
    mocker.patch(
        "socket.socket.recv",
        lambda x, y: json.dumps(message_json).encode(),
    )
    msg = ground_system._get_msg()
    assert msg == None


@pytest.mark.parametrize(
    "request_log", ["5 3 temperature", "100 3 temperature", "1 3 temperature"]
)
def test_handle_request_log(ground_system, request_log):
    queue_len_before = len(ground_system._request_queue)
    ground_system._handle_request(request_log.split())
    queue_len_after = len(ground_system._request_queue)
    assert queue_len_before + 1 == queue_len_after


@pytest.mark.parametrize("request_failure_count", ["5", "1", "2"])
def test_handle_request_failure_count(ground_system, request_failure_count):
    ground_system._handle_request(request_failure_count.split())


@pytest.mark.parametrize(
    ["interval", "device", "sensor"], [(5, 3, "temperature"), (1, 3, "temperature")]
)
def test_request_log(ground_system, mocker, interval, device, sensor):
    mocker.patch(
        "socket.socket.sendto",
        lambda x, y, z: None,
    )
    ground_system._send_log_request(interval, device, sensor)


@pytest.mark.parametrize(
    "message",
    [
        Message("2025-08-26", "13:28:40", "online", "3", "temp", "5", ""),
        Message("2025-08-26", "13:28:40", "log", "2", "voltage", "5.555", ""),
    ],
)
def test_handle_message(ground_system, message):
    ground_system._last_request_time -= 5  # для того чтобы проверить отправку запроса
    ground_system._handle_message(message)
