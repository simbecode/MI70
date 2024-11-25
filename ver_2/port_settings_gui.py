import os
import sys
import json
import logging
import time
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QDoubleValidator, QIntValidator
import serial
import serial.tools.list_ports
from password_dialog import PasswordDialog  # PasswordDialog 가져옵니다.

class PortSettingsGUI(QtWidgets.QDialog):
    def __init__(self, spm, config_file=None):
        super().__init__()

        self.spm = spm
        self.port_settings = {}
        self.saved_settings = {}
        self.temperature_source = 'humidity_sensor'
        self.hs_value = 1.0
        self.hr_value = 1.0
        self.qnh_unit = 'hPa'
        self.qfe_unit = 'hPa'
        self.qff_unit = 'hPa'
        self.barometer_interval = 60  # 기압계 interval 기본값
        self.humidity_interval = 60   # 습도계 interval 기본값

        # 설정 파일 경로 설정
        self.sitech_dir = r'C:\Sitech'  # 설정 파일 디렉토리를 C:\Sitech로 변경
        if not os.path.exists(self.sitech_dir):
            os.makedirs(self.sitech_dir)
        if config_file is None:
            self.config_file = os.path.join(self.sitech_dir, 'settings.json')
        else:
            self.config_file = config_file

        # 설정 불러오기
        self.saved_settings = self.load_settings()

        self.init_ui()

    def init_ui(self):
        # 아이콘 설정 (수정된 부분)
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        
        self.setWindowTitle("설정")
        layout = QtWidgets.QVBoxLayout()

        # 사용 가능한 포트 목록 검색하기
        ports = [port.device for port in serial.tools.list_ports.comports()]
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

        # 스톱 비트 옵션
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

            # 스톱 비트 선택
            stop_bits_combo = QtWidgets.QComboBox()
            stop_bits_combo.addItems([str(sb) for sb in stop_bits_options])
            form_layout.addRow("스톱 비트:", stop_bits_combo)

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

            self.widgets[sensor] = {
                'port': port_combo,
                'baudrate': baudrate_combo,
                'parity': parity_combo,
                'data_bits': data_bits_combo,
                'stop_bits': stop_bits_combo
            }

            group_box.setLayout(form_layout)
            layout.addWidget(group_box)

        # Interval 설정 그룹박스 추가 (수정된 부분)
        interval_group_box = QtWidgets.QGroupBox("Interval 설정")
        interval_layout = QtWidgets.QHBoxLayout()

        # 기압계 Interval 입력 필드 추가
        barometer_interval_label = QtWidgets.QLabel("기압계 Interval (초):")
        self.barometer_interval_input = QtWidgets.QLineEdit()
        self.barometer_interval_input.setValidator(QIntValidator(1, 9999))
        self.barometer_interval_input.setText(str(self.barometer_interval))
        interval_layout.addWidget(barometer_interval_label)
        interval_layout.addWidget(self.barometer_interval_input)

        # 습도계 Interval 입력 필드 추가
        humidity_interval_label = QtWidgets.QLabel("습도계 Interval (초):")
        self.humidity_interval_input = QtWidgets.QLineEdit()
        self.humidity_interval_input.setValidator(QIntValidator(1, 9999))
        self.humidity_interval_input.setText(str(self.humidity_interval))
        interval_layout.addWidget(humidity_interval_label)
        interval_layout.addWidget(self.humidity_interval_input)

        interval_group_box.setLayout(interval_layout)
        layout.addWidget(interval_group_box)

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
        self.temperature_input.setEnabled(False)  # 비활성화 상태로 설정

        # 이전 설정 불러오기
        if self.temperature_source == 'humidity_sensor':
            self.radio_humidity_sensor.setChecked(True)
        elif self.temperature_source == 'barometer_sensor':
            self.radio_barometer_sensor.setChecked(True)
        elif isinstance(self.temperature_source, float):
            self.radio_user_defined.setChecked(True)
            self.temperature_input.setText(str(self.temperature_source))

        # 라디오 버튼의 상태 변경 시 슬롯 연결
        self.radio_humidity_sensor.toggled.connect(self.on_temperature_source_changed)
        self.radio_barometer_sensor.toggled.connect(self.on_temperature_source_changed)
        self.radio_user_defined.toggled.connect(self.on_temperature_source_changed)  # 사용자 정의 온도값 라디오 버튼 연결

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
        self.hs_input.setValidator(QDoubleValidator(0.0001, 9999.0, 4))  # 0보다 큰 승수만 입력 가능
        self.hs_input.setText(str(self.hs_value))
        hs_hr_layout.addWidget(hs_label)
        hs_hr_layout.addWidget(self.hs_input)

        # HR 입력 필드 추가
        hr_label = QtWidgets.QLabel("HR 값:")
        self.hr_input = QtWidgets.QLineEdit()
        self.hr_input.setValidator(QDoubleValidator(0.0001, 9999.0, 4))  # 0보다 큰 승수만 입력 가능
        self.hr_input.setText(str(self.hr_value))
        hs_hr_layout.addWidget(hr_label)
        hs_hr_layout.addWidget(self.hr_input)

        hs_hr_group_box.setLayout(hs_hr_layout)
        layout.addWidget(hs_hr_group_box)

        # 단위 선택 콤보박스 추가
        unit_group_box = QtWidgets.QGroupBox("단위 설정")
        unit_layout = QtWidgets.QHBoxLayout()

        # QNH 단위 선택
        qnh_label = QtWidgets.QLabel("QNH:")
        self.qnh_unit_combo = QtWidgets.QComboBox()
        self.qnh_unit_combo.addItems(['hPa', 'inchHg', 'mb'])
        self.qnh_unit_combo.setCurrentText(self.qnh_unit)
        self.qnh_unit_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)  # 크기 자동 맞춤
        self.qnh_unit_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)  # 최대화
        unit_layout.addWidget(qnh_label)
        unit_layout.addWidget(self.qnh_unit_combo)

        # QFE 단위 선택
        qfe_label = QtWidgets.QLabel("QFE:")
        self.qfe_unit_combo = QtWidgets.QComboBox()
        self.qfe_unit_combo.addItems(['hPa', 'inchHg', 'mb'])
        self.qfe_unit_combo.setCurrentText(self.qfe_unit)
        self.qfe_unit_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)  # 크기 자동 맞춤
        self.qfe_unit_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)  # 최대화
        unit_layout.addWidget(qfe_label)
        unit_layout.addWidget(self.qfe_unit_combo)

        # QFF 단위 선택
        qff_label = QtWidgets.QLabel("QFF:")
        self.qff_unit_combo = QtWidgets.QComboBox()
        self.qff_unit_combo.addItems(['hPa', 'inchHg', 'mb'])
        self.qff_unit_combo.setCurrentText(self.qff_unit)
        self.qff_unit_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)  # 크기 자동 맞춤
        self.qff_unit_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)  # 최대화
        unit_layout.addWidget(qff_label)
        unit_layout.addWidget(self.qff_unit_combo)

        unit_group_box.setLayout(unit_layout)
        layout.addWidget(unit_group_box)

        # 회사 정보 라벨 추가 (수정된 부분)
        company_label = QtWidgets.QLabel("© 2024 에스아이테크. All rights reserved.")
        company_label.setAlignment(QtCore.Qt.AlignCenter)  # 가운데 정렬
        layout.addWidget(company_label)

        # 실행 버튼
        run_button = QtWidgets.QPushButton("실행")
        run_button.clicked.connect(self.on_run)
        layout.addWidget(run_button)

        self.setLayout(layout)

    def on_temperature_source_changed(self):
        if self.radio_humidity_sensor.isChecked():
            self.temperature_source = 'humidity_sensor'
            self.temperature_input.setEnabled(False)
        elif self.radio_barometer_sensor.isChecked():
            self.temperature_source = 'barometer_sensor'
            self.temperature_input.setEnabled(False)
        elif self.radio_user_defined.isChecked():
            self.temperature_input.setEnabled(True)
            if self.temperature_input.text():
                try:
                    self.temperature_source = float(self.temperature_input.text())
                    logging.info(f"사용자 정의 온도값이 입력되었습니다: {self.temperature_source}")
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "경고", "유효한 숫자를 입력하세요.")
            else:
                self.temperature_source = None

    def on_run(self):
        # Interval 값 검증 및 저장 (수정된 부분)
        barometer_interval_text = self.barometer_interval_input.text()
        if not barometer_interval_text.isdigit():
            QtWidgets.QMessageBox.warning(self, "경고", "기압계의 Interval 값은 숫자여야 합니다.")
            return
        barometer_interval = int(barometer_interval_text)
        if barometer_interval <= 0:
            QtWidgets.QMessageBox.warning(self, "경고", "기압계의 Interval 값은 0보다 커야 합니다.")
            return

        humidity_interval_text = self.humidity_interval_input.text()
        if not humidity_interval_text.isdigit():
            QtWidgets.QMessageBox.warning(self, "경고", "습도계의 Interval 값은 숫자여야 합니다.")
            return
        humidity_interval = int(humidity_interval_text)
        if humidity_interval <= 0:
            QtWidgets.QMessageBox.warning(self, "경고", "습도계의 Interval 값은 0보다 커야 합니다.")
            return

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

        # Interval 값을 각 센서 설정에 추가
        if '기압계' in self.port_settings:
            self.port_settings['기압계']['interval'] = barometer_interval
        if '습도계' in self.port_settings:
            self.port_settings['습도계']['interval'] = humidity_interval

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
                    return
            else:
                QtWidgets.QMessageBox.warning(self, "경고", "온도값을 입력하세요.")
                return

        # HS, HR 값 저장 및 검증
        try:
            self.hs_value = float(self.hs_input.text())
            self.hr_value = float(self.hr_input.text())
            if self.hs_value <= 0:
                QtWidgets.QMessageBox.warning(self, "경고", "HS 값은 0보다 커야 합니다.")
                return
            if self.hr_value <= 0:
                QtWidgets.QMessageBox.warning(self, "경고", "HR 값은 0보다 커야 합니다.")
                return
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "경고", "유효한 HS 및 HR 값을 입력하세요.")
            return

        # 단위 선택 값 저장
        self.qnh_unit = self.qnh_unit_combo.currentText()
        self.qfe_unit = self.qfe_unit_combo.currentText()
        self.qff_unit = self.qff_unit_combo.currentText()
        
        for sensor_name, settings in self.port_settings.items():
            try:
                # 패리티 변환
                parity_dict = {
                    'None': serial.PARITY_NONE,
                    'Even': serial.PARITY_EVEN,
                    'Odd': serial.PARITY_ODD,
                    'Mark': serial.PARITY_MARK,
                    'Space': serial.PARITY_SPACE
                }
                parity_value = parity_dict.get(settings['parity'], serial.PARITY_NONE)

                # 스톱 비트 변환
                stop_bits_dict = {
                    1: serial.STOPBITS_ONE,
                    1.5: serial.STOPBITS_ONE_POINT_FIVE,
                    2: serial.STOPBITS_TWO
                }
                stop_bits_value = stop_bits_dict.get(settings['stop_bits'], serial.STOPBITS_ONE)

                # 시리얼 포트 열기
                ser = serial.Serial(
                    port=settings['port'],
                    baudrate=settings['baudrate'],
                    bytesize=settings['data_bits'],
                    parity=parity_value,
                    stopbits=stop_bits_value,
                    timeout=1
                )
                logging.info(f"{sensor_name}의 시리얼 포트가 열렸습니다: {settings['port']}")

                # # interval 값 가져오기
                # interval = settings.get('interval', 60)
                # print(interval)
                # 약간의 지연 추가 (필요한 경우)
                # time.sleep(3)
                
                # 센서에 'INTV {interval}' 명령어 전송
                # command_interval = b'intv ' + str(interval).encode('ascii') + b'\r\n'  # 바이트 배열로 정의
                # ser.write(command_interval)
                # logging.info(f"{sensor_name}에 명령어 '{command_interval.decode('ascii').strip()}'를 전송하였습니다.")

                # 센서에 'R' 명령어 전송 (대문자 'R' 사용)
                ser.write(b'R\r\n')  # 아스키로 전송
                logging.info(f"{sensor_name}에 명령어 'R'을 전송하였습니다.")

                # 시리얼 포트 닫기 (수정된 부분)
                ser.close()
                logging.info(f"{sensor_name}의 시리얼 포트를 닫았습니다.")

            except Exception as e:
                logging.error(f"{sensor_name}의 시리얼 포트를 열거나 명령어 전송 중 오류 발생: {e}")
                QtWidgets.QMessageBox.warning(self, "오류", f"{sensor_name}에 명령어를 전송하는 중 오류 발생:\n{e}")
        

        # 설정 저장
        self.save_settings()

        # 비밀번호 입력 창 표시
        self.show_password_dialog()

    def show_password_dialog(self):
        password_dialog = PasswordDialog(self)
        if password_dialog.exec_() == QtWidgets.QDialog.Accepted:
            # 올바른 비밀번호가 입력된 경우 다이얼로그 닫기
            self.accept()
        else:
            # 비밀번호가 틀린 경우 프로그램 종료 또는 다른 처리
            QtWidgets.QMessageBox.warning(self, "비밀번호 오류", "올바른 비밀번호를 입력해야 합니다.")
            sys.exit()

    def save_settings(self):
        settings = {
            'port_settings': self.port_settings,
            'temperature_source': self.temperature_source,
            'hs_value': self.hs_value,
            'hr_value': self.hr_value,
            'qnh_unit': self.qnh_unit,
            'qfe_unit': self.qfe_unit,
            'qff_unit': self.qff_unit
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            print(f"설정이 저장되었습니다: {self.config_file}")
        except Exception as e:
            print(f"설정 파일을 저장하는 중 오류 발생: {e}")

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.temperature_source = settings.get('temperature_source', 'humidity_sensor')
                    self.hs_value = settings.get('hs_value', 1.0)
                    self.hr_value = settings.get('hr_value', 1.0)
                    self.qnh_unit = settings.get('qnh_unit', 'hPa')
                    self.qfe_unit = settings.get('qfe_unit', 'hPa')
                    self.qff_unit = settings.get('qff_unit', 'hPa')

                    port_settings = settings.get('port_settings', {})

                    # Interval 값 로드 (수정된 부분)
                    if '기압계' in port_settings:
                        self.barometer_interval = port_settings['기압계'].get('interval', 60)
                    else:
                        self.barometer_interval = 60
                    if '습도계' in port_settings:
                        self.humidity_interval = port_settings['습도계'].get('interval', 60)
                    else:
                        self.humidity_interval = 60

                    return port_settings
            except Exception as e:
                print(f"설정 파일을 불러오는 중 오류 발생: {e}")
                logging.error("예외 발생", exc_info=True)
                # 설정 파일을 불러오지 못했을 때 기본값 설정
                self.hs_value = 1.0
                self.hr_value = 1.0
                self.qnh_unit = 'hPa'
                self.qfe_unit = 'hPa'
                self.qff_unit = 'hPa'
                self.barometer_interval = 60
                self.humidity_interval = 60
                return {}
        else:
            print("설정 파일이 존재하지 않습니다.")
            # 설정 파일이 없을 때 기본값 설정
            self.hs_value = 1.0
            self.hr_value = 1.0
            self.qnh_unit = 'hPa'
            self.qfe_unit = 'hPa'
            self.qff_unit = 'hPa'
            self.barometer_interval = 60
            self.humidity_interval = 60
            return {}

    def show(self):
        result = self.exec_()
        if result == QtWidgets.QDialog.Accepted:
            return self.port_settings
        else:
            return None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    spm = None  # 실제 SerialPortManager 객체로 대체해야 합니다.
    gui = PortSettingsGUI(spm)
    if gui.exec_() == QtWidgets.QDialog.Accepted:
        # 프로그램의 메인 로직을 여기에 작성합니다.
        print("프로그램이 실행되었습니다.")
    else:
        print("프로그램이 종료되었습니다.")
    sys.exit()
