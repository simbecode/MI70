import os
import threading
import time
from PyQt5.QtWidgets import QMainWindow, QComboBox, QPushButton, QLineEdit, QLCDNumber
from PyQt5 import uic
from serial_controller import SerialController
from data_processor import DataProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # UI 파일 경로 설정
        ui_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        uic.loadUi(ui_path, self)

        # UI 요소에 접근
        self.port_combo = self.findChild(QComboBox, 'comboBox')
        self.baudrate_combo = self.findChild(QComboBox, 'comboBox_2')
        self.connect_button = self.findChild(QPushButton, 'pushButton')
        self.log_input = self.findChild(QLineEdit, 'lineEdit')
        self.command_input = self.findChild(QLineEdit, 'lineEdit_2')  # 명령어 입력을 위한 QLineEdit
        self.lcd_pressure = self.findChild(QLCDNumber, 'lcdNumber')
        self.lcd_temperature = self.findChild(QLCDNumber, 'lcdNumber_2')

        # 소수점 자릿수 설정
        self.lcd_pressure.setDigitCount(7)
        self.lcd_temperature.setDigitCount(7)

        # 콤보박스에 항목 추가
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8"])
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])

        # 클래스 인스턴스 생성
        self.serial_controller = SerialController()
        self.data_processor = DataProcessor()

        # 추가적인 초기화 작업
        self.connect_button.clicked.connect(self.toggle_connection)
        self.command_input.returnPressed.connect(self.send_command)  # 엔터 키를 눌렀을 때 명령어 전송

    def toggle_connection(self):
        if self.serial_controller.serial_connection and self.serial_controller.serial_connection.is_open:
            self.serial_controller.disconnect()
            self.connect_button.setText("Connect")
            self.log_input.setText("Disconnected")
        else:
            port = self.port_combo.currentText()
            baudrate = int(self.baudrate_combo.currentText())
            success, message = self.serial_controller.connect(port, baudrate)
            self.log_input.setText(message)
            if success:
                self.connect_button.setText("Disconnect")
                self.start_receiving_thread()
                self.execute_initial_commands()

    def start_receiving_thread(self):
        self.receiving_thread = threading.Thread(target=self.receive_data_loop, daemon=True)
        self.receiving_thread.start()

    def receive_data_loop(self):
        while self.serial_controller.serial_connection and self.serial_controller.serial_connection.is_open:
            data = self.serial_controller.receive_data()
            if data:
                pressure, temperature = self.data_processor.process_data(data)
                if pressure is not None and temperature is not None:
                    self.update_lcd_displays(pressure, temperature)
            time.sleep(0.1)

    def execute_initial_commands(self):
        self.serial_controller.send_command('VERS\r\n')
        time.sleep(1)  # 1초 대기
        self.serial_controller.send_command('R\r\n')
        time.sleep(1)  # 1초 대기

    def send_command(self):
        command = self.command_input.text().strip()
        if command:
            self.serial_controller.send_command(command + '\r\n')
            self.log_input.setText(f"Sent command: {command}")
            self.command_input.clear()

    def update_lcd_displays(self, pressure, temperature):
        self.lcd_pressure.display(pressure)
        self.lcd_temperature.display(temperature)
        self.log_input.setText(f"Received: Pressure={pressure}, Temperature={temperature}")
