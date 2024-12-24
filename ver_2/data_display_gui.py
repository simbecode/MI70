# data_display_gui.py

import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QDialog, QFormLayout, QDateTimeEdit, QCheckBox,
    QComboBox, QGridLayout, QStatusBar, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QKeySequence, QIcon
import pyqtgraph as pg
from datetime import datetime, timedelta
import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def resource_path(relative_path):
    """ PyInstaller가 생성한 임시 경로에서 리소스를 가져옴 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class DataDisplayGUI(QMainWindow):
    def __init__(self, data_queue, data_receiver, ds):
        super().__init__()
        
        plt.rcParams['font.family'] ='Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] =False

        # settings.json 파일 경로 설정
        self.settings_file = os.path.join(r'C:\Sitech', 'settings.json')

        # 단위 설정 로드
        self.load_unit_settings()        

        self.data_queue = data_queue
        self.data_receiver = data_receiver
        self.ds = ds  # DataStorage 인스턴스 추가
        self.latest_data = {}
        self.connection_status = {}
        self.is_fullscreen = False  # 전체 화면 여부를 나타내는 플래그

        # 초기 폰트 설정을 저장할 딕셔너리
        self.initial_fonts = {}
        # 초기 창 크기를 저장할 변수
        self.initial_geometry = None

        self.barometer_port_closed = False  # 기압계 포트 닫힘 상태를 추적하는 플래그 추가

        self.init_ui()
        self.apply_styles()

        # 데이터 업데이트 타이머 설정
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # 1초마다 업데이트

        # 센서 상태 확인 타이머 설정
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_sensor_status)
        self.status_timer.start(1000)  # 1초마다 상태 확인

        # 상태바 시간 업데이트 타이머 설정
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_current_time)
        self.time_timer.start(1000)  # 1초마다 시간 업데이트
        
        self.barometer_reconnect_timer = QTimer()
        self.barometer_reconnect_timer.timeout.connect(self.send_reconnect_command)
        self.barometer_reconnect_timer.start(1000)  # 1초마다 타이머 실행
        
    def init_ui(self):
        self.setWindowTitle("실황 정보")
        
        # 아이콘 파일 경로를 동적으로 설정
        icon_path = resource_path("icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 창 초기 크기 설정 및 저장
        self.resize(600, 400)
        self.initial_geometry = self.geometry()  # 초기 창 크기를 저장합니다
        

        # 메인 위젯 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 레이아웃 설정
        self.main_layout = QVBoxLayout()
        main_widget.setLayout(self.main_layout)

        # 폰트 설정
        custom_font = QFont("나눔스퀘어_ac")

        # 데이터 표시를 위한 레이블 생성
        self.label_pressure = QLabel("기압(hPa):")
        self.label_pressure.setFont(custom_font)  # 폰트 설정
        self.value_pressure = QLabel("-")
        self.value_pressure.setFont(custom_font)  # ���트 설정
        self.label_temperature_barometer = QLabel("기압계 온도(°C):")
        self.label_temperature_barometer.setFont(custom_font)  # 폰트 설정
        self.value_temperature_barometer = QLabel("-")
        self.value_temperature_barometer.setFont(custom_font)  # 폰트 설정
        self.label_temperature_humidity = QLabel("온도(°C):")
        self.label_temperature_humidity.setFont(custom_font)  # 폰트 설정
        self.value_temperature_humidity = QLabel("-")
        self.value_temperature_humidity.setFont(custom_font)  # 폰트 설정
        self.label_humidity = QLabel("습도(%):")
        self.label_humidity.setFont(custom_font)  # 폰트 설정
        self.value_humidity = QLabel("-")
        self.value_humidity.setFont(custom_font)  # 폰트 설정
        self.label_QNH = QLabel("QNH:")
        self.label_QNH.setFont(custom_font)  # 폰트 설정
        self.value_QNH = QLabel("-")
        self.value_QNH.setFont(custom_font)  # 폰트 설정
        self.label_QFE = QLabel("QFE:")
        self.label_QFE.setFont(custom_font)  # 폰트 설정
        self.value_QFE = QLabel("-")
        self.value_QFE.setFont(custom_font)  # 폰트 설정
        self.label_QFF = QLabel("QFF:")
        self.label_QFF.setFont(custom_font)  # 폰트 설정
        self.value_QFF = QLabel("-")
        self.value_QFF.setFont(custom_font)  # 폰트 설정

        # 데이터 표시 레이아웃 설정
        grid_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.label_pressure)
        left_layout.addWidget(self.value_pressure)
        left_layout.addWidget(self.label_temperature_barometer)
        left_layout.addWidget(self.value_temperature_barometer)
        left_layout.addWidget(self.label_humidity)
        left_layout.addWidget(self.value_humidity)
        left_layout.addWidget(self.label_temperature_humidity)
        left_layout.addWidget(self.value_temperature_humidity)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.label_QNH)
        right_layout.addWidget(self.value_QNH)
        right_layout.addWidget(self.label_QFE)
        right_layout.addWidget(self.value_QFE)
        right_layout.addWidget(self.label_QFF)
        right_layout.addWidget(self.value_QFF)

        grid_layout.addLayout(left_layout)
        grid_layout.addLayout(right_layout)

        self.main_layout.addLayout(grid_layout)

        # 버튼 추가
        self.button_pressure = QPushButton("기압 데이터 조회")
        self.button_pressure.setFont(custom_font)  # 폰트 설정
        self.button_pressure.clicked.connect(lambda: self.show_data_selection_window(['pressure']))
        self.button_temperature = QPushButton("온도 데이터 조회")
        self.button_temperature.setFont(custom_font)  # 폰트 설정
        self.button_temperature.clicked.connect(lambda: self.show_data_selection_window(['temperature_barometer', 'temperature_humidity']))
        self.button_humidity = QPushButton("습도 데이터 조회")
        self.button_humidity.setFont(custom_font)  # 폰트 설정
        self.button_humidity.clicked.connect(lambda: self.show_data_selection_window(['humidity']))
        self.button_q_values = QPushButton("기압 기준 값")
        self.button_q_values.setFont(custom_font)  # 폰트 설정
        self.button_q_values.clicked.connect(lambda: self.show_data_selection_window(['QNH', 'QFE', 'QFF']))

        # 버튼 폰트 크기 조정
        small_font = QFont(custom_font)
        small_font.setPointSize(5)  # 원하는 작은 크기로 설정

        self.button_pressure.setFont(small_font)
        self.button_temperature.setFont(small_font)
        self.button_humidity.setFont(small_font)
        self.button_q_values.setFont(small_font)

        # 버튼 크기 조정
        # button_height = 10  # 버튼 높이 설정
        # button_width = 120  # 버튼 너비 설정
        # for button in [self.button_pressure, self.button_temperature, self.button_humidity, self.button_q_values]:
        #     button.setFixedSize(button_width, button_height)

        # 버튼을 가로로 정렬
        button_layout = QHBoxLayout()  # 수평 레이아웃으로 변경
        button_layout.addWidget(self.button_pressure)
        button_layout.addWidget(self.button_temperature)
        button_layout.addWidget(self.button_humidity)
        button_layout.addWidget(self.button_q_values)
        self.main_layout.addLayout(button_layout)

        # 상태바 생성 및 추가
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.current_time_label = QLabel()
        self.status_bar.addPermanentWidget(self.current_time_label)
        self.update_current_time()  # 초기 시간 설정

        # 객체명 설정 (스타일시트에서 사용하기 위해)
        self.setObjectName("MainWindow")
        self.label_pressure.setObjectName("labelPressure")
        self.value_pressure.setObjectName("valuePressure")
        self.label_temperature_barometer.setObjectName("labelTemperatureBarometer")
        self.value_temperature_barometer.setObjectName("valueTemperatureBarometer")
        self.label_temperature_humidity.setObjectName("labelTemperatureHumidity")
        self.value_temperature_humidity.setObjectName("valueTemperatureHumidity")
        self.label_humidity.setObjectName("labelHumidity")
        self.value_humidity.setObjectName("valueHumidity")
        self.label_QNH.setObjectName("labelQNH")
        self.value_QNH.setObjectName("valueQNH")
        self.label_QFE.setObjectName("labelQFE")
        self.value_QFE.setObjectName("valueQFE")
        self.label_QFF.setObjectName("labelQFF")
        self.value_QFF.setObjectName("valueQFF")
        
        # # 센서 상태 레이블 생성
        # self.label_barometer_status = QLabel("기압계 상태: 연결 안됨")
        # self.label_humidity_status = QLabel("습도계 상태: 연결 안됨")

        # # 레이아웃에 센서 상태 레이블 추가
        # left_layout.addWidget(self.label_barometer_status)
        # left_layout.addWidget(self.label_humidity_status)

        # 초기 폰트와 창 크기 저장 (버튼 생성 후에 호출)
        self.store_initial_fonts()
        self.initial_geometry = self.geometry()
        
    def update_sensor_status(self, sensor, connected):
        """
        센서 연결 상태(connected=True/False)에 따라 
        해당 센서의 값 표시 및 글자 색상(UI)를 업데이트.
        """
        if sensor == '기압계':
            if connected:
                # 정상 연결: 파란색, 기존 값 유지 (값은 update_display에서 계속 업데이트)
                self.value_pressure.setStyleSheet("color: blue;")
                self.value_temperature_barometer.setStyleSheet("color: blue;")
            else:
                # 연결 해제: 적색, 값은 '-'로 표시
                self.value_pressure.setText('-')
                self.value_temperature_barometer.setText('-')
                self.value_pressure.setStyleSheet("color: red;")
                self.value_temperature_barometer.setStyleSheet("color: red;")

        elif sensor == '습도계':
            if connected:
                # 정상 연결: 파란색, 기존 값 유지
                self.value_temperature_humidity.setStyleSheet("color: blue;")
                self.value_humidity.setStyleSheet("color: blue;")
            else:
                # 연결 해제: 적색, 값은 '-'로 표시
                self.value_temperature_humidity.setText('-')
                self.value_humidity.setText('-')
                self.value_temperature_humidity.setStyleSheet("color: red;")
                self.value_humidity.setStyleSheet("color: red;")
                
    def load_unit_settings(self):
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.qnh_unit = settings.get('qnh_unit', 'hPa')
                self.qfe_unit = settings.get('qfe_unit', 'hPa')
                self.qff_unit = settings.get('qff_unit', 'hPa')
                logging.info(f"단위 설정 로드: QNH - {self.qnh_unit}, QFE - {self.qfe_unit}, QFF - {self.qff_unit}")

                self.sensor_intervals = {
                    '기압계': 10,  # 기압계 기본 interval
                    '습도계': 10   # 습도계 기본 interval
                }
                # logging.info(f"하드코딩된 interval 값: {self.sensor_intervals}")

        except Exception as e:
            logging.error(f"설정 파일을 로드하는 중 오류 발생: {e}")
            # 기본 단위 설정
            self.qnh_unit = 'hPa'
            self.qfe_unit = 'hPa'
            self.qff_unit = 'hPa'
            # 기본 센서 interval 값 설정
            self.sensor_intervals = {'기압계': 10, '습도계': 10}
            
    def convert_unit(self, value, to_unit):
        """hPa 단위를 다른 단위로 변환"""
        if to_unit == 'hPa':
            return value
        elif to_unit == 'inchHg':
            return value * 0.029529983071445  # 1 hPa = 0.02953 inchHg
        elif to_unit == 'mb':
            return value  # 1 hPa = 1 mb
        else:
            logging.warning(f"알 수 없는 단위: {to_unit}")
            return value  # 알 수 없는 단위일 경우 그대로 반환
  
    def resizeEvent(self, event):
        """창 크기 변경 이벤트가 발생할 때 폰트와 버튼 크기를 비례적으로 조정"""
        if self.initial_geometry:
            # 창 크기 비율을 계산하여 폰트와 버튼 크기를 조정
            width_ratio = self.width() / self.initial_geometry.width()
            height_ratio = self.height() / self.initial_geometry.height()
            scale_factor = min(width_ratio, height_ratio) * 2.3
            self.adjust_sizes(scale_factor)
            
    def adjust_sizes(self, scale_factor):
        """scale_factor에 따라 폰트와 버튼 크기를 비례적으로 조정"""
        for widget, initial_font in self.initial_fonts.items():
            font = QFont(initial_font)
            font.setPointSizeF(initial_font.pointSizeF() * scale_factor)
            widget.setFont(font)

        # 버튼 크기 조정
        button_height = int(30 * scale_factor)  # 버튼 높이를 비례적으로 조정
        for button in [self.button_pressure, self.button_temperature, self.button_humidity, self.button_q_values]:
            button.setFixedHeight(button_height)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 버튼 크기 자동 조정

    def store_initial_fonts(self):
        """초기 폰트를 저장하여 크기 조정 시 기준으로 사용"""
        widgets = [
            self.label_pressure, self.label_temperature_barometer, self.label_temperature_humidity,
            self.label_humidity, self.label_QNH, self.label_QFE, self.label_QFF,
            self.value_pressure, self.value_temperature_barometer, self.value_temperature_humidity,
            self.value_humidity, self.value_QNH, self.value_QFE, self.value_QFF,
            self.button_pressure, self.button_temperature, self.button_humidity, self.button_q_values
        ]
        for widget in widgets:
            self.initial_fonts[widget] = widget.font()

    def apply_styles(self):
        # 스타일시트 문자열 성
        style_sheet = """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QLabel {
            color: #333333;
        }
        QLabel#valuePressure, QLabel#valueTemperatureBarometer, QLabel#valueTemperatureHumidity,
        QLabel#valueHumidity, QLabel#valueQNH, QLabel#valueQFE, QLabel#valueQFF {
            font-weight: bold;
            color: #0000ff;
        }
        QPushButton {
            background-color: #f0f0f0;
            color: #000000;
            border-radius: 5px;
            padding: 1px;
        }
        QPushButton:hover {
            background-color: #d3d3d3;
        }
        """
        # 스타일시트 적용
        self.setStyleSheet(style_sheet)

    def store_initial_fonts(self):
        # 초기 폰트 설정을 저장
        widgets = [
            self.label_pressure, self.label_temperature_barometer, self.label_temperature_humidity,
            self.label_humidity, self.label_QNH, self.label_QFE, self.label_QFF,
            self.value_pressure, self.value_temperature_barometer, self.value_temperature_humidity,
            self.value_humidity, self.value_QNH, self.value_QFE, self.value_QFF,
            self.button_pressure, self.button_temperature, self.button_humidity, self.button_q_values
        ]
        for widget in widgets:
            self.initial_fonts[widget] = widget.font()

    def update_current_time(self):
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.current_time_label.setText(current_time)
        self.current_time_label.setFont(QFont("나눔스퀘어_ac ExtraBold", 20))

    def update_data(self):
        # 데이터 큐에서 데이터 가져오기
        while not self.data_queue.empty():
            data = self.data_queue.get()
            # print("[update_data] dequeued data:", data)
            self.handle_new_data(data)
            

    def handle_new_data(self, data):
        """
        큐에서 전달된 데이터(센서 측정값, 포트 상태 등)를 받아,
        최신 데이터로 갱신하고 UI를 업데이트하는 함수.
        """

        # 1) sensor와 timestamp, status를 꺼냄
        sensor = data.get('sensor')
        status = data.get('status', 'valid')  # default: 'valid'
        new_ts_str = data.get('timestamp')    # 새로 들어온 데이터의 타임스탬프 (문자열)

        # sensor가 없거나, 우리가 관심 없는 센서면 무시
        if sensor not in ('기압계', '습도계','계산값'):
            return

        # 2) 만약 'port_disconnected' 같 상태라면, 바로 처리
        if status == 'port_disconnected':
            # 예: 포트가 해제된 경우 즉시 '-' 표시, 이전 데이터 삭제
            self.disconnect_sensor_immediately(sensor)
            return

        # 3) 정상 or 기타 상태의 데이터인 경우 → 이전 데이터와 타임스탬프 비교
        old_data = self.latest_data.get(sensor)
        old_ts_str = old_data.get('timestamp') if old_data else None

        # (A) 새 데이터에 timestamp가 없는 경우 → 그냥 로그 찍고 반환할 수도 있음
        if not new_ts_str:
            # timestamp 자체가 없으면, 일단 저장을 안 하거나 default로 처리
            logging.warning(f"New data for {sensor} has no timestamp! Data={data}")
            return

        # (B) 이전 데이터의 timestamp가 없는 경우 → (최초 데이터, 혹은 None)
        if not old_ts_str:
            # 이전 데이터가 없었거나 timestamp가 없었다면,
            # 그냥 '새 데이터'를 받아들이고 진행
            self.latest_data[sensor] = data
            self.connection_status[sensor] = datetime.now()
            # UI 업데이트
            self.update_display()
            return

        # (C) 이제 둘 다 문자열이라면 strptime으로 비교 가능
        try:
            new_ts = datetime.strptime(new_ts_str, '%Y-%m-%d %H:%M:%S')
            old_ts = datetime.strptime(old_ts_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as e:
            # 만약 파싱 실패하면 -> 로그 찍고 그냥 새 데이터로 덮어쓸 수도 있음
            logging.error(f"Timestamp parse error: {e}, new_ts={new_ts_str}, old_ts={old_ts_str}")
            self.latest_data[sensor] = data
            self.connection_status[sensor] = datetime.now()
            self.update_display()
            return

        # (D) 타임스탬프 비교
        if new_ts <= old_ts:
            # 더 과거 데이터라면 무시하거나 로그만 찍음
            # logging.info(f"Ignored old (or same) data for {sensor}. old_ts={old_ts_str}, new_ts={new_ts_str}")
            return
        else:
            # 정말 '새로운' 데이터이므로 업데이트
            self.latest_data[sensor] = data
            self.connection_status[sensor] = datetime.now()
            self.update_display()
 
    def disconnect_sensor_immediately(self, sensor):
        """
        물리적으로 포트가 해제된 센서에 대해
        1) 값은 '-'로 표시
        2) 이전 latest_data 제거
        3) 적색 등으로 표시
        """
        # 1) 값 '-' 표시
        if sensor == '기압계':
            self.value_pressure.setText('-')
            self.value_temperature_barometer.setText('-')
            # 색상도 빨강
            self.value_pressure.setStyleSheet("color: red;")
            self.value_temperature_barometer.setStyleSheet("color: red;")

        elif sensor == '습도계':
            self.value_temperature_humidity.setText('-')
            self.value_humidity.setText('-')
            self.value_temperature_humidity.setStyleSheet("color: red;")
            self.value_humidity.setStyleSheet("color: red;")

        # 2) self.latest_data에서 제거
        if sensor in self.latest_data:
            del self.latest_data[sensor]

        # 3) 마지막 수시각도 제거 or None 처리
        if sensor in self.connection_status:
            del self.connection_status[sensor] 
 
 
    def update_display(self):
        def format_float(value, default="-"):
            """
            숫자 value를 받아 소수점 둘째자리까지 문자열로 변환합니다.
            변환 불가능하거나 None/'-'인 경우 default 문자열을 반환합니다.
            """
            if value is None or value == '-':
                return default
            try:
                return f"{float(value):.2f}"
            except (ValueError, TypeError):
                return default
                
        # 최신 데이터 가져오기
        calc_data = self.latest_data.get('계산값', {})
        barometer_data = self.latest_data.get('기압계', {})
        humidity_data = self.latest_data.get('습도계', {})

        # --- 1) 기압계 온도(temperature_barometer) ---
        barometer_temp = barometer_data.get('temperature_barometer')
        # 헬퍼 함수로 2자리 소수점 변환
        self.value_temperature_barometer.setText(format_float(barometer_temp))

        # --- 2) 기압계 기압(pressure) ---
        barometer_pressure = barometer_data.get('pressure')
        self.value_pressure.setText(format_float(barometer_pressure))

        # --- 3) 습도계 온도(temperature_humidity) ---
        humidity_temp = humidity_data.get('temperature_humidity')
        self.value_temperature_humidity.setText(format_float(humidity_temp))

        # --- 4) 습도(humidity) ---
        humidity = humidity_data.get('humidity')
        self.value_humidity.setText(format_float(humidity))

        # --- 5) QNH, QFE, QFF (단위 변환 후 소수점 2자리) ---
        qnh = calc_data.get('QNH')  
        qfe = calc_data.get('QFE')  
        qff = calc_data.get('QFF')  

        if qnh is not None:
            qnh_converted = self.convert_unit(qnh, self.qnh_unit)  
            self.value_QNH.setText(f"{format_float(qnh_converted, default='-')} {self.qnh_unit}")
        else:
            self.value_QNH.setText('-')

        if qfe is not None:
            qfe_converted = self.convert_unit(qfe, self.qfe_unit)
            self.value_QFE.setText(f"{format_float(qfe_converted, default='-')} {self.qfe_unit}")
        else:
            self.value_QFE.setText('-')

        if qff is not None:
            qff_converted = self.convert_unit(qff, self.qff_unit)
            self.value_QFF.setText(f"{format_float(qff_converted, default='-')} {self.qff_unit}")
        else:
            self.value_QFF.setText('-')
    
    def mark_old_data_as_red(self, sensor):
        if sensor == '기압계':
            self.value_pressure.setStyleSheet("color: red;")
            self.value_temperature_barometer.setStyleSheet("color: red;")
        elif sensor == '습도계':
            self.value_temperature_humidity.setStyleSheet("color: red;")
            self.value_humidity.setStyleSheet("color: red;")

    def mark_data_as_normal(self, sensor):
        if sensor == '기압계':
            self.value_pressure.setStyleSheet("color: blue;")
            self.value_temperature_barometer.setStyleSheet("color: blue;")
        elif sensor == '습도계':
            self.value_temperature_humidity.setStyleSheet("color: blue;")
            self.value_humidity.setStyleSheet("color: blue;")
            
            
    def check_sensor_status(self):       
        current_time = datetime.now()
        for sensor in ['기압계', '습도계']:
            last_received = self.connection_status.get(sensor)
            if last_received:
                time_diff = (current_time - last_received).total_seconds()

                if time_diff > 60:
                    # ★ 1분 이상  데이터 없음 → 적색 표시 (값은 그대로 유지)
                    self.mark_old_data_as_red(sensor)
                else:
                    # 데이터가 정상적으로 어오고 있음 → 파란색(등) 표시
                    self.mark_data_as_normal(sensor)
            else:
                # 아직 한 번도 데이터를 못 받았다면 (또는 reset됨)
                # 여기서는 그냥 적색으로 표시 or '-' 로 표할 수도 있음
                self.mark_data_as_red(sensor)

    def close_port_connection(self, sensor):
        """센서의 포트 연결을 닫는 함수"""
        if sensor == '기압계':
            # 기압계 포트 닫기 로직 추가
            logging.info("기압계 포트 연결을 닫습니다.")
            if self.data_receiver:
                self.data_receiver.close_sensor_port(sensor)
        elif sensor == '습도계':
            # 습도계 포트 닫기 로직 추가
            logging.info("습도계 포트 연결을 닫습니다.")
            # 실제 포트 닫기 코드 추가

    def show_data_selection_window(self, default_selected_data_types):
        dialog = QDialog(self)
        dialog.setWindowTitle("데이터 선택")

        # 메인 레이아웃 생성
        layout = QVBoxLayout(dialog)

        # 데이터 타입 선택 레이블
        data_type_label = QLabel("데이터 타입 선택:")
        layout.addWidget(data_type_label)

        # 체크박스 생성
        self.checkbox_pressure = QCheckBox("기압")
        self.checkbox_temperature_barometer = QCheckBox("기압계 온도")
        self.checkbox_temperature_humidity = QCheckBox("습도계 온도")
        self.checkbox_humidity = QCheckBox("습도")
        self.checkbox_QNH = QCheckBox("QNH")
        self.checkbox_QFE = QCheckBox("QFE")
        self.checkbox_QFF = QCheckBox("QFF")

        # 기본 선택 설정
        data_type_checkboxes = {
            'pressure': self.checkbox_pressure,
            'temperature_barometer': self.checkbox_temperature_barometer,
            'temperature_humidity': self.checkbox_temperature_humidity,
            'humidity': self.checkbox_humidity,
            'QNH': self.checkbox_QNH,
            'QFE': self.checkbox_QFE,
            'QFF': self.checkbox_QFF
        }

        for data_type in default_selected_data_types:
            checkbox = data_type_checkboxes.get(data_type)
            if checkbox:
                checkbox.setChecked(True)

        # 체크박스 레이아웃
        checkbox_layout = QGridLayout()
        checkbox_layout.addWidget(self.checkbox_pressure, 0, 0)
        checkbox_layout.addWidget(self.checkbox_temperature_barometer, 0, 1)
        checkbox_layout.addWidget(self.checkbox_temperature_humidity, 1, 0)
        checkbox_layout.addWidget(self.checkbox_humidity, 1, 1)
        checkbox_layout.addWidget(self.checkbox_QNH, 2, 0)
        checkbox_layout.addWidget(self.checkbox_QFE, 2, 1)
        checkbox_layout.addWidget(self.checkbox_QFF, 3, 0)

        layout.addLayout(checkbox_layout)

        # 기간 선택 레이블
        time_period_label = QLabel("기간 선택:")
        layout.addWidget(time_period_label)

        # 기간 선택 콤보박스
        self.combo_time_period = QComboBox()
        self.combo_time_period.addItem("사용자 정의")
        self.combo_time_period.addItem("오늘")
        self.combo_time_period.addItem("1시간 전")
        self.combo_time_period.addItem("1일 전")
        self.combo_time_period.addItem("1주일 전")
        layout.addWidget(self.combo_time_period)

        # 사용자 정의 기간 입력 위젯 (시작 시간, 종료 시간)
        self.datetime_widgets = QWidget()
        datetime_layout = QFormLayout()

        self.start_datetime_edit = QDateTimeEdit()
        self.start_datetime_edit.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.start_datetime_edit.setCalendarPopup(True)
        datetime_layout.addRow("시작 시간:", self.start_datetime_edit)

        self.end_datetime_edit = QDateTimeEdit()
        self.end_datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.end_datetime_edit.setCalendarPopup(True)
        datetime_layout.addRow("종료 시간:", self.end_datetime_edit)

        self.datetime_widgets.setLayout(datetime_layout)
        layout.addWidget(self.datetime_widgets)

        # 콤보박스 선택에 따라 사용자 정의 기간 입력 위젯 표시/숨김
        self.combo_time_period.currentIndexChanged.connect(self.on_time_period_changed)
        self.on_time_period_changed(self.combo_time_period.currentIndex())  # 초기 설정

        # 확인 및 취소 버튼
        button_layout = QHBoxLayout()
        ok_button = QPushButton("확인")
        ok_button.clicked.connect(lambda: self.on_data_selection_confirmed(dialog))
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.exec_()

    def on_time_period_changed(self, index):
        # '사용자 정의'가 선택된 경우에만 datetime_widgets를 보여줌
        if self.combo_time_period.currentText() == "사용자 정의":
            self.datetime_widgets.show()
        else:
            self.datetime_widgets.hide()

    def on_data_selection_confirmed(self, dialog):
        # 선택된 데이터 타입 가져오기
        selected_data_types = []
        if self.checkbox_pressure.isChecked():
            selected_data_types.append('pressure')
        if self.checkbox_temperature_barometer.isChecked():
            selected_data_types.append('temperature_barometer')
        if self.checkbox_temperature_humidity.isChecked():
            selected_data_types.append('temperature_humidity')
        if self.checkbox_humidity.isChecked():
            selected_data_types.append('humidity')
        if self.checkbox_QNH.isChecked():
            selected_data_types.append('QNH')
        if self.checkbox_QFE.isChecked():
            selected_data_types.append('QFE')
        if self.checkbox_QFF.isChecked():
            selected_data_types.append('QFF')

        if not selected_data_types:
            QMessageBox.warning(self, "경고", "최소 한 개의 데이터 타입을 선택해야 합니다.")
            return

        # 기간 선택 처리
        time_period = self.combo_time_period.currentText()
        if time_period == "사용자 정의":
            start_datetime = self.start_datetime_edit.dateTime().toPyDateTime()
            end_datetime = self.end_datetime_edit.dateTime().toPyDateTime()
        else:
            end_datetime = datetime.now()
            if time_period == "오늘":
                start_datetime = datetime.combine(datetime.today(), datetime.min.time())
            elif time_period == "1시간 전":
                start_datetime = end_datetime - timedelta(hours=1)
            elif time_period == "1일 전":
                start_datetime = end_datetime - timedelta(days=1)
            elif time_period == "1주일 전":
                start_datetime = end_datetime - timedelta(weeks=1)
            else:
                # 예외 처리
                start_datetime = None

        if start_datetime is None or end_datetime is None:
            QMessageBox.warning(self, "경고", "기간을 올바르게 선택해 주세요.")
            return

        dialog.accept()

        # 데이터 로드 및 그래프 표시
        self.load_and_plot_data(selected_data_types, start_datetime, end_datetime)

    def load_and_plot_data(self, data_types, start_datetime, end_datetime):
        # CSV 파일에서 데이터 로드
        data_list = self.load_data_from_csv(data_types, start_datetime, end_datetime)

        if data_list is not None:
            df = pd.DataFrame(data_list)
            #데이터 보간 처리
            df = df.set_index('timestamp').resample('T').mean().interpolate().reset_index()
            
            self.plot_data(df, data_types)
        else:
            QMessageBox.information(self, "정보", "선택한 기간에 데이터가 없습니다.")

    def load_data_from_csv(self, data_types, start_datetime, end_datetime):
        data_list = []

        # 시작 날짜부터 종료 날짜까지 반복
        current_date = start_datetime.date()
        end_date = end_datetime.date()
        delta = timedelta(days=1)

        base_dir = self.ds.base_dir  # DataStorage의 데이터 저장 경로

        while current_date <= end_date:
            # 파일 경로 생성
            month_str = current_date.strftime('%Y-%m')
            date_str = current_date.strftime('%Y-%m-%d')
            csv_file = os.path.join(base_dir, month_str, date_str + '.csv')

            if os.path.exists(csv_file):
                # CSV 파일 읽기
                try:
                    data = pd.read_csv(csv_file)
                except Exception as e:
                    print(f"CSV 파일을 읽는 중 오류 발생: {csv_file}, {e}")
                    current_date += delta
                    continue

                # timestamp 열을 datetime 형식으로 변환
                data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')

                # 선택한 기간으로 필터링
                data = data[(data['timestamp'] >= start_datetime) & (data['timestamp'] <= end_datetime)]

                if not data.empty:
                    # 필요한 데이터 타입만 선택
                    columns_to_keep = ['timestamp'] + data_types
                    data = data[columns_to_keep]
                    data_list.append(data)
            else:
                print(f"CSV 파일을 찾을 수 없습니다: {csv_file}")

            current_date += delta

        if data_list:
            # 데이터프레임 연결
            df = pd.concat(data_list, ignore_index=True)
            # 시간순으로 정렬
            df.sort_values('timestamp', inplace=True)
            return df
        else:
            return None

    def plot_data(self, df, data_types):
        if df.empty:
            QMessageBox.information(self, "정보", "데이터가 없습니다.")
            return

        # 스타일 적용
        plt.style.use('ggplot')

        # Figure와 첫 번째 Y축 생성
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # X축 포맷 지정
        ax1.set_xlabel('Timestamp')
        
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator()) #자동으로 조정
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)
        
        # Y축 포맷 지정
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.2f}'))

        # 첫 번째 데이터 타입을 첫 번째 Y축에 플롯
        color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_index = 0

        y_axes = [ax1]
        lines = []
        labels = []

        first_data_type = data_types[0]
        ax = ax1
        color = color_cycle[color_index % len(color_cycle)]
        line, = ax.plot(df['timestamp'], df[first_data_type], label=first_data_type, linestyle='-', color=color)
        lines.append(line)
        labels.append(first_data_type)
        ax.set_ylabel(first_data_type, color=color)
        ax.tick_params(axis='y', labelcolor=color)
        color_index += 1

        # 나머지 데이터 타입들을 추가 Y축에 플롯
        for data_type in data_types[1:]:
            ax = ax1.twinx()
            y_axes.append(ax)
            ax.spines['right'].set_position(('outward', 60 * (len(y_axes) - 2)))  # Y축 간격 조정
            color = color_cycle[color_index % len(color_cycle)]
            line, = ax.plot(df['timestamp'], df[data_type], label=data_type, linestyle='-', color=color)
            lines.append(line)
            labels.append(data_type)
            ax.set_ylabel(data_type, color=color)
            ax.tick_params(axis='y', labelcolor=color)
            color_index += 1

        # 범례 설정
        fig.legend(lines, labels, loc='upper right', bbox_to_anchor=(1, 1), ncol=1)

        # 그리드 및 레이아웃 설정
        plt.title('데이터 그래프')
        plt.grid(True, linestyle='--', linewidth=0.7)
        fig.tight_layout()

        plt.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showFullScreen()  # 전체 화면 모드로 전환
            self.is_fullscreen = True
            self.adjust_font_sizes(scale_factor=6.0)  # 폰트 크기 확대
        else:
            self.showNormal()  # 일반 모드로 전환
            self.is_fullscreen = False
            self.adjust_font_sizes(scale_factor=1.0)  # 폰트 크기 초기화
            
            # 창 크기를 수동으로 설정
            self.resize(self.initial_geometry.width(), self.initial_geometry.height())  # 초기 크기로 복원

    def adjust_font_sizes(self, scale_factor=1.0):
        # 레블과 버튼의 폰트 크기를 조절
        # print(f"Adjusting font sizes with scale factor: {scale_factor}")
        
        # 초기 폰트를 기반으로 폰트 크기 조절
        for widget, initial_font in self.initial_fonts.items():
            font = QFont(initial_font)
            point_size = font.pointSize()
            pixel_size = font.pixelSize()
            
            if point_size > 0:
                new_point_size = int(point_size * scale_factor)
                font.setPointSize(new_point_size)
            elif pixel_size > 0:
                new_pixel_size = int(pixel_size * scale_factor)
                font.setPixelSize(new_pixel_size)
            else:
                # 포인트 크기와 픽셀 크기 모두 0인 경우 기본 크기 설정
                default_point_size = 12  # 원하는 기본 폰트 크기로 설정
                font.setPointSize(int(default_point_size * scale_factor))
            
            widget.setFont(font)

        # 창 크기를 초기화하는 조건 추가
        if not self.is_fullscreen:
            self.adjust_window_size()  # 창 크기 조정 메서드 호출

    def adjust_window_size(self):
        # 초기 크기로 창 크기 조정
        self.resize(self.initial_geometry.width(), self.initial_geometry.height())  # 초기 크기로 복원

    def store_initial_fonts(self):
        # 초기 폰트 설정을 저장
        widgets = [
            self.label_pressure, self.label_temperature_barometer, self.label_temperature_humidity,
            self.label_humidity, self.label_QNH, self.label_QFE, self.label_QFF,
            self.value_pressure, self.value_temperature_barometer, self.value_temperature_humidity,
            self.value_humidity, self.value_QNH, self.value_QFE, self.value_QFF,
            self.button_pressure, self.button_temperature, self.button_humidity, self.button_q_values
        ]
        for widget in widgets:
            # 위젯에 폰트가 설정되어 있지 않다면 기본 폰트를 설정
            if not widget.font():
                widget.setFont(QFont())
            self.initial_fonts[widget] = widget.font()
            
    def send_reconnect_command(self):
        """기압계 센서에 재연결 명령어를 전송"""
        if '기압계' in self.connection_status and not self.connection_status['기압계']:
            # 기압계 센서가 연결 끊김 상태일 때만 명령어 전송
            self.data_receiver.reconnect_sensor('기압계')  # 'r' 명령어 전송
            

            
# 테스트 코드 (단독 실행 시)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    from queue import Queue
    data_queue = Queue()
    data_receiver = None  # 실제 데이터 수신 객체로 대체해야 함
    class DummyDataStorage:
        def __init__(self):
            self.base_dir = r'C:\Sitech\data'  # 실제 데이터 저장 경로로 변경해야 함
    ds = DummyDataStorage()
    gui = DataDisplayGUI(data_queue, data_receiver, ds)
    gui.show()
    sys.exit(app.exec_())
