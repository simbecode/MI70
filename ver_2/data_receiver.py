# data_receiver.py

import os
import re
import json
import threading
import serial
import logging
from datetime import datetime
from calculator import Calculator
from serial_port_manager import SerialPortManager
from calculator import Calculator
import time

class DataReceiver(threading.Thread):
    def __init__(self, data_queue, port_settings, data_storage, hs_value, hr_value, temperature_source):
        super().__init__()
        self.data_queue = data_queue
        self.port_settings = port_settings
        self.data_storage = data_storage
        self.hs_value = hs_value
        self.hr_value = hr_value
        self.temperature_source = temperature_source
        self.user_temperature = temperature_source if isinstance(temperature_source, float) else None  # user_temperature 초기화
        self._stop_event = threading.Event()
        self.serial_ports = {}
        self.latest_data = {}
        self.lock = threading.Lock()
        self.calculator = Calculator(self.hs_value, self.hr_value)
        self.initial_data_received = False
        

        # 시리얼 포트 매니저 초기화
        self.spm = SerialPortManager()
        self.init_serial_ports()
        

    def init_serial_ports(self):
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

                # 스탑 비트 변환
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
                self.serial_ports[sensor_name] = ser
                logging.info(f"{sensor_name}의 시리얼 포트가 열렸습니다: {settings['port']}")
                
                
            except Exception as e:
                logging.error(f"{sensor_name}의 시리얼 포트를 열 수 없습니다: {e}")

    def run(self):
        logging.info("DataReceiver 스레드가 시작되었습니다.")
        time.sleep(1)  # 데이터 수신을 위한 지연 시간 추가
        while not self._stop_event.is_set():
            new_data_received = False  # 새로운 데이터 수신 여부를 확인하는 변수
            barometer_received = False  # 기압계 데이터 수신 여부
            humidity_received = False  # 습도계 데이터 수신 여부

            for sensor_name, ser in self.serial_ports.items():
                # 시리얼 포트가 None이거나 닫혀 있는 경우 재연결 시도
                if ser is None or not ser.is_open:
                    logging.warning(f"{sensor_name}의 시리얼 포트가 닫혀 있습니다. 재연결 시도 중...")
                    self.reconnect_sensor(sensor_name)
                    continue  # 다음 센서로 넘어감

                try:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8').strip()
                        if data:
                            logging.info(f"{sensor_name}에서 데이터 수신: {data}")
                            parsed_data = self.parse_data(sensor_name, data)
                            if parsed_data:
                                with self.lock:
                                    self.latest_data[sensor_name] = parsed_data
                                self.data_queue.put(parsed_data)
                                self.data_storage.save_data(parsed_data)

                                new_data_received = True  # 새로운 데이터가 수신되었음을 표시
                                if sensor_name == '기압계':
                                    barometer_received = True  # 기압계 데이터 수신
                                elif sensor_name == '습도계':
                                    humidity_received = True  # 습도계 데이터 수신

                except serial.SerialException:
                    logging.error(f"{sensor_name}의 시리얼 포트에서 SerialException 발생. 재연결 시도 중...")
                    ser.close()
                    self.serial_ports[sensor_name] = None  # 포트를 None으로 설정하여 재연결 시도 가능하게 함
                    self.reconnect_sensor(sensor_name)  # 재연결 시도
                    self.notify_gui_sensor_disconnected(sensor_name)  # GUI에 연결 해제 알림
                except Exception as e:
                    logging.error(f"{sensor_name}에서 데이터 수신 중 오류 발생: {e}")

            time.sleep(1)  # CPU 사용량을 줄이기 위해 잠시 대기

            # 새로운 데이터가 수신되었거나, 기압계와 습도계 데이터가 모두 수신되었을 때 계산 수행
            if new_data_received or (barometer_received and humidity_received):
                self.generate_calculated_data()

    def parse_data(self, sensor_name, data):
        # print(sensor_name, data)
        try:
            if sensor_name == '기압계':
                # 데이터 문자열을 공백으로 분리
                parts = data.strip().split()
                if len(parts) >= 2:
                    pressure = float(parts[0])
                    temperature = float(parts[1])
                    # print(pressure, temperature)
                    return {
                        'sensor': '기압계',
                        'pressure': pressure,
                        'temperature_barometer': temperature,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    logging.error(f"{sensor_name} 데이터 형식 오류: {data}")
                    self.reconnect_sensor(sensor_name)  # 데이터 형식 오류 시 reconnect_sensor 호출
                    return None
            elif sensor_name == '습도계':
                # 정규 표현식을 사용하여 습도와 온도 값 추출
                humidity_match = re.search(r'RH=\s*([\d\.]+)', data)
                temperature_match = re.search(r'T=\s*([\d\.]+)', data)
                # print(humidity_match, temperature_match)
                if humidity_match and temperature_match:
                    humidity = float(humidity_match.group(1))
                    temperature = float(temperature_match.group(1))
                    return {
                        'sensor': '습도계',
                        'humidity': humidity,
                        'temperature_humidity': temperature,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    logging.error(f"{sensor_name} 데이터 형식 오류: {data}")
                    return None
            else:
                logging.warning(f"알 수 없는 센서 데이터 수신: {sensor_name}")
                return None
        except Exception as e:
            logging.error(f"{sensor_name} 데이터 파싱 중 오류 발생: {e}")
            return None

    def generate_calculated_data(self):
        with self.lock:
            barometer_data = self.latest_data.get('기압계')
            humidity_data = self.latest_data.get('습도계')

        if barometer_data:
            try:
                pressure = barometer_data.get('pressure')
                temperature_barometer = barometer_data.get('temperature_barometer')

                # 온도값 결정
                if self.temperature_source == 'barometer_sensor':
                    temperature = temperature_barometer
                elif self.temperature_source == 'humidity_sensor':
                    temperature = humidity_data.get('temperature_humidity')
                else:
                    temperature = self.user_temperature

                # 계산 수행
                qnh, qfe, qff = self.calculator.calculate(pressure, temperature)

                calculated_data = {
                    'sensor': '계산값',
                    'pressure': pressure,
                    'temperature_barometer': temperature_barometer,
                    'temperature_humidity': humidity_data.get('temperature_humidity') if humidity_data else None,
                    'temperature': temperature,  # 계산에 사용된 온도값
                    'QNH': qnh,
                    'QFE': qfe,
                    'QFF': qff,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                self.data_queue.put(calculated_data)
                self.data_storage.save_data(calculated_data)
                
            except Exception as e:
                logging.error(f"계산 중 오류 발생: {e}")
        else:
            logging.warning("기압계 데이터가 없어 계산을 수행할 수 없습니다.")
            
    def stop(self):
        self._stop_event.set()
        # 시리얼 포트 닫기
        for sensor_name, ser in self.serial_ports.items():
            try:
                ser.close()
                logging.info(f"{sensor_name}의 시리얼 포트를 닫았습니다.")
            except Exception as e:
                logging.error(f"{sensor_name}의 시리얼 포트를 닫는 중 오류 발생: {e}")

    def reconnect_sensor(self, sensor_name):
        """센서 재연결 및 필요한 경우 명령어 전송"""
        settings = self.port_settings.get(sensor_name)
        if settings:
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

                # 스탑 비트 변환
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
                self.serial_ports[sensor_name] = ser
                logging.info(f"{sensor_name}의 시리얼 포트가 재연결되었습니다: {settings['port']}")

                # 기압계일 때만 'R' 명령어 전송
                if sensor_name == '기압계':
                    ser.write(b'R\r\n')  # 아스키로 전송
                    logging.info(f"{sensor_name}에 명령어 'R'을 전송하였습니다.")

            except Exception as e:
                logging.error(f"{sensor_name}의 시리얼 포트를 열거나 명령어 전송 중 오류 발생: {e}")
                self.serial_ports[sensor_name] = None  # 재연결 실패 시 포트를 None으로 설정
                time.sleep(5)  # 재연결 시도 간격을 두기 위해 잠시 대기
    def notify_gui_sensor_disconnected(self, sensor_name):
        """GUI에 센서 연결 해제 알림"""
        # 이 메서드는 GUI에 연결 해제 알림을 보냅니다.
        # 예를 들어, 데이터 큐에 특정 메시지를 추가하거나, GUI 객체에 직접 접근하여 색상을 변경할 수 있습니다.
        self.data_queue.put({'sensor': sensor_name, 'status': 'disconnected'})

    def close_sensor_port(self, sensor_name):
        """지정된 센서의 시리얼 포트를 닫습니다."""
        ser = self.serial_ports.get(sensor_name)
        if ser and ser.is_open:
            try:
                ser.close()
                self.serial_ports[sensor_name] = None  # 포트를 None으로 설정하여 재연결 시도 가능하게 함
                logging.info(f"{sensor_name}의 시리얼 포트를 닫았습니다.")
            except Exception as e:
                logging.error(f"{sensor_name}의 시리얼 포트를 닫는 중 오류 발생: {e}") 
                
                
                