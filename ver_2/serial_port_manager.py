# serial_port_manager.py

import logging
import serial
import serial.tools.list_ports

class SerialPortManager:
    def __init__(self):
        self.available_ports = []
        self.serial_connections = {}
        self.port_settings = {}  # 포트 설정 정보를 저장하기 위한 딕셔너리 추가


    def scan_ports(self):
        ports = serial.tools.list_ports.comports()
        self.available_ports = [port.device for port in ports]
        logging.debug(f"사용 가능한 포트: {self.available_ports}")

    def open_ports(self, port_settings):
        self.port_settings = port_settings  # 포트 설정 정보를 저장
        for sensor_name, settings in port_settings.items():
            port_name = settings['port']
            baudrate = settings['baudrate']
            parity = settings.get('parity', 'None')
            data_bits = settings.get('data_bits', 8)
            stop_bits = settings.get('stop_bits', 1)

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

            try:
                ser = serial.Serial(
                    port=port_name,
                    baudrate=baudrate,
                    bytesize=data_bits,
                    parity=parity_value,
                    stopbits=stop_bits_value,
                    timeout=1
                )
                self.serial_connections[sensor_name] = ser
                logging.info(f"{sensor_name} ({port_name}) 열림. 보드레이트: {baudrate}, 패리티: {parity}, 데이터 비트: {data_bits}, 스탑 비트: {stop_bits}")
            except serial.SerialException as e:
                logging.error(f"{sensor_name} ({port_name}) 열기에 실패했습니다: {e}")
                print(f"{sensor_name} ({port_name}) 열기에 실패했습니다: {e}")

    def close_ports(self):
        for sensor_name, ser in self.serial_connections.items():
            ser.close()
            logging.info(f"{sensor_name} 닫힘.")
        self.serial_connections.clear()
