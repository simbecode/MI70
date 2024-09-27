# main.py

import os
import sys
import logging
import time
import threading
import queue
from datetime import datetime
from serial_port_manager import SerialPortManager
from data_receiver import DataReceiver
from data_storage import DataStorage
from port_settings_gui import PortSettingsGUI
from data_display_gui import DataDisplayGUI
from PyQt5 import QtWidgets
from custom_timed_rotating_file_handler import CustomTimedRotatingFileHandler

def main():
    # 로그 저장 디렉토리 설정
    log_base_dir = 'C:\\Sitech\\log'

    # 로그 디렉토리가 없으면 생성
    if not os.path.exists(log_base_dir):
        os.makedirs(log_base_dir)

    # 로그 핸들러 생성
    handler = CustomTimedRotatingFileHandler(
        dir_path=log_base_dir,
        when='midnight',
        interval=1,
        backupCount=7,  # 보관할 백업 파일 개수
        encoding='utf-8'
    )

    # 로그 포맷 설정
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)

    # 루트 로거에 핸들러 추가
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # 콘솔 출력 핸들러 추가 (선택 사항)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logging.info("프로그램이 시작되었습니다.")

    try:
        # 관측 지점의 고도 설정 (예: 50미터)
        elevation = 50  # 필요에 따라 실제 고도로 수정하세요.

        # SerialPortManager 인스턴스 생성
        spm = SerialPortManager()

        # PyQt5 애플리케이션 생성
        app = QtWidgets.QApplication(sys.argv)

        # GUI를 통해 포트 설정 가져오기
        gui = PortSettingsGUI(spm)
        port_settings = gui.show()

        if not port_settings:
            logging.info("프로그램이 종료되었습니다.")
            print("프로그램이 종료되었습니다.")
            sys.exit()

        # 설정된 포트 열기
        spm.open_ports(port_settings)

        # 데이터 큐 생성
        data_queue = queue.Queue()

        # DataReceiver 인스턴스 생성
        dr = DataReceiver(spm, elevation=elevation, data_queue=data_queue)
        dr.start_receiving()

        # DataStorage 인스턴스 생성
        ds = DataStorage(base_dir='C:\\Sitech')

        # 데이터 저장 스레드 시작
        def data_saving_thread():
            while True:
                if not data_queue.empty():
                    data = data_queue.get()
                    # 데이터를 저장
                    ds.save_data(data)
                    # 로그에 데이터 기록
                    logging.debug(f"{data['sensor']}에서 수신된 데이터: {data}")
                time.sleep(0.1)

        saving_thread = threading.Thread(target=data_saving_thread)
        saving_thread.daemon = True
        saving_thread.start()

        # 데이터 표시 GUI 실행
        display_gui = DataDisplayGUI(data_queue)
        sys.exit(app.exec_())

    except Exception as e:
        logging.exception(f"프로그램 실행 중 예외 발생: {e}")
    finally:
        # 리소스 정리
        dr.stop_receiving()
        spm.close_ports()
        logging.info("프로그램이 종료되었습니다.")

if __name__ == "__main__":
    main()
