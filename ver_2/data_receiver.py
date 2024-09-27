# data_receiver.py

import logging
import threading
import time
import queue
from datetime import datetime
from calculator import Calculator
import os
import re  # 정규표현식 모듈 임포트

class DataReceiver:
    def __init__(self, serial_port_manager, elevation=0, data_queue=None):
        self.spm = serial_port_manager
        self.receiving = False
        self.receive_thread = None
        self.data_queue = data_queue if data_queue else queue.Queue()
        self.calculator = Calculator(elevation)
        # 최신 데이터 저장용 딕셔너리
        self.latest_data = {}

    def start_receiving(self):
        self.receiving = True
        self.receive_thread = threading.Thread(target=self._receive_data)
        self.receive_thread.start()
        logging.info("데이터 수신을 시작합니다.")

    def _receive_data(self):
        while self.receiving:
            for sensor_name, ser in self.spm.serial_connections.items():
                if ser.in_waiting > 0:
                    raw_bytes = ser.readline()
                    try:
                        raw_data = raw_bytes.decode('ascii', errors='ignore').strip()
                        logging.debug(f"{sensor_name}에서 수신된 원본 데이터: {raw_data}")
                        if not raw_data:
                            continue  # 빈 데이터는 무시
                        parsed_data = self.parse_data(raw_data, sensor_name)
                        if parsed_data is not None:
                            parsed_data['sensor'] = sensor_name

                            # 최신 데이터 저장
                            self.latest_data[sensor_name] = parsed_data

                            # 데이터를 큐에 추가
                            self.data_queue.put(parsed_data)
                            logging.debug(f"{sensor_name}에서 파싱된 데이터: {parsed_data}")

                            # 모든 센서 데이터가 수집되었을 때 계산 수행
                            if '기압계' in self.latest_data and '습도계' in self.latest_data:
                                pressure = self.latest_data['기압계'].get('pressure')
                                temperature_barometer = self.latest_data['기압계'].get('temperature')
                                temperature_humidity = self.latest_data['습도계'].get('temperature')
                                humidity = self.latest_data['습도계'].get('humidity')

                                # 온도값 선택 (여기서는 습도계의 온도값 사용)
                                temperature = temperature_humidity

                                if pressure is not None and temperature is not None and humidity is not None:
                                    qnh = self.calculator.calculate_qnh(pressure, temperature)
                                    qfe = self.calculator.calculate_qfe(pressure)
                                    qff = self.calculator.calculate_qff(pressure, temperature, humidity)

                                    # 소수점 둘째 자리까지 표시
                                    calculated_data = {
                                        'sensor': '계산값',
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'pressure': pressure,
                                        'temperature_barometer': temperature_barometer,
                                        'temperature_humidity': temperature_humidity,
                                        'humidity': humidity,
                                        'QNH': round(qnh, 2),
                                        'QFE': round(qfe, 2),
                                        'QFF': round(qff, 2)
                                    }

                                    # 계산된 데이터를 큐에 추가
                                    self.data_queue.put(calculated_data)
                                    logging.info(f"계산된 데이터: {calculated_data}")
                        else:
                            logging.warning(f"{sensor_name}에서 파싱된 데이터가 None입니다.")
                    except Exception as e:
                        logging.error(f"{sensor_name} 데이터 처리 오류: {e}. 수신된 데이터: {raw_bytes}")
            time.sleep(0.1)

    def stop_receiving(self):
        self.receiving = False
        if self.receive_thread is not None:
            self.receive_thread.join()
            self.receive_thread = None
        logging.info("데이터 수신을 종료합니다.")

    def parse_data(self, raw_data, sensor_name):
        try:
            if not raw_data:
                return None

            if sensor_name == '습도계':
                # 원본 데이터 출력
                logging.debug(f"수신된 원본 데이터: {repr(raw_data)}")

                # 제어 문자 제거
                raw_data_cleaned = raw_data.replace('\x02', '').replace('\x03', '').replace('\n', '').replace('\r', '')

                data_parts = raw_data_cleaned.split(',')

                if len(data_parts) >= 3:
                    # 습도 추출
                    humidity_str = data_parts[1].strip()

                    # 공백으로 분리하여 두 번째 값 사용
                    humidity_tokens = humidity_str.split()
                    if len(humidity_tokens) >= 2:
                        humidity_value_str = humidity_tokens[1]
                    else:
                        humidity_value_str = humidity_tokens[0]

                    # 숫자와 소수점만 추출
                    humidity_value_str = re.sub(r'[^0-9.]', '', humidity_value_str)
                    humidity = float(humidity_value_str)

                    # 온도 추출
                    temperature_str = data_parts[2].strip()
                    # 단위를 제거하고 숫자와 소수점, 부호만 추출
                    temperature_str_cleaned = re.sub(r'[^0-9.-]', '', temperature_str)
                    temperature = float(temperature_str_cleaned)

                    # 현재 시간을 사람이 읽을 수 있는 형식으로 변환
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    parsed_data = {
                        'temperature': temperature,
                        'humidity': humidity,
                        'timestamp': timestamp
                    }
                    return parsed_data
                else:
                    logging.error(f"데이터 부족: {raw_data}")
                    return None

            elif sensor_name == '기압계':
                # 기압계 데이터 파싱 ("1005.87 26.75" 형식)
                parts = raw_data.strip().split()
                if len(parts) == 2:
                    pressure_str = parts[0]
                    temperature_str = parts[1]

                    # 압력 추출
                    pressure = float(pressure_str)

                    # 압력 값 검증
                    if pressure < 800 or pressure > 1100:
                        logging.error(f"압력 값 이상: {pressure}")
                        return None

                    # 온도 추출
                    temperature = float(temperature_str)

                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    parsed_data = {
                        'pressure': pressure,
                        'temperature': temperature,
                        'timestamp': timestamp
                    }
                    return parsed_data
                else:
                    logging.error(f"기압계 데이터 형식 오류: {raw_data}")
                    return None

            else:
                logging.error(f"알 수 없는 센서: {sensor_name}")
                return None

        except ValueError as e:
            logging.error(f"{sensor_name} 데이터 변환 오류: {e}. 원본 데이터: {raw_data}")
            return None
