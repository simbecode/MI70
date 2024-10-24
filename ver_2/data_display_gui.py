# data_display_gui.py

import time
import logging
from datetime import datetime, timedelta
from clickable_label import ClickableLabel
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from data_storage import DataStorage
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QMessageBox, QDateTimeEdit, QMainWindow
)


class DataDisplayGUI(QMainWindow):
    def __init__(self, data_queue, data_receiver):
        super().__init__()
        self.data_queue = data_queue
        self.dr = data_receiver
        self.ds = DataStorage(base_dir='C:\\Sitech')
        

        # latest_data 초기화
        self.latest_data = {
            'pressure': 'N/A',
            'temperature_barometer': 'N/A',
            'temperature_humidity': 'N/A',
            'humidity': 'N/A',
            'QNH': 'N/A',
            'QFE': 'N/A',
            'QFF': 'N/A'
        }
        self.is_fullscreen = False
        
        self.init_ui()

        # 상태 확인 타이머 설정
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_sensor_status)
        self.status_timer.start(1000)  # 1초마다 상태 확인

        self.dr.data_callback = self.handle_new_data
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F11:
        # and event.modifiers() & QtCore.Qt.AltModifier:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
            

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            # 전체 화면 모드에서 일반 모드로 전환
            self.showNormal()
            self.is_fullscreen = False
        else:
            # 일반 모드에서 전체 화면 모드로 전환
            self.showFullScreen()
            self.is_fullscreen = True            

    @pyqtSlot(dict)
    def handle_new_data(self, data):
        # _update_latest_data를 직접 호출합니다.
        self._update_latest_data(data)
        
    def _update_latest_data(self, data):
        if data['sensor'] == '기압계':
            self.latest_data['pressure'] = data.get('pressure', 'N/A')
            self.latest_data['temperature_barometer'] = data.get('temperature', 'N/A')
        elif data['sensor'] == '습도계':
            self.latest_data['temperature_humidity'] = data.get('temperature', 'N/A')
            self.latest_data['humidity'] = data.get('humidity', 'N/A')
        elif data['sensor'] == '계산값':
            self.latest_data['QNH'] = data.get('QNH', 'N/A')
            self.latest_data['QFE'] = data.get('QFE', 'N/A')
            self.latest_data['QFF'] = data.get('QFF', 'N/A')
            
                # 라벨 업데이트
        self.label_pressure.setText(str(self.latest_data['pressure']))
        self.label_temperature_barometer.setText(str(self.latest_data['temperature_barometer']))
        self.label_temperature_humidity.setText(str(self.latest_data['temperature_humidity']))
        self.label_humidity.setText(str(self.latest_data['humidity']))
        self.label_qnh.setText(str(self.latest_data['QNH']))
        self.label_qfe.setText(str(self.latest_data['QFE']))
        self.label_qff.setText(str(self.latest_data['QFF']))
            
    def check_sensor_status(self):
        # 각 센서의 상태를 확인하고 UI 업데이트
        for sensor_name in self.dr.connection_status.keys():
            is_connected = self.dr.connection_status[sensor_name]

            # 상태에 따른 색상 결정
            if is_connected:
                color = 'blue'  # 정상 상태
            else:
                color = 'red'  # 포트 연결 끊김 또는 데이터 미수신

            # 해당 센서의 라벨 색상 업데이트
            self.update_label_color(sensor_name, color)

    def update_label_color(self, sensor_name, color):
        # 라벨의 스타일 시트를 업데이트하여 색상 변경
        if sensor_name == '기압계':
            self.label_pressure.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.label_temperature_barometer.setStyleSheet(f"color: {color}; font-weight: bold;")
        elif sensor_name == '습도계':
            self.label_humidity.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.label_temperature_humidity.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        
    def init_ui(self):
        self.setWindowTitle("이동형 기압계 표출프로그램")

        central_widget = QtWidgets.QWidget()
        main_layout = QVBoxLayout(central_widget)


        # 기압계 그룹 박스
        barometer_group = QtWidgets.QGroupBox("기압계")
        barometer_layout = QHBoxLayout()
        self.label_pressure = ClickableLabel(str(self.latest_data['pressure']))
        self.label_pressure.setObjectName("pressureLabel")
        self.label_temperature_barometer = ClickableLabel(str(self.latest_data['temperature_barometer']))
        self.label_temperature_barometer.setObjectName("temperatureBarometerLabel")
        barometer_layout.addWidget(QtWidgets.QLabel("기압값 (hPa):"))
        barometer_layout.addWidget(self.label_pressure)
        barometer_layout.addWidget(QtWidgets.QLabel("온도값 (°C):"))
        barometer_layout.addWidget(self.label_temperature_barometer)
        barometer_group.setLayout(barometer_layout)
        main_layout.addWidget(barometer_group)

        # 습도계 그룹 박스
        humidity_group = QtWidgets.QGroupBox("습도계")
        humidity_layout = QHBoxLayout()
        self.label_humidity = ClickableLabel(str(self.latest_data['humidity']))
        self.label_humidity.setObjectName("humidityLabel")
        self.label_temperature_humidity = ClickableLabel(str(self.latest_data['temperature_humidity']))
        self.label_temperature_humidity.setObjectName("temperatureHumidityLabel")
        humidity_layout.addWidget(QtWidgets.QLabel("습도값 (%):"))
        humidity_layout.addWidget(self.label_humidity)
        humidity_layout.addWidget(QtWidgets.QLabel("온도값 (°C):"))
        humidity_layout.addWidget(self.label_temperature_humidity)
        humidity_group.setLayout(humidity_layout)
        main_layout.addWidget(humidity_group)

        # 계산된 값 그룹 박스
        calculation_group = QtWidgets.QGroupBox("계산된 값")
        calculation_layout = QHBoxLayout()
        self.label_qnh = ClickableLabel(str(self.latest_data['QNH']))
        self.label_qnh.setObjectName("qnhLabel")
        self.label_qfe = ClickableLabel(str(self.latest_data['QFE']))
        self.label_qfe.setObjectName("qfeLabel")
        self.label_qff = ClickableLabel(str(self.latest_data['QFF']))
        self.label_qff.setObjectName("qffLabel")
        calculation_layout.addWidget(QtWidgets.QLabel("QNH:"))
        calculation_layout.addWidget(self.label_qnh)
        calculation_layout.addWidget(QtWidgets.QLabel("QFE:"))
        calculation_layout.addWidget(self.label_qfe)
        calculation_layout.addWidget(QtWidgets.QLabel("QFF:"))
        calculation_layout.addWidget(self.label_qff)
        calculation_group.setLayout(calculation_layout)
        main_layout.addWidget(calculation_group)

        self.setCentralWidget(central_widget)

        # 상태바 추가
        self.status_bar = self.statusBar()
        self.time_label = QLabel()
        self.company_label = QLabel("에스아이테크")
        self.status_bar.addWidget(self.time_label, 1)  # 왼쪽 정렬
        self.status_bar.addPermanentWidget(self.company_label)  # 오른쪽 정렬

        self.update_status_bar_time()

        # 상태바 시간 업데이트 타이머 설정
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self.update_status_bar_time)
        self.time_update_timer.start(1000)  # 1초마다 시간 업데이트

        # 창 크기 조정
        self.adjustSize()
        self.show()

        # 폰트 크기 초기 조절
        self.adjust_font_sizes()

        # 클릭 이벤트 연결
        self.label_pressure.clicked.connect(lambda: self.show_data_selection_window('pressure'))
        self.label_temperature_barometer.clicked.connect(lambda: self.show_data_selection_window('temperature_barometer'))
        self.label_humidity.clicked.connect(lambda: self.show_data_selection_window('humidity'))
        self.label_temperature_humidity.clicked.connect(lambda: self.show_data_selection_window('temperature_humidity'))
        self.label_qnh.clicked.connect(lambda: self.show_data_selection_window('QNH'))
        self.label_qfe.clicked.connect(lambda: self.show_data_selection_window('QFE'))
        self.label_qff.clicked.connect(lambda: self.show_data_selection_window('QFF'))

    def update_status_bar_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def update_display(self):
        try:
            data_updated = False
            while not self.data_queue.empty():
                data = self.data_queue.get()
                if data['sensor'] == '기압계':
                    self.latest_data['pressure'] = data.get('pressure', 'N/A')
                    self.latest_data['temperature_barometer'] = data.get('temperature', 'N/A')
                    data_updated = True
                elif data['sensor'] == '습도계':
                    self.latest_data['temperature_humidity'] = data.get('temperature', 'N/A')
                    self.latest_data['humidity'] = data.get('humidity', 'N/A')
                    data_updated = True
                elif data['sensor'] == '계산값':
                    self.latest_data['QNH'] = data.get('QNH', 'N/A')
                    self.latest_data['QFE'] = data.get('QFE', 'N/A')
                    self.latest_data['QFF'] = data.get('QFF', 'N/A')
                    data_updated = True

            if data_updated:
                # 라벨 업데이트
                self.label_pressure.setText(str(self.latest_data['pressure']))
                self.label_temperature_barometer.setText(str(self.latest_data['temperature_barometer']))
                self.label_temperature_humidity.setText(str(self.latest_data['temperature_humidity']))
                self.label_humidity.setText(str(self.latest_data['humidity']))
                self.label_qnh.setText(str(self.latest_data['QNH']))
                self.label_qfe.setText(str(self.latest_data['QFE']))
                self.label_qff.setText(str(self.latest_data['QFF']))
        except Exception as e:
            logging.error(f"update_display 메서드에서 예외 발생: {e}")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_font_sizes()
        
    def adjust_font_sizes(self):
        # 윈도우의 현재 높이 가져오기
        window_height = self.height()

        # 기준 윈도우 높이에 따른 폰트 크기 계산 (예시: 높이 600 기준)
        base_height = 600
        base_font_size = 20  # 기준 폰트 크기

        # 폰트 크기 비율 계산
        font_scale = window_height / base_height
        new_font_size = max(10, int(base_font_size * font_scale))  # 최소 폰트 크기를 10으로 설정

        # 폰트 크기 비율 조절 (예: 1.1배)
        font_scale *= 3  # 이 값을 변경하여 전체적인 폰트 크기 비율을 조절하세요.
        
        new_font_size = max(10, int(base_font_size * font_scale))  # 최소 폰트 크기를 10으로 설정

        
        self.setStyleSheet(f"""
                QLabel {{
                    font-size: {new_font_size}px;
                }}
                QGroupBox {{
                    font-size: {max(12, int(18 * font_scale))}px;
                    font-weight: bold;
                }}
                QLabel#pressureLabel {{
                    color: blue;
                    font-weight: bold;
                }}
                QLabel#temperatureBarometerLabel {{
                    color: blue;
                    font-weight: bold;
                }}
                QLabel#humidityLabel {{
                    color: blue;
                    font-weight: bold;
                }}
                QLabel#temperatureHumidityLabel {{
                    color: blue;
                    font-weight: bold;
                }}
                QLabel#qnhLabel, QLabel#qfeLabel, QLabel#qffLabel {{
                    color: blue;
                    font-weight: bold;
                }}
            """)


        # 폰트 설정
        font = QFont()
        font.setPointSize(new_font_size)

        # 모든 QLabel에 폰트 적용
        labels = self.findChildren(QLabel)
        for label in labels:
            label.setFont(font)
            

        # 그룹 박스의 폰트 적용
        group_font = QFont()
        group_font.setPointSize(max(12, int(18 * font_scale)))  # 그룹 박스의 폰트 크기 조절

        groups = self.findChildren(QtWidgets.QGroupBox)
        for group in groups:
            group.setFont(group_font)

        # 라벨들의 크기 재조정
        for label in labels:
            label.adjustSize()
            

    def plot_data(self, dialog, start_datetime, end_datetime, range_combo, data_type_checks):
        # 선택된 데이터 타입들
        selected_data_types = [dt for dt, cb in data_type_checks.items() if cb.isChecked()]
        if not selected_data_types:
            QMessageBox.warning(dialog, "경고", "최소 하나의 데이터 타입을 선택해야 합니다.")
            return

        # 범위 옵션에 따른 시간 설정
        range_option = range_combo.currentText()
        try:
            if range_option != "사용자 지정":
                end_time = datetime.now()
                if range_option == "최근 1시간":
                    start_time = end_time - timedelta(hours=1)
                elif range_option == "오늘":
                    start_time = datetime(end_time.year, end_time.month, end_time.day)
                elif range_option == "이번 주":
                    start_time = end_time - timedelta(days=end_time.weekday())
                else:
                    start_time = None
            else:
                start_time = start_datetime.dateTime().toPyDateTime()
                end_time = end_datetime.dateTime().toPyDateTime()
        except ValueError:
            QMessageBox.critical(dialog, "오류", "날짜 또는 시간 형식이 올바르지 않습니다.")
            return

        # 데이터 검색
        data_list = self.ds.search_data(start_time=start_time, end_time=end_time)

        if not data_list:
            QMessageBox.information(dialog, "정보", "선택한 기간에 데이터가 없습니다.")
            return

        # 데이터 시각화
        self.plot_graph(data_list, selected_data_types)

        # 그래프를 그린 후 대화상자 닫기
        dialog.accept()
        
    def plot_graph(self, data_list, selected_data_types):
            # 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'  # 운영체제에 맞게 변경
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

        # 모든 타임스탬프 추출 및 변환
        times = []
        for d in data_list:
            try:
                times.append(datetime.strptime(d['timestamp'], '%Y-%m-%d %H:%M:%S'))
            except ValueError:
                times.append(None)

        # 유효한 데이터 필터링
        valid_indices = [i for i, t in enumerate(times) if t is not None]
        times = [times[i] for i in valid_indices]
        data_list = [data_list[i] for i in valid_indices]

        if not times:
            QMessageBox.information(self, "정보", "유효한 데이터가 없습니다.")
            return

        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()  # 두 번째 y축 생성

        # 데이터 타입에 따른 색상 지정
        colors = {
            'pressure': 'tab:red',
            'temperature_barometer': 'tab:orange',
            'temperature_humidity': 'tab:pink',
            'QNH': 'tab:cyan',
            'QFE': 'tab:olive',
            'QFF': 'tab:brown',
            'humidity': 'tab:green'
        }

        # 첫 번째 y축과 두 번째 y축에 표시할 데이터 타입 구분
        ax1_data_types = []
        ax2_data_types = []

        for data_type in selected_data_types:
            if data_type in ['pressure', 'QNH', 'QFE', 'QFF']:
                ax2_data_types.append(data_type)
            else:
                ax1_data_types.append(data_type)

        # 첫 번째 y축에 데이터 플롯
        for data_type in ax1_data_types:
            values = []
            for d in data_list:
                value = d.get(data_type)
                if value is not None and value != '':
                    try:
                        values.append(float(value))
                    except ValueError:
                        values.append(None)
                else:
                    values.append(None)
            # 유효한 데이터만 선택
            times_filtered = [t for t, v in zip(times, values) if v is not None]
            values_filtered = [v for v in values if v is not None]
            if times_filtered and values_filtered:
                ax1.plot(times_filtered, values_filtered, label=data_type, color=colors.get(data_type, 'black'))

        ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
        if ax1_data_types:
            ax1.set_ylabel('온도 및 습도', color='tab:blue')
            ax1.tick_params(axis='y', labelcolor='tab:blue')

        # 두 번째 y축에 데이터 플롯
        for data_type in ax2_data_types:
            values = []
            for d in data_list:
                value = d.get(data_type)
                if value is not None and value != '':
                    try:
                        values.append(float(value))
                    except ValueError:
                        values.append(None)
                else:
                    values.append(None)
            # 유효한 데이터만 선택
            times_filtered = [t for t, v in zip(times, values) if v is not None]
            values_filtered = [v for v in values if v is not None]
            if times_filtered and values_filtered:
                ax2.plot(times_filtered, values_filtered, label=data_type, linestyle='--', color=colors.get(data_type, 'black'))

        ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
        if ax2_data_types:
            ax2.set_ylabel('압력 (hPa)', color='tab:red')
            ax2.tick_params(axis='y', labelcolor='tab:red')

        # 축 레이블 및 제목 설정
        ax1.set_xlabel('시간')
        plt.title('데이터 시각화')

        # X축 날짜 포맷팅
        fig.autofmt_xdate()

        # 범례 설정
        lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        plt.legend(lines, labels, loc='upper right')

        plt.tight_layout()
        plt.show()
        
    def on_range_changed(self, index, start_datetime, end_datetime, range_combo):
        if range_combo.currentText() != "사용자 지정":
            start_datetime.setEnabled(False)
            end_datetime.setEnabled(False)
        else:
            start_datetime.setEnabled(True)
            end_datetime.setEnabled(True)
            
    def handle_data(self):
        while True:
            try:
                if not self.data_queue.empty():
                    data = self.data_queue.get()
                    # 계산된 데이터인 경우에만 업데이트
                    if data.get('sensor') == '계산값':
                        # 시그널을 통해 메인 스레드로 데이터 전달
                        self.data_updated.emit(data)
            except Exception as e:
                print(f"데이터 처리 중 오류 발생: {e}")
            time.sleep(0.1)

    @QtCore.pyqtSlot(dict)
    def handle_data_updated(self, data):
        # 최신 데이터 업데이트
        for key in self.latest_data:
            value = data.get(key)
            if value is not None:
                self.latest_data[key] = str(value)
        self.refresh_ui()

    def refresh_ui(self):
        # 최신 데이터로 라벨 업데이트
        self.label_pressure.setText(self.latest_data['pressure'])
        self.label_temperature_barometer.setText(self.latest_data['temperature_barometer'])
        self.label_humidity.setText(self.latest_data['humidity'])
        self.label_temperature_humidity.setText(self.latest_data['temperature_humidity'])
        self.label_qnh.setText(self.latest_data['QNH'])
        self.label_qfe.setText(self.latest_data['QFE'])
        self.label_qff.setText(self.latest_data['QFF'])

    def closeEvent(self, event):
        # 창 닫힘 시 이벤트 처리
        event.accept()

    def show_data_selection_window(self, data_type):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"{data_type} 데이터 조회 및 시각화")

        layout = QtWidgets.QVBoxLayout()

        # 날짜 및 시간 선택 위젯
        date_time_layout = QHBoxLayout()
        start_label = QLabel("시작 시간:")
        start_datetime = QDateTimeEdit(QtCore.QDateTime.currentDateTime().addDays(-1))
        start_datetime.setCalendarPopup(True)
        end_label = QLabel("종료 시간:")
        end_datetime = QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        end_datetime.setCalendarPopup(True)
        date_time_layout.addWidget(start_label)
        date_time_layout.addWidget(start_datetime)
        date_time_layout.addWidget(end_label)
        date_time_layout.addWidget(end_datetime)
        layout.addLayout(date_time_layout)

        # 검색 범위 옵션
        range_layout = QHBoxLayout()
        range_label = QLabel("검색 범위:")
        range_combo = QComboBox()
        range_combo.addItems(["사용자 지정", "최근 1시간", "오늘", "이번 주"])
        range_combo.currentIndexChanged.connect(lambda index: self.on_range_changed(index, start_datetime, end_datetime, range_combo))
        range_layout.addWidget(range_label)
        range_layout.addWidget(range_combo)
        layout.addLayout(range_layout)

        # 데이터 타입 선택 (체크박스)
        data_types_layout = QVBoxLayout()
        data_types_label = QLabel("데이터 타입:")
        data_types_layout.addWidget(data_types_label)
        data_type_checks = {}
        data_types = ['pressure', 'temperature_barometer', 'temperature_humidity', 'humidity', 'QNH', 'QFE', 'QFF']
        for dt in data_types:
            checkbox = QCheckBox(dt)
            # 클릭한 데이터 타입은 기본으로 선택
            if dt == data_type:
                checkbox.setChecked(True)
            data_types_layout.addWidget(checkbox)
            data_type_checks[dt] = checkbox
        layout.addLayout(data_types_layout)

        # 시각화 버튼
        plot_button = QPushButton("시각화")
        plot_button.clicked.connect(lambda: self.plot_data(dialog, start_datetime, end_datetime, range_combo, data_type_checks))
        layout.addWidget(plot_button)

        dialog.setLayout(layout)
        dialog.exec_()

