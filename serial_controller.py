import serial

class SerialController:
    def __init__(self, main_window):
        self.main_window = main_window  
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

    def send_command(self, command):
        if self.serial_connection and self.serial_connection.is_open:
            try:
                command_to_send = command + '\r'
                self.serial_connection.write(command_to_send.encode())
                print(f"Sent: {command.strip()}")
            except serial.SerialException as e:
                print(f"Failed to send command: {e}")
        else:
            print("Serial port is not open. Cannot send command.")

    def receive_data(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                data = self.serial_connection.read_until(b'\n').decode('utf-8').strip()
                if data:
                    print(f"Received data: {data}")
                    return data
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"Error during serial communication: {e}")
            if isinstance(e, serial.SerialException):
                self.disconnect()  # serial.SerialException 발생 시 연결 해제
                self.main_window.update_button_state(False)  # MainWindow에서 버튼 상태를 변경
        except AttributeError as e:
            print(f"AttributeError: {e}. This may occur if the serial connection was closed unexpectedly.")
        return None
    
    def disconnect(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                print("Serial port disconnected.")
                
        except serial.SerialException as e:
            print(f"Failed to close serial port: {e}")
        except Exception as e:
            print(f"Unexpected error during disconnect: {e}")
        finally:
            # receive_thread가 None이 아닌지 확인한 후, is_alive() 호출
            if hasattr(self, 'receive_thread') and self.receive_thread is not None:
                if self.receive_thread.is_alive():
                    self.receive_thread.join()
                    print("Receive thread terminated.")
        # GUI 업데이트는 MainWindow에서 처리하도록 알림
        self.main_window.update_button_state(False)
