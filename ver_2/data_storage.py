# data_storage.py

import csv
import os
import logging
from datetime import datetime

class DataStorage:
    def __init__(self, base_dir='C:\\Sitech'):
        self.base_dir = base_dir
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.current_file = None
        self.ensure_directory()
        self.create_csv_file()

    def ensure_directory(self):
        # 데이터 디렉토리 생성
        data_base_dir = os.path.join(self.base_dir, 'data')
        if not os.path.exists(data_base_dir):
            os.makedirs(data_base_dir)
            logging.info(f"데이터 기본 디렉토리 생성: {data_base_dir}")

        # 날짜별 데이터 디렉토리 생성
        date_dir = os.path.join(data_base_dir, self.current_date)
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
            logging.info(f"날짜별 데이터 디렉토리 생성: {date_dir}")
        self.data_dir = date_dir

    def create_csv_file(self):
        self.filename = os.path.join(self.data_dir, 'sensor_data.csv')
        # 파일이 없으면 헤더를 작성합니다.
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, mode='w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # 헤더 작성
                    writer.writerow(['timestamp', 'sensor', 'pressure', 'temperature_barometer', 'temperature_humidity', 'humidity', 'QNH', 'QFE', 'QFF'])
                logging.info(f"CSV 파일 생성: {self.filename}")
            except Exception as e:
                logging.error(f"CSV 파일 생성 중 오류 발생: {e}")
                
    def save_data(self, data):
        # 날짜가 변경되었는지 확인
        current_date = datetime.now().strftime('%Y-%m-%d')
        if current_date != self.current_date:
            self.current_date = current_date
            self.ensure_directory()
            self.create_csv_file()

        # 데이터가 None인 경우 저장하지 않습니다.
        if data is None:
            return

        # 계산된 데이터만 저장
        if data.get('sensor') != '계산값':
            return

        # 저장할 데이터 준비
        timestamp = data.get('timestamp', '')
        pressure = data.get('pressure', '')
        temperature_barometer = data.get('temperature_barometer', '')
        temperature_humidity = data.get('temperature_humidity', '')
        temperature = data.get('temperature', '')  # 선택된 온도값
        humidity = data.get('humidity', '')
        qnh = data.get('QNH', '')
        qfe = data.get('QFE', '')
        qff = data.get('QFF', '')

        # CSV 파일에 데이터 저장
        try:
                with open(self.filename, mode='a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        timestamp,
                        data.get('sensor', ''),
                        pressure,
                        temperature_barometer,
                        temperature_humidity,
                        temperature,
                        humidity,
                        qnh,
                        qfe,
                        qff
                    ])
                logging.debug(f"데이터 저장: {data}")
        except Exception as e:
            logging.error(f"데이터 저장 중 오류 발생: {e}")
            
            
    def load_data(self, start_time=None, end_time=None):
        # 전체 데이터 디렉토리에서 데이터 로드
        data_list = []
        data_base_dir = os.path.join(self.base_dir, 'data')
        for root, dirs, files in os.walk(data_base_dir):
            for file in files:
                if file == 'sensor_data.csv':
                    file_path = os.path.join(root, file)
                    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            # 타임스탬프 필터링
                            try:
                                row_time = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                                if start_time and row_time < start_time:
                                    continue
                                if end_time and row_time > end_time:
                                    continue
                                data_list.append(row)
                            except ValueError as e:
                                logging.error(f"타임스탬프 파싱 오류: {e}. 원본 데이터: {row}")
        return data_list

    def process_data(self, data_list):
        # 데이터를 가공하거나 추가적인 처리를 수행하는 메서드
        pass  # 필요에 따라 구현하세요.

    def search_data(self, sensor=None, start_time=None, end_time=None):
        # 조건에 맞는 데이터를 검색합니다.
        data_list = self.load_data(start_time=start_time, end_time=end_time)
        result = []

        for row in data_list:
            match = True

            if sensor and row['sensor'] != sensor:
                match = False

            if match:
                result.append(row)
        return result
