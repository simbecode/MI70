import serial
import threading
import time


class SerialCommunicator:
    def __init__(self, port="COM2", baudrate=4800, parity=serial.PARITY_EVEN,
                 bytesize=serial.SEVENBITS, stopbits=serial.STOPBITS_ONE, timeout=1):
        self.port_settings = {
            "port": port,
            "baudrate": baudrate,
            "parity": parity,
            "bytesize": bytesize,
            "stopbits": stopbits,
            "timeout": timeout,
        }
        self.ser = None
        self.running = True

    def connect(self):
        """시리얼 포트 연결"""
        try:
            self.ser = serial.Serial(**self.port_settings)
            print(f"Connected to {self.port_settings['port']} successfully.")
            # 데이터 읽기를 별도의 스레드로 실행
            threading.Thread(target=self.read_data, daemon=True).start()
        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def send_command(self, command):
        """명령어 전송"""
        if self.ser and self.ser.is_open:
            try:
                full_command = command.strip() + "\r\n"  # 명령어 끝에 \r\n 추가
                self.ser.write(full_command.encode('ascii'))
                print(f"Sent: {command.strip()}")
            except Exception as e:
                print(f"Error while sending command: {e}")
        else:
            print("Serial port not connected.")

    def read_data(self):
        """실시간 데이터 읽기"""
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    print(f"Received: {data.decode('ascii')}")
                time.sleep(0.1)  # 100ms 대기
            except Exception as e:
                print(f"Error while reading data: {e}")
                break

    def disconnect(self):
        """시리얼 포트 닫기"""
        if self.ser and self.ser.is_open:
            self.running = False
            self.ser.close()
            print("Serial port closed.")


def main():
    print("Starting Serial Communicator...")
    communicator = SerialCommunicator()

    # 시리얼 포트 연결
    communicator.connect()

    try:
        while True:
            # 사용자 입력 대기
            command = input("Enter command (or 'exit' to quit): ")
            if command.lower() == "exit":
                break
            communicator.send_command(command)
    except KeyboardInterrupt:
        print("\nExiting program.")
    finally:
        communicator.disconnect()


if __name__ == "__main__":
    main()
