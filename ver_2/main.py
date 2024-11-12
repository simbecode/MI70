# main.py

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from data_display_gui import DataDisplayGUI
from data_receiver import DataReceiver
from data_storage import DataStorage
from port_settings_gui import PortSettingsGUI
from serial_port_manager import SerialPortManager
from queue import Queue
from custom_timed_rotating_file_handler import CustomTimedRotatingFileHandler


def setup_logging():
    # 로그를 저장할 기본 디렉토리 설정
    log_dir = r'C:\Sitech\logs'  # 로그를 저장할 경로 지정
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 로거 생성
    logger = logging.getLogger()  # 루트 로거를 사용하거나 원하는 이름으로 로거 생성
    logger.setLevel(logging.DEBUG)  # 필요에 따라 로그 레벨 설정

    # 핸들러 생성
    handler = CustomTimedRotatingFileHandler(
        dir_path=log_dir,
        when='midnight',    # 매일 자정마다 롤오버
        interval=1,
        backupCount=30,      # 최근 7개의 로그 파일만 보관 (원하는 값으로 설정)
        encoding='utf-8'
    )

    # 포매터 설정
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)

    # 핸들러를 로거에 추가
    logger.addHandler(handler)

def main():
        # 로그 설정
    setup_logging()

    # 프로그램 초기화
    logging.info("프로그램이 시작되었습니다.")
    
    app = QApplication(sys.argv)

    # 데이터 큐 생성
    data_queue = Queue()
    
    # 기본 데이터 저장 경로 설정
    base_dir = r'C:\Sitech\data'
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # 데이터 저장 객체 생성
    ds = DataStorage(base_dir=base_dir)

    # 포트 설정 GUI 표시
    spm = SerialPortManager()
    port_settings_gui = PortSettingsGUI(spm)
    if port_settings_gui.exec_() == 0:
        print("포트 설정이 취소되었습니다.")
        sys.exit()

    port_settings = port_settings_gui.port_settings
    hs_value = port_settings_gui.hs_value
    hr_value = port_settings_gui.hr_value
    temperature_source = port_settings_gui.temperature_source

    if not port_settings:
        print("포트 설정이 없습니다.")
        sys.exit()

    # 데이터 수신 객체 생성
    data_receiver = DataReceiver(data_queue, port_settings, ds, hs_value, hr_value, temperature_source)
    data_receiver.start()

    # 데이터 표시 GUI 생성
    gui = DataDisplayGUI(data_queue, data_receiver, ds)
    gui.show()

    # 프로그램 종료 시 처리
    def on_exit():
        data_receiver.stop()
        data_receiver.join()
        ds.close()

    app.aboutToQuit.connect(on_exit)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


