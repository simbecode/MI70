# port_settings_gui.py

import sys
import os
import json
from PyQt5 import QtWidgets, QtCore
import serial.tools.list_ports

class PortSettingsGUI(QtWidgets.QDialog):
    def __init__(self, spm, config_file=None):
        super().__init__()

        self.spm = spm
        self.port_settings = {}

        # Sitech 폴더 경로 설정
        self.sitech_dir = 'C:\\Sitech'

        # config_file 경로 설정
        if config_file is None:
            self.config_file = os.path.join(self.sitech_dir, 'config.json')
        else:
            self.config_file = config_file

        # Sitech 폴더 생성
        if not os.path.exists(self.sitech_dir):
            os.makedirs(self.sitech_dir)

        # 이전 설정 불러오기
        self.saved_settings = self.load_settings()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("포트 및 통신 설정")

        # 레이아웃 설정
        layout = QtWidgets.QVBoxLayout()

        # 포트 목록 가져오기
        self.spm.scan_ports()
        ports = self.spm.available_ports

        if not ports:
            QtWidgets.QMessageBox.critical(self, "오류", "사용 가능한 COM 포트가 없습니다.")
            self.reject()
            return

        # 센서 목록
        sensors = ['기압계', '습도계']

        # 보드레이트 옵션
        baudrate_options = [4800, 9600, 19200, 38400, 57600, 115200]

        # 패리티 옵션
        parity_options = ['None', 'Even', 'Odd', 'Mark', 'Space']

        # 데이터 비트 옵션
        data_bits_options = [5, 6, 7, 8]

        # 스탑 비트 옵션
        stop_bits_options = [1, 1.5, 2]

        self.widgets = {}

        for sensor in sensors:
            group_box = QtWidgets.QGroupBox(sensor)
            form_layout = QtWidgets.QFormLayout()

            # 포트 선택
            port_combo = QtWidgets.QComboBox()
            port_combo.addItems(ports)
            form_layout.addRow("포트:", port_combo)

            # 보드레이트 선택
            baudrate_combo = QtWidgets.QComboBox()
            baudrate_combo.addItems([str(b) for b in baudrate_options])
            form_layout.addRow("보드레이트:", baudrate_combo)

            # 패리티 선택
            parity_combo = QtWidgets.QComboBox()
            parity_combo.addItems(parity_options)
            form_layout.addRow("패리티:", parity_combo)

            # 데이터 비트 선택
            data_bits_combo = QtWidgets.QComboBox()
            data_bits_combo.addItems([str(db) for db in data_bits_options])
            form_layout.addRow("데이터 비트:", data_bits_combo)

            # 스탑 비트 선택
            stop_bits_combo = QtWidgets.QComboBox()
            stop_bits_combo.addItems([str(sb) for sb in stop_bits_options])
            form_layout.addRow("스탑 비트:", stop_bits_combo)

            # 이전 설정이 있으면 적용
            if sensor in self.saved_settings:
                saved_settings = self.saved_settings[sensor]
                if 'port' in saved_settings and saved_settings['port'] in ports:
                    port_combo.setCurrentText(saved_settings['port'])
                if 'baudrate' in saved_settings:
                    baudrate_combo.setCurrentText(str(saved_settings['baudrate']))
                if 'parity' in saved_settings:
                    parity_combo.setCurrentText(saved_settings['parity'])
                if 'data_bits' in saved_settings:
                    data_bits_combo.setCurrentText(str(saved_settings['data_bits']))
                if 'stop_bits' in saved_settings:
                    stop_bits_combo.setCurrentText(str(saved_settings['stop_bits']))

            group_box.setLayout(form_layout)
            layout.addWidget(group_box)

            self.widgets[sensor] = {
                'port': port_combo,
                'baudrate': baudrate_combo,
                'parity': parity_combo,
                'data_bits': data_bits_combo,
                'stop_bits': stop_bits_combo
            }

        # 실행 버튼
        run_button = QtWidgets.QPushButton("실행")
        run_button.clicked.connect(self.on_run)
        layout.addWidget(run_button)

        self.setLayout(layout)

    def on_run(self):
        for sensor, widgets in self.widgets.items():
            port = widgets['port'].currentText()
            baudrate = int(widgets['baudrate'].currentText())
            parity = widgets['parity'].currentText()
            data_bits = int(widgets['data_bits'].currentText())
            stop_bits = float(widgets['stop_bits'].currentText())

            if not port:
                QtWidgets.QMessageBox.warning(self, "경고", f"{sensor}의 포트를 선택해야 합니다.")
                return

            self.port_settings[sensor] = {
                'port': port,
                'baudrate': baudrate,
                'parity': parity,
                'data_bits': data_bits,
                'stop_bits': stop_bits
            }

        # 설정 저장
        self.save_settings(self.port_settings)

        self.accept()

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings
            except Exception as e:
                print(f"설정 파일을 불러오는 중 오류 발생: {e}")
                return {}
        else:
            return {}

    def save_settings(self, settings):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            print("설정이 저장되었습니다.")
        except Exception as e:
            print(f"설정 파일을 저장하는 중 오류 발생: {e}")

    def show(self):
        result = self.exec_()
        if result == QtWidgets.QDialog.Accepted:
            return self.port_settings
        else:
            return None
