import socket
import time
import json
import random
import threading as thr

from collections import deque
from datetime import datetime

from message_types import RequestMessage
from tools import calc_checksum


class SputnikLogSystem:
    def __init__(
        self,
        gs_ip,
        gs_port,
        sls_ip,
        sls_port,
        log_filename="server.log",
    ):
        """Класс для отправки логов, принятых от бортовой системы космического аппарата"""

        self.gs_ip = str(gs_ip).strip()
        self.gs_port = int(gs_port)
        self.sls_ip = (sls_ip).strip()
        self.sls_port = int(sls_port)

        self.log_filename = log_filename

        self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_sock.bind((self.sls_ip, self.sls_port))

        # для того чтобы метод recv блокировал максимум на 0.5 сек
        self._udp_sock.settimeout(0.5)

        self._sender_msg_thr = thr.Thread(target=self._sender_msg)

        # поток должен убиться если основной завершен
        self._sender_msg_thr.daemon = True

        # очередь FIFO для отправки сообщений
        # NOTE: желательно добавить синхронизацию, это критическая секция
        self._fifo_queue = deque()
        self._fifo_queue_lock = thr.Lock()

    def _send_msg(self):
        with self._fifo_queue_lock:
            msg_to_send = self._fifo_queue.popleft()

        self._udp_sock.sendto(
            json.dumps(msg_to_send).encode(), (self.gs_ip, self.gs_port)
        )
        print(f'Sent: "{msg_to_send}"')

    def _sender_msg(self):
        while True:
            time.sleep(0.05)
            if not self._fifo_queue:
                continue

            self._send_msg()

    @staticmethod
    def generate_log_message():
        now = datetime.now()
        temperature = random.randint(0, 50)
        failure = ""
        if temperature > 40:
            failure = "ERROR:sensor_fail"
        elif temperature > 20:
            failure = "WARNING:overheat"

        log = f"{now} log 3 temperature {failure if failure else temperature}"

        return log

    @staticmethod
    def generate_online_message() -> dict:
        now = datetime.now()
        voltage = round(random.random() * random.randint(3, 10), 3)
        message = {
            "recv_time": int(now.timestamp()),
            "message": f"{now} online 2 voltage {voltage}",
        }

        checksum = calc_checksum(*message["message"].split())
        message["message"] = message["message"] + f" {checksum}"

        return message

    def _receive_command(self) -> RequestMessage | None:
        try:
            # сообщение весит меньше КиБ
            data = self._udp_sock.recv(1024)
            req_msg = json.loads(data)
        except (json.JSONDecodeError, TimeoutError, ConnectionError) as e:
            if not isinstance(e, TimeoutError):
                print(e)
            return None

        req_msg = RequestMessage(
            req_msg["command"],
            req_msg["interval"],
            req_msg["device"],
            req_msg["sensor"],
        )

        print(
            f"command: {req_msg.command} | interval: {req_msg.interval} | device: {req_msg.device} | sensor: {req_msg.sensor} | at time: {datetime.now()}"
        )
        return req_msg

    def _handle_command(self, req_msg: RequestMessage):
        now = datetime.now()
        file = open(self.log_filename, "r")

        eof = False
        msgs = []

        while not eof:
            newline = file.readline().strip()

            if not newline:
                eof = True
                break

            dt, tm, src, device, sensor, value = newline.split(" ")
            dtm = datetime.fromisoformat(dt + "T" + tm)

            delta = now - dtm

            if (
                delta.total_seconds() < int(req_msg.interval)
                and sensor == str(req_msg.sensor)
                and device == str(req_msg.device)
            ):
                checksum = calc_checksum(dt, tm, src, device, sensor, value)
                msg = {
                    "recv_time": int(now.timestamp()),
                    "message": newline + f" {checksum}",
                }
                msgs.append(msg)

        if msgs:
            log_start = {
                "recv_time": int(now.timestamp()),
                "message": f"{dt} {tm} {src} {device} system log_start {calc_checksum(dt, tm, src, device, 'system', 'log_start')}",
            }
            log_end = {
                "recv_time": int(now.timestamp()),
                "message": f"{dt} {tm} {src} {device} system log_end {calc_checksum(dt, tm, src, device, 'system', 'log_end')}",
            }
            with self._fifo_queue_lock:
                self._fifo_queue.append(log_start)
                self._fifo_queue.extend(msgs)
                self._fifo_queue.append(log_end)

        file.close()

    def _save_msg(self, msg):
        with open(self.log_filename, "a") as file:
            file.write(msg + "\n")

    def run(self):
        """Основной метод для запуска системы логов космического аппарата. Блокирующий вызов!"""

        self._sender_msg_thr.start()

        while 1:
            message = self.generate_online_message()
            log = self.generate_log_message()

            self._save_msg(log)

            with self._fifo_queue_lock:
                self._fifo_queue.append(message)

            req_msg = self._receive_command()
            if not req_msg:
                continue

            self._handle_command(req_msg)


def main():
    sputnik = SputnikLogSystem("127.0.0.1", 5001, "127.0.0.1", 5002)
    sputnik.run()


if __name__ == "__main__":
    main()
