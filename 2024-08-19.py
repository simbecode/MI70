import sys
import serial
import threading
import time
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel,
    QComboBox, QTextEdit, QLineEdit, QHBoxLayout
)
from PyQt5.QtCore import pyqtSlot, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class RS232Controller:
    def __init__(self):
        self.serial_connection = None

    def connect(self, port, baudrate):
        try:
            self.serial_connection = serial.Serial(port, baudrate, timeout=1)
            return True
        except serial.SerialException:
            return False

    def disconnect(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

    def send_command(self, command):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(command.encode())

    def receive_data(self):
        if self.serial_connection and self.serial_connection.is_open:
            try:
                data = self.serial_connection.read(1024)
                if data:
                    return data.decode(errors='ignore')
            except serial.SerialTimeoutException:
                return None
        return None


class Logger:
    def __init__(self):
        self.logs = []

    def add_log(self, message):
        self.logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

    def get_logs(self):
        return "\n".join(self.logs)


class GraphPlotter(QWidget):
    def __init__(self, parent=None):
        super(GraphPlotter, self).__init__(parent)
        self.figure, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 5))
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.pressure_data = []
        self.temperature_data = []

    def update_pressure_plot(self, pressure):
        self.pressure_data.append(pressure)
        self.ax1.clear()
        self.ax1.plot(self.pressure_data, marker='o')
        self.ax1.set_title('Pressure (hPa)')
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('Pressure')
        self.canvas.draw()

    def update_temperature_plot(self, temperature):
        self.temperature_data.append(temperature)
        self.ax2.clear()
        self.ax2.plot(self.temperature_data, marker='o')
        self.ax2.set_title('Temperature (°C)')
        self.ax2.set_xlabel('Time')
        self.ax2.set_ylabel('Temperature')
        self.canvas.draw()


class DataReceiverThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, rs232_controller, parent=None):
        super().__init__(parent)
        self.rs232_controller = rs232_controller
        self.running = True

    def run(self):
        while self.running:
            data = self.rs232_controller.receive_data()
            if data:
                self.data_received.emit(data.strip())
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RS-232 Communication GUI")

        self.rs232 = RS232Controller()
        self.logger = Logger()

        self.init_ui()
        self.is_connected = False
        self.data_receiver_thread = None

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Connection Section
        conn_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM7", "COM2", "COM3", "COM4"])  # Example ports
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        # Connection Status LED
        self.connection_status_label = QLabel()
        self.update_connection_status_led(False)  # Initially disconnected

        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(QLabel("Baudrate:"))
        conn_layout.addWidget(self.baudrate_combo)
        conn_layout.addWidget(self.connect_button)
        conn_layout.addWidget(QLabel("Status:"))
        conn_layout.addWidget(self.connection_status_label)  # LED
        main_layout.addLayout(conn_layout)

        # Command Section
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.send_button = QPushButton("Send Command")
        self.send_button.clicked.connect(self.send_command)
        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.send_button)
        main_layout.addLayout(command_layout)

        # Log and Data Display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        main_layout.addWidget(QLabel("Logs:"))
        main_layout.addWidget(self.log_display)

        # Additional Output Line
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        main_layout.addWidget(QLabel("Output:"))
        main_layout.addWidget(self.output_display)

        # Graph Plotter
        self.graph_plotter = GraphPlotter(self)
        main_layout.addWidget(self.graph_plotter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_connection_status_led(self, is_connected):
        palette = QPalette()
        if is_connected:
            palette.setColor(QPalette.Window, QColor("green"))
        else:
            palette.setColor(QPalette.Window, QColor("red"))
        self.connection_status_label.setAutoFillBackground(True)
        self.connection_status_label.setPalette(palette)
        self.connection_status_label.setFixedWidth(20)
        self.connection_status_label.setFixedHeight(20)

    def toggle_connection(self):
        if self.is_connected:
            self.rs232.disconnect()
            self.connect_button.setText("Connect")
            self.is_connected = False
            self.update_connection_status_led(False)
            if self.data_receiver_thread:
                self.data_receiver_thread.stop()
        else:
            port = self.port_combo.currentText()
            baudrate = int(self.baudrate_combo.currentText())
            if self.rs232.connect(port, baudrate):
                self.connect_button.setText("Disconnect")
                self.is_connected = True
                self.update_connection_status_led(True)
                self.start_receiving_thread()
                self.execute_initial_commands()  # Execute initial commands after connection
            else:
                self.logger.add_log("Failed to connect.")
                self.update_log_display()

    def execute_initial_commands(self):
        self.rs232.send_command('VERS\r\n')
        self.logger.add_log("Sent: VERS")
        self.update_log_display()
        time.sleep(1)  # Wait for 1 second

        self.rs232.send_command('R\r\n')
        self.logger.add_log("Sent: R")
        self.update_log_display()
        time.sleep(1)  # Wait for 1 second

    def send_command(self):
        command = self.command_input.text()
        self.rs232.send_command(command)
        self.logger.add_log(f"Sent: {command}")
        self.update_log_display()

    def start_receiving_thread(self):
        self.data_receiver_thread = DataReceiverThread(self.rs232)
        self.data_receiver_thread.data_received.connect(self.process_received_data)
        self.data_receiver_thread.start()

    @pyqtSlot(str)
    def process_received_data(self, data):
        self.logger.add_log(f"Received: {data}")
        self.update_log_display()
        
        try:
            # 데이터가 "1003.38, 26.77" 형식으로 들어올 것을 가정합니다.
            pressure_str, temperature_str = data.split(',')
            pressure = float(pressure_str.strip())
            temperature = float(temperature_str.strip())
            
            # 각각의 차트에 데이터 업데이트
            self.graph_plotter.update_pressure_plot(pressure)
            self.graph_plotter.update_temperature_plot(temperature)
        except ValueError:
            self.logger.add_log(f"Failed to parse data: {data}")
        
        self.update_output_display(data)

    def update_output_display(self, data):
        self.output_display.append(data)

    @pyqtSlot()
    def update_log_display(self):
        self.log_display.setText(self.logger.get_logs())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
