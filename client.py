import socket
import time
import json
import threading as thr

from collections import deque
from datetime import datetime

from message_types import Message
from tools import calc_checksum


class GroundLogSystem:

    def __init__(
        self,
        gs_ip,
        gs_port,
        sls_ip,
        sls_port,
        log_filename="client.log",
    ):
        """Класс для управления логами космического аппарата с наземной станции"""

        self.sls_ip = str(sls_ip).strip()
        self.sls_port = int(sls_port)

        self.gs_ip = str(gs_ip).strip()
        self.gs_port = int(gs_port)

        self.log_filename = log_filename

        self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_sock.bind((self.gs_ip, self.gs_port))

        self._handle_telemetry_thr = thr.Thread(target=self._message_handler)
        self._handle_telemetry_thr.daemon = True

        self._request_queue = deque()
        self._request_queue_lock = thr.Lock()

        self._last_request_time = time.time()
        self._start_datetime = datetime.now()

    def _get_msg(self):
        """Получение сообщения через UDP и его десериализация в Message"""

        try:
            data = self._udp_sock.recv(1024)
            msg = json.loads(data)
        except (json.JSONDecodeError, TimeoutError, ConnectionError) as e:
            print(e)
            return None

        if not msg.get("message"):
            return None

        message = Message(*msg["message"].split(" "))
        if int(message.checksum) != calc_checksum(
            message.date,
            message.time,
            message.source,
            message.device,
            message.sensor,
            message.value,
        ):
            print(f"Packet at { message.date} {message.time} is broken")
            return None

        return message

    @staticmethod
    def _format_online(self, message: Message) -> dict:
        """Форматирует сообщение для вывода в стандартный поток / файл"""

        online = {
            "device": message.device,
            "sensor": message.sensor,
            "value": message.value,
        }
        return online

    def _handle_message(self, message: Message):
        """Обработка принятого сообщения"""

        output = None
        if message.source == "online":
            output = self._format_online(message)
        elif message.source == "log":
            output = self._format_chart_recorder(message)

        if output:
            print(output)
            self._save_log(
                dt=message.date,
                tm=message.time,
                src=message.source,
                device=message.device,
                sensor=message.sensor,
                val=message.value,
            )

    def _message_handler(self):
        """Обработчик сообщений. Необходимо запускать в отдельном потоке."""
        while 1:
            msg = self._get_msg()
            if msg:
                self._handle_message(msg)

            if time.time() - self._last_request_time > 3.0:

                with self._request_queue_lock:
                    req_msg = (
                        self._request_queue.popleft() if self._request_queue else None
                    )
                if req_msg:
                    self._send_log_request(*req_msg)
                    self._last_request_time = time.time()

            time.sleep(0.05)

    def _format_chart_recorder(self, message: Message) -> dict:
        """Форматирует сообщение для вывода в стандартный поток / файл"""
        log = {
            "device": message.device,
            "sensor": message.sensor,
        }
        if any(level in message.value.lower() for level in ("warning", "error")):
            log["failure"] = message.value
        else:
            log["value"] = message.value
        return log

    def _save_log(self, **kwargs):
        with open(self.log_filename, "a") as file:
            file.write(
                " ".join((f"{key}={value}" for key, value in kwargs.items())) + "\n"
            )

    def _handle_request(self, request_log):
        len_req_log = len(request_log)

        if len_req_log == 3:
            interval, device, sensor = request_log
            if interval.isnumeric() and device.isnumeric() and not sensor.isspace():
                self._request_queue.append((int(interval), int(device), sensor))

        elif len_req_log == 1:
            (device,) = request_log
            errors, warnings = self._get_failure_count(device)
            print(f"Session errors: {errors} || Session warnings: {warnings}")

    def run(self):
        print(
            f"""
Сокет наземной станции: {self.gs_ip}:{self.gs_port}
Сокет космического аппарата: {self.sls_ip}:{self.sls_port}
\nДоступные команды (для отправки команд отправьте в стандартный поток ввода строку в заданном формате):
\n[getlog] <interval> <device> <sensor> (Получить логи с самописца)
Пример: 5 3 temperature
\n[printfails] <device> (Подсчитать количество ошибок и предупреждений)
Пример: 3
"""
        )

        self._last_request_time = time.time()
        self._start_datetime = datetime.now()
        self._handle_telemetry_thr.start()

        while 1:
            request_log = input().split(" ")
            self._handle_request(request_log)

    def _send_log_request(self, interval: int, device: int, sensor: str):
        """Отправка запроса логов с параметрами через UDP"""

        message = {
            "command": "getlog",
            "interval": interval,
            "device": device,
            "sensor": sensor,
        }
        self._udp_sock.sendto(
            json.dumps(message).encode(), (self.sls_ip, self.sls_port)
        )

        self._save_log(
            datetime=datetime.now().isoformat(),
            command=message["command"],
            interval=message["interval"],
            device=message["device"],
            sensor=message["sensor"],
        )

    def _get_failure_count(self, device):
        errors = 0
        warnings = 0

        with open(self.log_filename, "r") as file:
            eof = False

            while not eof:
                newline = file.readline().strip()

                if not newline:
                    eof = True
                    break

                log = {
                    line.split("=")[0]: line.split("=")[1]
                    for line in newline.split(" ")
                }
                if (
                    log.get("device") is not None
                    and log.get("device") == device
                    and log.get("val") is not None
                    and log.get("dt") is not None
                    and log.get("tm") is not None
                    and datetime.fromisoformat(log.get("dt") + "T" + log.get("tm"))
                    > self._start_datetime
                ):
                    if "error" in log.get("val").lower():
                        errors += 1
                    elif "warning" in log.get("val").lower():
                        warnings += 1

        return errors, warnings


def main():
    ground = GroundLogSystem("127.0.0.1", 5001, "127.0.0.1", 5002)
    ground.run()


if __name__ == "__main__":
    main()
