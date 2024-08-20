import serial

class SerialController:
    def __init__(self):
        self.serial_connection = None
        self.receive_thread = None  # 초기화
        self.running = False
        self.buffer = ""

    def connect(self, port, baudrate):
        try:
            self.serial_connection = serial.Serial(port, baudrate, timeout=1)
            return True, f"Connected to {port} at {baudrate} baud."
        except serial.SerialException as e:
            return False, f"Failed to connect: {e}"

    def disconnect(self):
        if self.serial_connection and self.serial_connection.is_open:
            try:
                # 스레드 종료 플래그 설정
                self.running = False

                # 스레드가 종료될 때까지 대기
                if self.receive_thread and self.receive_thread.is_alive():
                    self.receive_thread.join()

                # 시리얼 포트를 닫고 리소스를 정리
                self.serial_connection.close()
                self.serial_connection = None
                print("Serial port disconnected and thread stopped.")
            except serial.SerialException as e:
                print(f"Error while disconnecting: {e}")

    def send_command(self, command):
        if self.serial_connection and self.serial_connection.is_open:
            try:
                command_to_send = command + '\r\n'
                self.serial_connection.write(command_to_send.encode())
                print(f"Sent: {command.strip()}")
            except serial.SerialException as e:
                print(f"Failed to send command: {e}")
        else:
            print("Serial port is not open. Cannot send command.")

    def receive_data(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                # 줄바꿈 문자까지 데이터를 읽어들임
                data = self.serial_connection.read_until(b'\n').decode('utf-8').strip()
                if data:
                    print(f"Received data: {data}")
                    return data
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"Error during serial communication: {e}")
        except AttributeError as e:
            print(f"AttributeError: {e}. This may occur if the serial connection was closed unexpectedly.")
        return None

class DataProcessor:
    def process_data(self, data):
        if ',' in data:
            try:
                pressure_str, temperature_str = data.split(',')
                pressure = float(pressure_str.strip())
                temperature = float(temperature_str.strip())
                return pressure, temperature
            except ValueError as e:
                print(f"Failed to parse data: {data}, Error: {e}")
                return None, None
        else:
            print(f"Received command response: {data}")
            return None, None

# MainWindow 및 기타 클래스는 이전과 동일하게 유지
