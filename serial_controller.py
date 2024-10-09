import serial
import logging

class SerialController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.serial_connection1 = None  # 첫 번째 포트
        self.serial_connection2 = None  # 두 번째 포트

    def connect(self, port, baudrate, port_number=1):
        try:
            if port_number == 1:
                self.serial_connection1 = serial.Serial(port, baudrate, timeout=1)
                self.logger.info(f"Connected to {port} at {baudrate} baud (Port 1).")
                return True, f"Connected to {port} at {baudrate} baud (Port 1)."
            else:
                self.serial_connection2 = serial.Serial(port, baudrate, timeout=1)
                self.logger.info(f"Connected to {port} at {baudrate} baud (Port 2).")
                return True, f"Connected to {port} at {baudrate} baud (Port 2)."
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to {port} at {baudrate} baud: {e}")
            return False, f"Failed to connect: {e}"

    def disconnect(self, port_number=1):
        try:
            if port_number == 1 and self.serial_connection1 and self.serial_connection1.is_open:
                self.serial_connection1.close()
                self.logger.info("Serial port 1 disconnected.")
            elif port_number == 2 and self.serial_connection2 and self.serial_connection2.is_open:
                self.serial_connection2.close()
                self.logger.info("Serial port 2 disconnected.")
        except serial.SerialException as e:
            self.logger.error(f"Failed to close serial port: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during disconnect: {e}")

    def send_command(self, command, port_number=1):
        serial_connection = self.serial_connection1 if port_number == 1 else self.serial_connection2
        if serial_connection and serial_connection.is_open:
            try:
                serial_connection.write((command + '\r').encode())
                self.logger.info(f"Sent: {command.strip()} (Port {port_number})")
            except serial.SerialException as e:
                self.logger.error(f"Failed to send command: {e}")
        else:
            self.logger.warning(f"Serial port {port_number} is not open. Cannot send command.")

    def receive_data(self, port_number=1):
        serial_connection = self.serial_connection1 if port_number == 1 else self.serial_connection2
        buffer = ""
        try:
            if serial_connection and serial_connection.is_open:
                data = serial_connection.read_until(b'\n').decode('utf-8').strip()
                if data:
                    self.logger.info(f"Received data from Port {port_number}: {data}")
                    return data
            else:
                self.logger.warning(f"Serial port {port_number} is not open.")
        except (serial.SerialException, UnicodeDecodeError) as e:
            self.logger.error(f"Error during serial communication: {e}")
            self.disconnect(port_number)
        return None