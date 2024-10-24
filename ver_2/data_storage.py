# data_storage.py

import csv
import os
import logging
from datetime import datetime

class DataStorage:
    def __init__(self, base_dir='C:\\Sitech'):
        self.base_dir = base_dir
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.ensure_directory()
        self.create_csv_file()

    def ensure_directory(self):
        data_base_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(data_base_dir, exist_ok=True)
        date_dir = os.path.join(data_base_dir, self.current_date)
        os.makedirs(date_dir, exist_ok=True)
        self.data_dir = date_dir
        
    def create_csv_file(self):
        self.filename = os.path.join(self.data_dir, 'sensor_data.csv')
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, mode='w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['timestamp', 'sensor', 'pressure', 'temperature_barometer', 'temperature_humidity', 'humidity', 'QNH', 'QFE', 'QFF']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
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

        if data is None:
            return

        if data.get('sensor') != '계산값':
            return

        try:
            with open(self.filename, mode='a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'sensor', 'pressure', 'temperature_barometer', 'temperature_humidity', 'humidity', 'QNH', 'QFE', 'QFF']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(data)
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
