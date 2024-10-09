import os
import threading
import time
import math
import logging
from datetime import datetime
import csv
from PyQt5.QtWidgets import QMainWindow, QComboBox, QPushButton, QLineEdit, QLCDNumber, QTextEdit
from PyQt5 import uic
from serial_controller import SerialController
from data_processor import DataProcessor
import re
from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
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

        # CSV 파일 경로 설정
        self.csv_file_path = self.setup_csv_file()
        
        # 자정에 파일을 업데이트하기 위해 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_midnight)
        self.timer.start(60000)  # 1분마다 타이머 체크

    def setup_csv_file(self):
        """CSV 파일 경로와 파일 설정을 위한 메서드"""
        # 날짜별 데이터 폴더 설정
        data_dir = os.path.join("C:\\", "SItech", "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # 날짜별 파일명 설정
        csv_filename = datetime.now().strftime("%Y%m%d") + ".csv"
        csv_file_path = os.path.join(data_dir, csv_filename)

        # 파일이 존재하지 않으면 헤더 작성
        if not os.path.isfile(csv_file_path):
            with open(csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Pressure", "Temperature", "QNH", "QFE", "QFF", "Port 2 First", "Port 2 Second"])  # CSV 헤더

        return csv_file_path

    def setup_logging(self):
        """로깅 설정을 위한 메서드"""
        log_dir = os.path.join("C:\\", "SItech", "log")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_filename = datetime.now().strftime("%Y%m%d") + ".txt"
        log_file_path = os.path.join(log_dir, log_filename)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path),  # 로그를 날짜별 파일에 저장
                logging.StreamHandler()
            ]
        )

    def check_midnight(self):
        """자정이 지났는지 확인하고 CSV 및 로그 파일을 업데이트"""
        current_date = datetime.now().strftime("%Y%m%d")
        current_csv_filename = os.path.basename(self.csv_file_path).split(".")[0]
        if current_date != current_csv_filename:
            self.csv_file_path = self.setup_csv_file()
            self.setup_logging()
            self.logger.info("새로운 날짜에 맞춰 CSV 및 로그 파일이 생성되었습니다.")

    def write_to_csv(self, data):
        """데이터를 CSV 파일에 기록하는 메서드"""
        try:
            with open(self.csv_file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)
            self.logger.info(f"Data written to CSV: {data}")
        except Exception as e:
            self.logger.error(f"Failed to write data to CSV: {e}")

    def receive_data_loop(self, port_number):
        while True:
            data = self.serial_controller.receive_data(port_number)
            if data:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if port_number == 1:
                    pressure, temperature = self.data_processor.process_data(data)
                    if pressure is not None and temperature is not None:
                        self.update_lcd_displays(pressure, temperature)
                        self.calculate_and_display_QNH_QFE_QFF(pressure, temperature)
                        # 데이터 수신 시점에서 CSV에 기록
                        csv_data = [
                            timestamp,
                            round(self.lcd_pressure.value(), 2),
                            round(self.lcd_temperature.value(), 2),
                            round(self.lcd_QNH.value(), 2),
                            round(self.lcd_QFE.value(), 2),
                            round(self.lcd_QFF.value(), 2),
                            None,
                            None
                        ]
                        self.write_to_csv(csv_data)
                else:
                    port2_first, port2_second = self.process_port2_data(data)
                    if port2_first is not None and port2_second is not None:
                        # 데이터 수신 시점에서 CSV에 기록
                        csv_data = [
                            timestamp,
                            None,
                            None,
                            None,
                            None,
                            None,
                            round(port2_first, 2),
                            round(port2_second, 2)
                        ]
                        self.write_to_csv(csv_data)
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
                self.logger.info(f"Port 2 Data: {first_value}, {second_value}")
                return first_value, second_value
            else:
                self.append_log("Port 2 Data Error: Not enough data received.")
                self.logger.warning("Port 2 Data Error: Not enough data received.")
                return None, None
        except ValueError as e:
            self.append_log(f"Port 2 Data Parsing Error: {e}")
            self.logger.error(f"Port 2 Data Parsing Error: {e}")
            return None, None
        
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
            self.logger.info(f"Disconnected from Port {port_number}")
        else:
            success, message = self.serial_controller.connect(port, baudrate, port_number)
            self.append_log(message)
            self.logger.info(message)
            if success:
                button.setText("Disconnect")
                self.start_receiving_thread(port_number)

    def start_receiving_thread(self, port_number):
        thread = threading.Thread(target=self.receive_data_loop, args=(port_number,), daemon=True)
        thread.start()
        self.logger.info(f"Started receiving thread for Port {port_number}")

    # def receive_data_loop(self, port_number):
    #     while True:
    #         data = self.serial_controller.receive_data(port_number)
    #         if data:
    #             if port_number == 1:
    #                 pressure, temperature = self.data_processor.process_data(data)
    #                 if pressure is not None and temperature is not None:
    #                     self.update_lcd_displays(pressure, temperature)
    #                     self.calculate_and_display_QNH_QFE_QFF(pressure, temperature)
    #             else:
    #                 self.process_port2_data(data)
    #         time.sleep(0.1)

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
        self.logger.info(f"Calculated QFE={QFE:.2f}, QNH={QNH:.2f}, QFF={QFF:.2f}")

    def send_command(self):
        command = self.command_input.text().strip()
        if command:
            # 명령을 두 포트에 모두 전송 (필요에 따라 수정 가능)
            self.serial_controller.send_command(command, 1)
            self.serial_controller.send_command(command, 2)
            self.append_log(f"Sent command to both ports: {command}")
            self.logger.info(f"Sent command to both ports: {command}")
            self.command_input.clear()

    def update_lcd_displays(self, pressure, temperature):
        self.lcd_pressure.display(pressure)
        self.lcd_temperature.display(temperature)

    def append_log(self, message):
        self.log_output.append(message)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # self.logger.info(message)

    def update_button_state(self, connected, port_number):
        if port_number == 1:
            button = self.connect_button1
        else:
            button = self.connect_button2

        if connected:
            button.setText("Disconnect")
        else:
            button.setText("Connect")