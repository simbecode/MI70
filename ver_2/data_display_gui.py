# data_display_gui.py

import sys
import os
import threading
import time
from datetime import datetime, timedelta
from clickable_label import ClickableLabel
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from data_storage import DataStorage
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QMessageBox, QDateTimeEdit
)

class DataDisplayGUI(QtWidgets.QWidget):
    # 데이터 업데이트를 위한 시그널 정의
    data_updated = pyqtSignal(dict)

    def __init__(self, data_queue):
        super().__init__()

        self.data_queue = data_queue
        self.ds = DataStorage(base_dir='C:\\Sitech')

        # 최신 데이터 저장용 딕셔너리
        self.latest_data = {
            'pressure': '-',
            'temperature_barometer': '-',
            'humidity': '-',
            'temperature_humidity': '-',
            'QNH': '-',
            'QFE': '-',
            'QFF': '-'
        }

        self.init_ui()

        # 시그널과 슬롯 연결
        self.data_updated.connect(self.handle_data_updated)

        # 데이터 처리 스레드 시작
        self.data_thread = threading.Thread(target=self.handle_data)
        self.data_thread.daemon = True
        self.data_thread.start()

    def init_ui(self):
        self.setWindowTitle("실시간 데이터 표시")

        main_layout = QVBoxLayout()

        # 스타일 시트 설정
        self.setStyleSheet("""
            QLabel {
                font-size: 16px;
            }
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
            }
        """)

        # 기압계 그룹 박스
        barometer_group = QtWidgets.QGroupBox("기압계")
        barometer_layout = QHBoxLayout()
        self.label_pressure = ClickableLabel(self.latest_data['pressure'])
        self.label_pressure.setStyleSheet("font-size: 20px; color: blue; font-weight: bold;")
        self.label_temperature_barometer = ClickableLabel(self.latest_data['temperature_barometer'])
        self.label_temperature_barometer.setStyleSheet("font-size: 20px; color: blue; font-weight: bold;")
        barometer_layout.addWidget(QtWidgets.QLabel("기압값 (hPa):"))
        barometer_layout.addWidget(self.label_pressure)
        barometer_layout.addWidget(QtWidgets.QLabel("온도값 (°C):"))
        barometer_layout.addWidget(self.label_temperature_barometer)
        barometer_group.setLayout(barometer_layout)
        main_layout.addWidget(barometer_group)

        # 습도계 그룹 박스
        humidity_group = QtWidgets.QGroupBox("습도계")
        humidity_layout = QHBoxLayout()
        self.label_humidity = ClickableLabel(self.latest_data['humidity'])
        self.label_humidity.setStyleSheet("font-size: 20px; color: green; font-weight: bold;")
        self.label_temperature_humidity = ClickableLabel(self.latest_data['temperature_humidity'])
        self.label_temperature_humidity.setStyleSheet("font-size: 20px; color: green; font-weight: bold;")
        humidity_layout.addWidget(QtWidgets.QLabel("습도값 (%):"))
        humidity_layout.addWidget(self.label_humidity)
        humidity_layout.addWidget(QtWidgets.QLabel("온도값 (°C):"))
        humidity_layout.addWidget(self.label_temperature_humidity)
        humidity_group.setLayout(humidity_layout)
        main_layout.addWidget(humidity_group)

        # 계산된 값 그룹 박스
        calculation_group = QtWidgets.QGroupBox("계산된 값")
        calculation_layout = QHBoxLayout()
        self.label_qnh = ClickableLabel(self.latest_data['QNH'])
        self.label_qnh.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        self.label_qfe = ClickableLabel(self.latest_data['QFE'])
        self.label_qfe.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        self.label_qff = ClickableLabel(self.latest_data['QFF'])
        self.label_qff.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        calculation_layout.addWidget(QtWidgets.QLabel("QNH:"))
        calculation_layout.addWidget(self.label_qnh)
        calculation_layout.addWidget(QtWidgets.QLabel("QFE:"))
        calculation_layout.addWidget(self.label_qfe)
        calculation_layout.addWidget(QtWidgets.QLabel("QFF:"))
        calculation_layout.addWidget(self.label_qff)
        calculation_group.setLayout(calculation_layout)
        main_layout.addWidget(calculation_group)

        self.setLayout(main_layout)

        # 창 크기 조정
        self.adjustSize()
        self.show()

        # 클릭 이벤트 연결
        self.label_pressure.clicked.connect(lambda: self.show_data_selection_window('pressure'))
        self.label_temperature_barometer.clicked.connect(lambda: self.show_data_selection_window('temperature_barometer'))
        self.label_humidity.clicked.connect(lambda: self.show_data_selection_window('humidity'))
        self.label_temperature_humidity.clicked.connect(lambda: self.show_data_selection_window('temperature_humidity'))
        self.label_qnh.clicked.connect(lambda: self.show_data_selection_window('QNH'))
        self.label_qfe.clicked.connect(lambda: self.show_data_selection_window('QFE'))
        self.label_qff.clicked.connect(lambda: self.show_data_selection_window('QFF'))
    
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