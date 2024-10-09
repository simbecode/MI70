# data_receiver.py

import logging
import threading
import time
import queue
from datetime import datetime
from calculator import Calculator
import os
import re  # 정규표현식 모듈 임포트
import serial

class DataReceiver:
    def __init__(self, serial_port_manager, elevation=0, data_queue=None, data_callback=None, temperature_source='humidity_sensor'):
        self.spm = serial_port_manager
        self.receiving = False
        self.receive_thread = None
        self.data_queue = data_queue if data_queue else queue.Queue()
        self.data_callback = data_callback  # 데이터 콜백 함수
        self.calculator = Calculator(elevation)
        self.temperature_source = temperature_source
        self.latest_data = {}
        self.connection_status = {}
        self.previous_connection_status = {}
        self.last_received_time = {}
        
    def start_receiving(self):
        self.receiving = True
        self.receive_thread = threading.Thread(target=self._receive_data)
        self.receive_thread.start()
        logging.info("데이터 수신을 시작합니다.")
        # 수신 스레드 시작 시 각 센서의 상태 초기화
        for sensor_name in self.spm.serial_connections.keys():
            self.connection_status[sensor_name] = True  # 현재 연결 상태
            self.previous_connection_status[sensor_name] = True  # 이전 연결 상태 초기화
            self.last_received_time[sensor_name] = time.time()

    def _receive_data(self):
        while self.receiving:
            for sensor_name in list(self.spm.serial_connections.keys()):
                ser = self.spm.serial_connections[sensor_name]
                try:
                    if ser.in_waiting > 0:
                        raw_bytes = ser.readline()
                        # 데이터 수신 시간 업데이트
                        self.last_received_time[sensor_name] = time.time()
                        # 연결 상태를 True로 설정
                        self.connection_status[sensor_name] = True
                        # 연결 상태 변경 확인 및 로그 기록
                        if self.previous_connection_status[sensor_name] != self.connection_status[sensor_name]:
                            logging.info(f"{sensor_name}의 연결이 복구되었습니다.")
                            self.previous_connection_status[sensor_name] = self.connection_status[sensor_name]
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

                                # 데이터 콜백 함수 호출 (GUI 업데이트)
                                if self.data_callback:
                                    self.data_callback(parsed_data)

                                logging.debug(f"{sensor_name}에서 파싱된 데이터: {parsed_data}")

                                # 계산 수행 코드...
                                if '기압계' in self.latest_data and '습도계' in self.latest_data:
                                    pressure = self.latest_data['기압계'].get('pressure')
                                    temperature_barometer = self.latest_data['기압계'].get('temperature')
                                    temperature_humidity = self.latest_data['습도계'].get('temperature')
                                    humidity = self.latest_data['습도계'].get('humidity')

                                    # 선택된 온도값 사용
                                    if self.temperature_source == 'humidity_sensor':
                                        temperature = temperature_humidity
                                    else:
                                        temperature = temperature_barometer

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

                                        # 데이터 콜백 함수 호출 (GUI 업데이트)
                                        if self.data_callback:
                                            self.data_callback(calculated_data)

                                        logging.info(f"계산된 데이터: {calculated_data}")
                            else:
                                logging.warning(f"{sensor_name}에서 파싱된 데이터가 None입니다.")
                        except Exception as e:
                            logging.error(f"{sensor_name} 데이터 처리 오류: {e}. 수신된 데이터: {raw_bytes}")
                    else:
                        # 데이터를 수신하지 못한 경우 연결 상태를 확인
                        current_time = time.time()
                        if current_time - self.last_received_time[sensor_name] > 10:  # 임계값 조정 가능
                            self.connection_status[sensor_name] = False
                            # 연결 상태 변경 확인 및 로그 기록
                            if self.previous_connection_status[sensor_name] != self.connection_status[sensor_name]:
                                logging.error(f"{sensor_name}의 연결이 끊어졌습니다.")
                                self.previous_connection_status[sensor_name] = self.connection_status[sensor_name]
                except serial.SerialException as e:
                    logging.error(f"{sensor_name} 시리얼 예외 발생: {e}")
                    self.connection_status[sensor_name] = False  # 포트 연결 끊김
                    # 연결 상태 변경 확인 및 로그 기록
                    if self.previous_connection_status[sensor_name] != self.connection_status[sensor_name]:
                        logging.error(f"{sensor_name}의 연결이 끊어졌습니다.")
                        self.previous_connection_status[sensor_name] = self.connection_status[sensor_name]

                    # 시리얼 포트 재연결 시도
                    self._reconnect_port(sensor_name)
                except Exception as e:
                    logging.error(f"{sensor_name} 데이터 처리 오류: {e}")
                    self.connection_status[sensor_name] = False
                    # 연결 상태 변경 확인 및 로그 기록
                    if self.previous_connection_status[sensor_name] != self.connection_status[sensor_name]:
                        logging.error(f"{sensor_name}의 연결이 끊어졌습니다.")
                        self.previous_connection_status[sensor_name] = self.connection_status[sensor_name]
            time.sleep(0.1)
            
    def _reconnect_port(self, sensor_name):
            # 기존 시리얼 포트 닫기
        try:
            self.spm.serial_connections[sensor_name].close()
            logging.info(f"{sensor_name} 포트를 닫았습니다.")
        except Exception as e:
            logging.error(f"{sensor_name} 포트 닫기 오류: {e}")

        # 일정 시간 대기 후 재연결 시도
        time.sleep(2)  # 재연결 시도 전 대기 시간 (필요에 따라 조정)

        try:
            # 저장된 포트 설정 가져오기
            port_settings = self.spm.port_settings[sensor_name]

            port_name = port_settings['port']
            baudrate = port_settings['baudrate']
            parity = port_settings.get('parity', 'None')
            data_bits = port_settings.get('data_bits', 8)
            stop_bits = port_settings.get('stop_bits', 1)

            # 패리티 변환
            parity_dict = {
                'None': serial.PARITY_NONE,
                'Even': serial.PARITY_EVEN,
                'Odd': serial.PARITY_ODD,
                'Mark': serial.PARITY_MARK,
                'Space': serial.PARITY_SPACE
            }
            parity_value = parity_dict.get(parity, serial.PARITY_NONE)

            # 스탑 비트 변환
            stop_bits_dict = {
                1: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO
            }
            stop_bits_value = stop_bits_dict.get(stop_bits, serial.STOPBITS_ONE)

            # 시리얼 포트 다시 열기
            ser = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=data_bits,
                parity=parity_value,
                stopbits=stop_bits_value,
                timeout=1
            )

            self.spm.serial_connections[sensor_name] = ser
            self.connection_status[sensor_name] = True
            logging.info(f"{sensor_name} 포트에 재연결되었습니다.")
        except Exception as e:
            logging.error(f"{sensor_name} 포트 재연결 실패: {e}")
            self.connection_status[sensor_name] = False
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

                # 데이터 형식: "RH= 38.7 %RH T= 27.1 'C"
                # 공백을 제거하지 않고 전체 문자열에서 필요한 부분을 추출

                # 정규표현식 패턴 정의
                pattern = r"RH=\s*([\d\.]+)\s*%RH\s*T=\s*([\d\.\-]+)\s*'C"

                match = re.search(pattern, raw_data)
                if match:
                    humidity_str = match.group(1)
                    temperature_str = match.group(2)

                    humidity = float(humidity_str)
                    temperature = float(temperature_str)

                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    parsed_data = {
                        'temperature': temperature,
                        'humidity': humidity,
                        'timestamp': timestamp
                    }
                    return parsed_data
                else:
                    logging.error(f"데이터 형식 오류: {raw_data}")
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

