import os
import threading
import time
import math
from PyQt5.QtWidgets import QMainWindow, QComboBox, QPushButton, QLineEdit, QLCDNumber, QLabel, QStatusBar, QTextEdit
from PyQt5.QtCore import QTimer
from PyQt5 import uic
from serial_controller import SerialController
from data_processor import DataProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_controller = SerialController(self)
        # UI 파일 경로 설정
        ui_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        uic.loadUi(ui_path, self)

        # UI 요소에 접근
        self.port_combo = self.findChild(QComboBox, 'comboBox')
        self.baudrate_combo = self.findChild(QComboBox, 'comboBox_2')
        self.connect_button = self.findChild(QPushButton, 'pushButton')
        self.log_output = self.findChild(QTextEdit, 'textEdit')  # QTextEdit 객체에 접근
        self.command_input = self.findChild(QLineEdit, 'lineEdit_2')
        self.lcd_pressure = self.findChild(QLCDNumber, 'lcdNumber')
        self.lcd_temperature = self.findChild(QLCDNumber, 'lcdNumber_2')
        self.lcd_QNH = self.findChild(QLCDNumber, 'lcdNumber_3')
        self.lcd_QFE = self.findChild(QLCDNumber, 'lcdNumber_4')
        self.lcd_QFF = self.findChild(QLCDNumber, 'lcdNumber_5')

        # 소수점 자릿수 설정
        self.lcd_pressure.setDigitCount(7)
        self.lcd_temperature.setDigitCount(7)
        self.lcd_QNH.setDigitCount(7)
        self.lcd_QFE.setDigitCount(7)
        self.lcd_QFF.setDigitCount(7)

        # QLCDNumber 스타일 및 크기 설정
        lcd_style = "QLCDNumber { font-weight: bold; color: black; font-size: 24px; }"

        # 각 QLCDNumber에 스타일과 크기 적용
        self.lcd_pressure.setStyleSheet(lcd_style)
        self.lcd_pressure.setFixedSize(150, 100)

        self.lcd_temperature.setStyleSheet(lcd_style)
        self.lcd_temperature.setFixedSize(150, 100)

        self.lcd_QNH.setStyleSheet(lcd_style)
        self.lcd_QNH.setFixedSize(150, 100)

        self.lcd_QFE.setStyleSheet(lcd_style)
        self.lcd_QFE.setFixedSize(150, 100)

        self.lcd_QFF.setStyleSheet(lcd_style)
        self.lcd_QFF.setFixedSize(150, 100)

        # 상태바 설정
        self.status_bar = self.statusBar()
        self.status_label = QLabel("")
        self.status_bar.setStyleSheet("QStatusBar::item {border: none;}")  # 경계선 제거
        self.status_bar.addPermanentWidget(self.status_label, 1)  # 1로 설정하여 왼쪽 정렬

        # 클래스 인스턴스 생성
        # self.serial_controller = SerialController()
        self.data_processor = DataProcessor()

        # 추가적인 초기화 작업
        self.connect_button.clicked.connect(self.toggle_connection)
        self.command_input.returnPressed.connect(self.send_command)

        # 상태바 업데이트 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status_bar)
        self.timer.start(1000)  # 1초마다 상태바 업데이트

    def toggle_connection(self):
        if self.serial_controller.serial_connection and self.serial_controller.serial_connection.is_open:
            self.serial_controller.disconnect()
            self.connect_button.setText("Connect")
            self.append_log("Disconnected")
            self.update_status_bar()  # 상태바 즉시 업데이트
        else:
            port = self.port_combo.currentText()
            baudrate = int(self.baudrate_combo.currentText())
            success, message = self.serial_controller.connect(port, baudrate)
            self.append_log(message)
            if success:
                self.connect_button.setText("Disconnect")
                self.update_status_bar()  # 상태바 즉시 업데이트
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
            self.serial_controller.send_command(command + '\r')
            self.append_log(f"Sent command: {command}")
            self.command_input.clear()

    def update_lcd_displays(self, pressure, temperature):
        self.lcd_pressure.display(pressure)
        self.lcd_temperature.display(temperature)

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

        self.append_log(f"Received: Pressure={pressure}, Temperature={temperature}, QFE={QFE:.2f}, QNH={QNH:.2f}, QFF={QFF:.2f}")

    def update_status_bar(self):
        # 현재 시간 가져오기
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # 접속 상태 및 환경 가져오기
        if self.serial_controller.serial_connection and self.serial_controller.serial_connection.is_open:
            connection_status = "Connected"
            port = self.port_combo.currentText()
            baudrate = self.baudrate_combo.currentText()
            env_info = f"{port} | {baudrate} bps"
        else:
            connection_status = "Disconnected"
            env_info = "Not connected"

        # 상태바 업데이트
        self.status_label.setText(f"{connection_status} | {env_info} | Time: {current_time}")

    def append_log(self, message):
        """QTextEdit에 로그 메시지를 추가하고 자동으로 스크롤."""
        self.log_output.append(message)
        # self.log_output.ensureCursorVisible()  # 새로운 로그가 추가될 때 스크롤이 아래로 이동
         # 수직 스크롤바를 최대값으로 설정하여 자동으로 아래로 스크롤
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_button_state(self, connected):
            if connected:
                self.connect_button.setText("Disconnect")
                self.connect_button.setEnabled(True)
            else:
                self.connect_button.setText("Connect")
                self.connect_button.setEnabled(True)