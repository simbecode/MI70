# custom_timed_rotating_file_handler.py

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import time

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, dir_path, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None):
        self.dir_path = dir_path
        self.suffix = "%Y-%m-%d"
        self.month_format = "%Y-%m"
        # 초기 로그 파일명 설정
        self.current_time = int(time.time())
        self.baseFilename = self._compute_fn()
        super().__init__(self.baseFilename, when, interval, backupCount, encoding, delay, utc, atTime)
    
    def _compute_fn(self):
        date_str = time.strftime(self.suffix, time.localtime(self.current_time))
        month_str = time.strftime(self.month_format, time.localtime(self.current_time))
        # 월별 디렉토리 생성
        month_dir = os.path.join(self.dir_path, month_str)
        if not os.path.exists(month_dir):
            os.makedirs(month_dir)
        filename = os.path.join(month_dir, f"{date_str}.log")
        return filename

    def doRollover(self):
        self.current_time = self.rolloverAt
        self.stream.close()
        # 현재 시간 갱신
        self.baseFilename = self._compute_fn()
        self.mode = 'a'
        self.stream = self._open()
        # 다음 롤오버 시간 계산
        self.rolloverAt = self.computeRollover(self.current_time)
