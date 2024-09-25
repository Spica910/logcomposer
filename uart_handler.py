import serial
import serial.tools.list_ports
from collections import deque

class UARTHandler:
    def __init__(self):
        self.serial = None
        self.read_buffer = bytearray()
        self.write_buffer = deque()
        self.max_write_buffer = 1000  # 최대 쓰기 버퍼 크기

    def get_ports(self):
        try:
            return [port.device for port in serial.tools.list_ports.comports()]
        except:
            return []

    def connect(self, port, baud):
        try:
            self.serial = serial.Serial(port, baud, timeout=1)
            return True, "연결 성공"
        except serial.SerialException as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
            except:
                pass
        self.serial = None

    def is_connected(self):
        return self.serial and self.serial.is_open

    def read_data(self):
        if self.is_connected():
            try:
                data = self.serial.read(self.serial.in_waiting or 1)
                if data:
                    self.read_buffer += data
                    if b'\n' in self.read_buffer:
                        lines = self.read_buffer.split(b'\n')
                        self.read_buffer = lines[-1]
                        return b'\n'.join(lines[:-1]).decode('utf-8', errors='replace').strip()
            except (serial.SerialException, OSError) as e:
                self.disconnect()
                return "COM_PORT_DISCONNECTED"
        return None

    def write_data(self, data):
        if self.is_connected():
            try:
                encoded_data = data.encode('utf-8', errors='replace') + b'\n'
                self.write_buffer.append(encoded_data)
                if len(self.write_buffer) > self.max_write_buffer:
                    self.write_buffer.popleft()
                self.flush_write_buffer()
                return True, "데이터 전송 성공"
            except (serial.SerialException, OSError) as e:
                self.disconnect()
                return False, "COM_PORT_DISCONNECTED"
        return False, "연결되지 않음"

    def flush_write_buffer(self):
        while self.write_buffer:
            try:
                self.serial.write(self.write_buffer.popleft())
            except (serial.SerialException, OSError):
                self.disconnect()
                break
