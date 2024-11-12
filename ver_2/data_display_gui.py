# data_display_gui.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QDialog, QFormLayout, QDateTimeEdit, QCheckBox,
    QComboBox, QGridLayout, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QKeySequence
import pyqtgraph as pg
from datetime import datetime, timedelta
import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class DataDisplayGUI(QMainWindow):
    def __init__(self, data_queue, data_receiver, ds):
        super().__init__()

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

    def init_ui(self):
        self.setWindowTitle("데이터 표시 GUI")

        # 메인 위젯 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 레이아웃 설정
        self.main_layout = QVBoxLayout()
        main_widget.setLayout(self.main_layout)

        # 데이터 표시를 위한 레이블 생성
        self.label_pressure = QLabel("압력:")
        self.value_pressure = QLabel("-")
        self.label_temperature_barometer = QLabel("기압계 온도:")
        self.value_temperature_barometer = QLabel("-")
        self.label_temperature_humidity = QLabel("습도계 온도:")
        self.value_temperature_humidity = QLabel("-")
        self.label_humidity = QLabel("습도:")
        self.value_humidity = QLabel("-")
        self.label_QNH = QLabel("QNH:")
        self.value_QNH = QLabel("-")
        self.label_QFE = QLabel("QFE:")
        self.value_QFE = QLabel("-")
        self.label_QFF = QLabel("QFF:")
        self.value_QFF = QLabel("-")

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
        button_layout = QVBoxLayout()  # 수직 레이아웃으로 변경
        button_row1 = QHBoxLayout()  # 첫 번째 행 레이아웃
        button_row2 = QHBoxLayout()  # 두 번째 행 레이아웃

        self.button_pressure = QPushButton("압력 데이터 조회")
        self.button_pressure.clicked.connect(lambda: self.show_data_selection_window(['pressure']))
        self.button_temperature = QPushButton("온도 데이터 조회")
        self.button_temperature.clicked.connect(lambda: self.show_data_selection_window(['temperature_barometer', 'temperature_humidity']))
        self.button_humidity = QPushButton("습도 데이터 조회")
        self.button_humidity.clicked.connect(lambda: self.show_data_selection_window(['humidity']))
        self.button_q_values = QPushButton("Q값 데이터 조회")
        self.button_q_values.clicked.connect(lambda: self.show_data_selection_window(['QNH', 'QFE', 'QFF']))

        button_row1.addWidget(self.button_pressure)
        button_row1.addWidget(self.button_temperature)
        button_row2.addWidget(self.button_humidity)
        button_row2.addWidget(self.button_q_values)

        button_layout.addLayout(button_row1)  # 첫 번째 행 추가
        button_layout.addLayout(button_row2)  # 두 번째 행 추가
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

        # 초기 폰트와 창 크기 저장 (버튼 생성 후에 호출)
        self.store_initial_fonts()
        self.initial_geometry = self.geometry()

    def apply_styles(self):
        # 스타일시트 문자열 작성
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
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #45a049;
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
        self.current_time_label.setText(f"현재 시간: {current_time}")

    def update_data(self):
        # 데이터 큐에서 데이터 가져오기
        while not self.data_queue.empty():
            data = self.data_queue.get()
            self.handle_new_data(data)

    def handle_new_data(self, data):
        sensor = data.get('sensor')
        if sensor:
            self.latest_data[sensor] = data
            self.connection_status[sensor] = datetime.now()

        # 데이터 업데이트
        self.update_display()

    def update_display(self):
        # 최신 데이터 가져오기
        calc_data = self.latest_data.get('계산값', {})
        barometer_data = self.latest_data.get('기압계', {})
        humidity_data = self.latest_data.get('습도계', {})
        
        # 기압계 온도 표시
        temperature_barometer = barometer_data.get('temperature_barometer', '-')
        self.value_temperature_barometer.setText(str(temperature_barometer))

        # 습도계 온도 표시
        temperature_humidity = humidity_data.get('temperature_humidity', '-')
        self.value_temperature_humidity.setText(str(temperature_humidity))

        # 나머지 데이터 표시
        self.value_pressure.setText(str(calc_data.get('pressure', '-')))
        self.value_humidity.setText(str(humidity_data.get('humidity', '-')))
        self.value_QNH.setText(str(calc_data.get('QNH', '-')))
        self.value_QFE.setText(str(calc_data.get('QFE', '-')))
        self.value_QFF.setText(str(calc_data.get('QFF', '-')))

    def check_sensor_status(self):
        # 센서 연결 상태 확인 (생략)
        pass

    def show_data_selection_window(self, default_selected_data_types):
        dialog = QDialog(self)
        dialog.setWindowTitle("데이터 선택")

        # 메인 레이아웃 생성
        layout = QVBoxLayout(dialog)

        # 데이터 타입 선택 레이블
        data_type_label = QLabel("데이터 타입 선택:")
        layout.addWidget(data_type_label)

        # 체크박스 생성
        self.checkbox_pressure = QCheckBox("압력")
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
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)

        # 첫 번째 데이터 타입을 첫 번째 Y축에 플롯
        color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_index = 0

        y_axes = [ax1]
        lines = []
        labels = []

        first_data_type = data_types[0]
        ax = ax1
        color = color_cycle[color_index % len(color_cycle)]
        line, = ax.plot(df['timestamp'], df[first_data_type], label=first_data_type, color=color)
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
            line, = ax.plot(df['timestamp'], df[data_type], label=data_type, color=color)
            lines.append(line)
            labels.append(data_type)
            ax.set_ylabel(data_type, color=color)
            ax.tick_params(axis='y', labelcolor=color)
            color_index += 1

        # 범례 설정
        ax1.legend(lines, labels, loc='upper left')

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
        # 레이블과 버튼의 폰트 크기를 조절
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
