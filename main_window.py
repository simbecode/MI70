import os
import threading
import time
import math
from PyQt5.QtWidgets import QMainWindow, QComboBox, QPushButton, QLineEdit, QLCDNumber, QLabel, QStatusBar, QTextEdit
from PyQt5.QtCore import QTimer
from PyQt5 import uic
from serial_controller import SerialController
from data_processor import DataProcessor
import re  # 추가된 부분: 정규 표현식을 사용하기 위해 import

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_controller = SerialController()
        ui_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        uic.loadUi(ui_path, self)

        # UI 요소에 접근
        self.port_combo1 = self.findChild(QComboBox, 'comboBox')  # 포트1
        self.baudrate_combo1 = self.findChild(QComboBox, 'comboBox_2')
        self.connect_button1 = self.findChild(QPushButton, 'pushButton')

        self.port_combo2 = self.findChild(QComboBox, 'comboBox_3')  # 포트2
        self.baudrate_combo2 = self.findChild(QComboBox, 'comboBox_4')
        self.connect_button2 = self.findChild(QPushButton, 'pushButton_2')

        self.log_output = self.findChild(QTextEdit, 'textEdit')
        self.command_input = self.findChild(QLineEdit, 'lineEdit_2')

        # QLCDNumber 요소를 GUI에서 불러오기
        self.lcd_pressure = self.findChild(QLCDNumber, 'lcdNumber')
        self.lcd_temperature = self.findChild(QLCDNumber, 'lcdNumber_2')
        self.lcd_QNH = self.findChild(QLCDNumber, 'lcdNumber_3')
        self.lcd_QFE = self.findChild(QLCDNumber, 'lcdNumber_4')
        self.lcd_QFF = self.findChild(QLCDNumber, 'lcdNumber_5')
        self.lcd_port2_first = self.findChild(QLCDNumber, 'lcdNumber_6')  # 포트 2의 첫 번째 값
        self.lcd_port2_rest = self.findChild(QLCDNumber, 'lcdNumber_7')   # 포트 2의 나머지 값

        self.data_processor = DataProcessor()

        # 각 연결 버튼에 대해 클릭 이벤트 설정
        self.connect_button1.clicked.connect(lambda: self.toggle_connection(1))
        self.connect_button2.clicked.connect(lambda: self.toggle_connection(2))
        self.command_input.returnPressed.connect(self.send_command)

    def toggle_connection(self, port_number):
        if port_number == 1:
            port = self.port_combo1.currentText()
            baudrate = int(self.baudrate_combo1.currentText())
            button = self.connect_button1
        else:
            port = self.port_combo2.currentText()
            baudrate = int(self.baudrate_combo2.currentText())
            button = self.connect_button2

        if (port_number == 1 and self.serial_controller.serial_connection1 and self.serial_controller.serial_connection1.is_open) or \
           (port_number == 2 and self.serial_controller.serial_connection2 and self.serial_controller.serial_connection2.is_open):
            self.serial_controller.disconnect(port_number)
            button.setText("Connect")
            self.append_log(f"Disconnected from Port {port_number}")
        else:
            success, message = self.serial_controller.connect(port, baudrate, port_number)
            self.append_log(message)
            if success:
                button.setText("Disconnect")
                self.start_receiving_thread(port_number)

    def start_receiving_thread(self, port_number):
        thread = threading.Thread(target=self.receive_data_loop, args=(port_number,), daemon=True)
        thread.start()

    def receive_data_loop(self, port_number):
        while True:
            data = self.serial_controller.receive_data(port_number)
            if data:
                if port_number == 1:
                    pressure, temperature = self.data_processor.process_data(data)
                    if pressure is not None and temperature is not None:
                        self.update_lcd_displays(pressure, temperature)
                        self.calculate_and_display_QNH_QFE_QFF(pressure, temperature)
                else:
                    self.process_port2_data(data)
            time.sleep(0.1)

    def process_port2_data(self, data):
        """포트 2에서 수신한 데이터를 처리하여 lcdNumber_6과 lcdNumber_7에 표시합니다."""
        try:
            # 정규 표현식을 사용하여 문자열에서 숫자만 추출
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", data)
            if len(numbers) >= 2:
                first_value = float(numbers[0])
                second_value = float(numbers[1])
                self.lcd_port2_first.display(first_value)  # 첫 번째 값을 lcdNumber_6에 표시
                self.lcd_port2_rest.display(second_value)  # 두 번째 값을 lcdNumber_7에 표시
                self.append_log(f"Port 2 Data: {first_value}, {second_value}")
            else:
                self.append_log("Port 2 Data Error: Not enough data received.")
        except ValueError as e:
            self.append_log(f"Port 2 Data Parsing Error: {e}")

    def calculate_and_display_QNH_QFE_QFF(self, pressure, temperature):
        # QFE, QNH, QFF 계산
        HS = 200  # 고정된 센서 높이
        HR = 200  # 고정된 기지의 고도
        b = 0.0086  # 상수 b (°C/m)
        c = 0.00325  # 상수 c (°C/m)
        d = 0.19025  # 상수 d

        QFE = pressure * math.exp(HS / (7996 + b * HS + 29.33 * temperature))
        QNH = QFE * math.exp((0.03416 * HR * (1 - d)) / (288.2 + c * HR))
        QFF = QFE * math.exp(HR / (7996 + b * HR + 29.33 * temperature))

        self.lcd_QFE.display(QFE)
        self.lcd_QNH.display(QNH)
        self.lcd_QFF.display(QFF)

        self.append_log(f"Calculated QFE={QFE:.2f}, QNH={QNH:.2f}, QFF={QFF:.2f}")

    def send_command(self):
        command = self.command_input.text().strip()
        if command:
            # 명령을 두 포트에 모두 전송 (필요에 따라 수정 가능)
            self.serial_controller.send_command(command, 1)
            self.serial_controller.send_command(command, 2)
            self.append_log(f"Sent command to both ports: {command}")
            self.command_input.clear()

    def update_lcd_displays(self, pressure, temperature):
        self.lcd_pressure.display(pressure)
        self.lcd_temperature.display(temperature)

    def append_log(self, message):
        self.log_output.append(message)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_button_state(self, connected, port_number):
        if port_number == 1:
            button = self.connect_button1
        else:
            button = self.connect_button2

        if connected:
            button.setText("Disconnect")
        else:
            button.setText("Connect")
