import csv
import threading
import logging
from datetime import datetime, timedelta
import os

class DataStorage:
    def __init__(self, base_dir=None):
        # 기본 디렉토리 설정
        if base_dir is None:
            self.base_dir = r'C:\Sitech\data'
        else:
            self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        self.lock = threading.Lock()  # 스레드 안전성을 위한 락
        self.current_date = datetime.now().date()  # 현재 날짜를 저장

    def _get_csv_path(self):
        now = datetime.now()
        dir_path = os.path.join(self.base_dir, now.strftime('%Y-%m'))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        csv_filename = now.strftime('%Y-%m-%d') + '.csv'
        csv_path = os.path.join(dir_path, csv_filename)
        return csv_path

    def _initialize_csv_file(self, csv_path):
        if not os.path.exists(csv_path):
            with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                fields = [
                    'timestamp',
                    'sensor',
                    'pressure',
                    'temperature_barometer',
                    'temperature_humidity',
                    'humidity',
                    'QNH',
                    'QFE',
                    'QFF'
                ]
                writer.writerow(fields)  # 필드 헤더 추가

    def save_data(self, data):
        with self.lock:
            # 현재 날짜 확인
            now_date = datetime.now().date()
            if now_date != self.current_date:
                # 날짜가 변경되었을 때 처리
                self.current_date = now_date
                logging.info(f'{now_date}csv 파일이 생성되었습니다.')
                

            csv_path = self._get_csv_path()

            # CSV 파일 초기화
            self._initialize_csv_file(csv_path)

            # 저장할 필드 목록 정의
            fields = [
                'timestamp',
                'sensor',
                'pressure',
                'temperature_barometer',
                'temperature_humidity',
                'humidity',
                'QNH',
                'QFE',
                'QFF'
            ]

            # 저장할 데이터 준비
            row = [data.get(field, '') for field in fields]

            # 데이터 저장
            with open(csv_path, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row)

    def load_data(self, start_time=None, end_time=None):
        data_list = []
        try:
            with self.lock:
                # 시작 날짜와 종료 날짜 계산
                if start_time is None:
                    start_date = datetime.now().date()
                else:
                    start_date = start_time.date()

                if end_time is None:
                    end_date = datetime.now().date()
                else:
                    end_date = end_time.date()

                # 날짜 범위에 해당하는 파일들을 읽음
                delta = end_date - start_date
                for i in range(delta.days + 1):
                    date = start_date + timedelta(days=i)
                    csv_path = os.path.join(
                        self.base_dir,
                        date.strftime('%Y-%m'),
                        f"{date.strftime('%Y-%m-%d')}.csv"
                    )

                    if os.path.exists(csv_path):
                        with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                                if start_time and timestamp < start_time:
                                    continue
                                if end_time and timestamp > end_time:
                                    continue
                                data_list.append(row)
                return data_list
        except Exception as e:
            logging.error(f"데이터 로드 중 오류 발생: {e}")
            return []

    def search_data(self, sensor=None, start_time=None, end_time=None):
        data_list = []
        try:
            with self.lock:
                # 시작 날짜와 종료 날짜 계산
                if start_time is None:
                    start_date = datetime.now().date()
                else:
                    start_date = start_time.date()

                if end_time is None:
                    end_date = datetime.now().date()
                else:
                    end_date = end_time.date()

                # 날짜 범위에 해당하는 파일들을 읽음
                delta = end_date - start_date
                for i in range(delta.days + 1):
                    date = start_date + timedelta(days=i)
                    csv_path = os.path.join(
                        self.base_dir,
                        date.strftime('%Y-%m'),
                        f"{date.strftime('%Y-%m-%d')}.csv"
                    )

                    if os.path.exists(csv_path):
                        with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                if sensor and row['sensor'] != sensor:
                                    continue
                                timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                                if start_time and timestamp < start_time:
                                    continue
                                if end_time and timestamp > end_time:
                                    continue
                                data_list.append(row)
                return data_list
        except Exception as e:
            logging.error(f"데이터 검색 중 오류 발생: {e}")
            return []

    def close(self):
        # CSV 파일은 별도의 연결을 유지하지 않으므로 특별한 종료 작업이 필요하지 않습니다.
        pass
