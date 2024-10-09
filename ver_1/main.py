import sys
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
import os

# 로그 디렉토리 설정
log_dir = os.path.join("C:\\", "SItech", "log", datetime.now().strftime("%Y-%m-%d"))

# 디렉토리가 존재하지 않으면 생성
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로그 파일 경로 설정
log_file = os.path.join(log_dir, datetime.now().strftime("%Y%m%d") + ".txt")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),  # 로그를 날짜별 파일에 저장
        logging.StreamHandler(sys.stdout)  # 로그를 콘솔에 출력
    ]
)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())