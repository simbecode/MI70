# port_settings_gui.py

import sys
import os
import json
import logging
import serial
from PyQt5 import QtWidgets, QtCore
import serial.tools.list_ports
from PyQt5.QtGui import QDoubleValidator

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

        # 온도값 선택 기본값 설정
        self.temperature_source = self.saved_settings.get('temperature_source', 'humidity_sensor')

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

            # 이전 설정 있으면 적용
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

        # 온도값 선택 라디오 버튼 그룹 생성
        temperature_group_box = QtWidgets.QGroupBox("온도값 선택")
        temperature_layout = QtWidgets.QHBoxLayout()

        self.radio_humidity_sensor = QtWidgets.QRadioButton("습도계 온도값 사용")
        self.radio_barometer_sensor = QtWidgets.QRadioButton("기압계 온도값 사용")
        self.radio_user_defined = QtWidgets.QRadioButton("온도값 사용")  

        # 사용자 입력 온도값 필드 추가
        self.temperature_input = QtWidgets.QLineEdit()
        self.temperature_input.setPlaceholderText("온도값 입력")
        self.temperature_input.setValidator(QDoubleValidator())  # 숫자만 입력 가능하도록 설정
        self.temperature_input.setEnabled(True)  # 비활성화 상태로 설정

        # 이전 설정 불러오기
        if self.temperature_source == 'humidity_sensor':
            self.radio_humidity_sensor.setChecked(True)
        elif self.temperature_source == 'barometer_sensor':
            self.radio_barometer_sensor.setChecked(True)
        elif isinstance(self.temperature_source, float):
            self.radio_user_defined.setChecked(True)
            self.temperature_input.setText(str(self.temperature_source))


        temperature_layout.addWidget(self.radio_humidity_sensor)
        temperature_layout.addWidget(self.radio_barometer_sensor)
        temperature_layout.addWidget(self.radio_user_defined)  # 사용자 정의 온도값 라디오 버튼 추가
        temperature_layout.addWidget(self.temperature_input)  # 사용자 입력 필드 추가
        temperature_group_box.setLayout(temperature_layout)
        layout.addWidget(temperature_group_box)

        # HS, HR 입력 필드를 그룹으로 묶기
        hs_hr_group_box = QtWidgets.QGroupBox("HS 및 HR 설정")
        hs_hr_layout = QtWidgets.QHBoxLayout()

        # HS 입력 필드 추가
        hs_label = QtWidgets.QLabel("HS 값:")
        self.hs_input = QtWidgets.QLineEdit()
        self.hs_input.setValidator(QDoubleValidator())
        self.hs_input.setText(str(self.hs_value))
        hs_hr_layout.addWidget(hs_label)
        hs_hr_layout.addWidget(self.hs_input)

        # HR 입력 필드 추가
        hr_label = QtWidgets.QLabel("HR 값:")
        self.hr_input = QtWidgets.QLineEdit()
        self.hr_input.setValidator(QDoubleValidator())
        self.hr_input.setText(str(self.hr_value))
        hs_hr_layout.addWidget(hr_label)
        hs_hr_layout.addWidget(self.hr_input)

        hs_hr_group_box.setLayout(hs_hr_layout)
        layout.addWidget(hs_hr_group_box)

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

        # 현재 선택된 온도값 소스 업데이트
        if self.radio_humidity_sensor.isChecked():
            self.temperature_source = 'humidity_sensor'
        elif self.radio_barometer_sensor.isChecked():
            self.temperature_source = 'barometer_sensor'
        elif self.radio_user_defined.isChecked():
            if self.temperature_input.text():
                try:
                    self.temperature_source = float(self.temperature_input.text())
                    logging.info(f"사용자 정의 온도값이 입력되었습니다: {self.temperature_source}")
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "경고", "유효한 숫자를 입력하세요.")
            else:
                self.temperature_source = None

        # HS, HR 값 저장
        try:
            self.hs_value = float(self.hs_input.text())
            self.hr_value = float(self.hr_input.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "경고", "유효한 HS 및 HR 값을 입력하세요.")
            return

        # 설정 저장
        self.save_settings()

        # 기압계에 명령어 'R'을 전송
        try:
            barometer_settings = self.port_settings.get('기압계')
            if barometer_settings:
                # 패리티 변환
                parity_dict = {
                    'None': serial.PARITY_NONE,
                    'Even': serial.PARITY_EVEN,
                    'Odd': serial.PARITY_ODD,
                    'Mark': serial.PARITY_MARK,
                    'Space': serial.PARITY_SPACE
                }
                parity_value = parity_dict.get(barometer_settings['parity'], serial.PARITY_NONE)

                # 스탑 비트 변환
                stop_bits_dict = {
                    1: serial.STOPBITS_ONE,
                    1.5: serial.STOPBITS_ONE_POINT_FIVE,
                    2: serial.STOPBITS_TWO
                }
                stop_bits_value = stop_bits_dict.get(barometer_settings['stop_bits'], serial.STOPBITS_ONE)

                # 시리얼 포트 열기
                ser = serial.Serial(
                    port=barometer_settings['port'],
                    baudrate=barometer_settings['baudrate'],
                    bytesize=barometer_settings['data_bits'],
                    parity=parity_value,
                    stopbits=stop_bits_value,
                    timeout=1
                )

                # 명령어 'R' 전송
                ser.write(b'R\r\n')
                logging.info("기압계에 명령어 'R'을 전송했습니.")
                ser.close()
            else:
                logging.error("기압계 설정을 찾을 수 없습니다.")
        except Exception as e:
            logging.error(f"기압계에 명령어를 전송하는 중 오류 발생: {e}")

        self.accept()

    def save_settings(self):
        settings = {
            'port_settings': self.port_settings,
            'temperature_source': self.temperature_source,
            'hs_value': self.hs_value,
            'hr_value': self.hr_value
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            logging.info("설정이 저장되었습니다.")
        except Exception as e:
            logging.info(f"설정 파일을 저장하는 중 오류 발생: {e}")
            
    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.temperature_source = settings.get('temperature_source', 'humidity_sensor')
                    self.hs_value = settings.get('hs_value', 0.0)
                    self.hr_value = settings.get('hr_value', 0.0)
                    logging.info(f"Loaded HS: {self.hs_value}, HR: {self.hr_value}")  # 디버깅용 출력
                    return settings.get('port_settings', {})
            except Exception as e:
                logging.info(f"설정 파일을 불러오는 중 오류 발생: {e}")
                return {}
        else:
            logging.info("설정 파일이 존재하지 않습니다.")
            return {}
        
    def exec(self):
        result = super().exec_()
        if result == QtWidgets.QDialog.Accepted:
            return self.port_settings
        else:
            return None
