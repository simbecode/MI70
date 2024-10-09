import csv
import os
import math
import serial
import serial.tools.list_ports
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime

class Calculator:
    def __init__(self, elevation):
        self.elevation = elevation  # 관측 지점의 고도(m)
        self.L = 0.0065  # 기온 감율(K/m)
        self.T0 = 288.15  # 표준 온도(K)
        self.g = 9.80665  # 중력 가속도(m/s^2)
        self.R = 287.05  # 기체 상수(J/(kg·K))

    def calculate_qnh(self, pressure, temperature):
        # 온도를 켈빈으로 변환
        temp_k = temperature + 273.15
        exponent = (self.g) / (self.R * self.L)
        factor = 1 - (self.L * self.elevation) / temp_k
        qnh = pressure * (factor ** (-exponent))
        return qnh

    def calculate_qfe(self, pressure):
        # QFE는 스테이션 압력과 동일
        return pressure

    def calculate_qff(self, pressure, temperature, humidity):
        # QFF 계산은 복잡하며, 여기서는 간단히 실제 온도와 습도를 고려하여 계산
        # 실제 계산에는 추가적인 기상 데이터가 필요할 수 있음
        temp_k = temperature + 273.15
        # 수증기 분압 계산
        e = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5)) * (humidity / 100)
        # 습윤 공기의 가상 온도 계산
        virtual_temp = temp_k / (1 - (e / pressure) * (1 - 0.622))
        exponent = (self.g * self.elevation) / (self.R * virtual_temp)
        qff = pressure * math.exp(exponent)
        return qff
    
class DataStorage:
    def __init__(self, filename='sensor_data.csv'):
        self.filename = filename

        # 파일이 없으면 헤더를 작성합니다.
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # 헤더 작성 (필요에 따라 수정)
                writer.writerow(['timestamp', 'sensor', 'pressure', 'temperature', 'humidity', 'QNH', 'QFE', 'QFF'])

    def save_data(self, data):
        # 데이터가 None인 경우 저장하지 않습니다.
        if data is None:
            return

        # 저장할 데이터 준비
        timestamp = data.get('timestamp', '')
        sensor = data.get('sensor', '')
        pressure = data.get('pressure', '')
        temperature = data.get('temperature', '')
        humidity = data.get('humidity', '')
        qnh = data.get('QNH', '')
        qfe = data.get('QFE', '')
        qff = data.get('QFF', '')

        # CSV 파일에 데이터 저장
        with open(self.filename, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, sensor, pressure, temperature, humidity, qnh, qfe, qff])

    def load_data(self):
        # 저장된 데이터를 불러옵니다.
        data_list = []
        if os.path.exists(self.filename):
            with open(self.filename, mode='r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data_list.append(row)
        else:
            print(f"{self.filename} 파일이 존재하지 않습니다.")
        return data_list

    def process_data(self, data_list):
        # 데이터를 가공하거나 추가적인 처리를 수행하는 메서드
        pass  # 필요에 따라 구현하세요.

    def search_data(self, sensor=None, start_time=None, end_time=None):
        # 조건에 맞는 데이터를 검색합니다.
        data_list = self.load_data()
        result = []

        for row in data_list:
            # 타임스탬프를 datetime 객체로 변환
            row_time = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            match = True

            if sensor and row['sensor'] != sensor:
                match = False
            if start_time and row_time < start_time:
                match = False
            if end_time and row_time > end_time:
                match = False

            if match:
                result.append(row)
        return result
    
class SerialPortManager:
    def __init__(self):
        self.available_ports = []
        self.serial_connections = {}

    def scan_ports(self):
        ports = serial.tools.list_ports.comports()
        self.available_ports = [port.device for port in ports]

    def open_ports(self, port_settings):
        for sensor_name, settings in port_settings.items():
            port_name = settings['port']
            baudrate = settings['baudrate']
            try:
                ser = serial.Serial(port=port_name, baudrate=baudrate, timeout=1)
                self.serial_connections[sensor_name] = ser
                print(f"{sensor_name} ({port_name}) 열림. 보드레이트: {baudrate}")
            except serial.SerialException as e:
                print(f"{sensor_name} ({port_name}) 열기에 실패했습니다: {e}")

    def close_ports(self):
        for sensor_name, ser in self.serial_connections.items():
            ser.close()
            print(f"{sensor_name} 닫힘.")
        self.serial_connections.clear()

class DataReceiver:
    def __init__(self, serial_port_manager, elevation=0):
        self.spm = serial_port_manager
        self.receiving = False
        self.receive_thread = None
        self.data_queue = queue.Queue()
        self.calculator = Calculator(elevation)

    def start_receiving(self):
        self.receiving = True
        self.receive_thread = threading.Thread(target=self._receive_data)
        self.receive_thread.start()

    def _receive_data(self):
        while self.receiving:
            for sensor_name, ser in self.spm.serial_connections.items():
                if ser.in_waiting > 0:
                    raw_bytes = ser.readline()
                    # 원본 데이터 로그 저장
                    with open(f'raw_data_{sensor_name}.log', 'ab') as f:
                        f.write(raw_bytes + b'\n')
                    try:
                        raw_data = raw_bytes.decode('ascii', errors='ignore').strip()
                        if not raw_data:
                            continue  # 빈 데이터는 무시
                        parsed_data = self.parse_data(raw_data, sensor_name)
                        if parsed_data is not None:
                            parsed_data['sensor'] = sensor_name

                            # 계산 추가
                            if sensor_name == '습도계':
                                self.latest_temperature = parsed_data.get('temperature')
                                self.latest_humidity = parsed_data.get('humidity')
                            elif sensor_name == '기압계':
                                self.latest_pressure = parsed_data.get('pressure')

                            # 모든 센서 데이터가 수집되었을 때 계산 수행
                            if hasattr(self, 'latest_pressure') and hasattr(self, 'latest_temperature') and hasattr(self, 'latest_humidity'):
                                qnh = self.calculator.calculate_qnh(self.latest_pressure, self.latest_temperature)
                                qfe = self.calculator.calculate_qfe(self.latest_pressure)
                                qff = self.calculator.calculate_qff(self.latest_pressure, self.latest_temperature, self.latest_humidity)
                                parsed_data['QNH'] = qnh
                                parsed_data['QFE'] = qfe
                                parsed_data['QFF'] = qff

                                # 계산된 데이터를 큐에 추가
                                self.data_queue.put(parsed_data)
                                print(f"{sensor_name} 에서 파싱된 데이터: {parsed_data}")

                                # 최신 데이터 초기화
                                del self.latest_pressure
                                del self.latest_temperature
                                del self.latest_humidity
                        else:
                            print(f"{sensor_name}에서 파싱된 데이터가 None입니다.")
                    except Exception as e:
                        print(f"{sensor_name} 데이터 처리 오류: {e}. 수신된 데이터: {raw_data}")
            time.sleep(0.1)

    def stop_receiving(self):
        self.receiving = False
        if self.receive_thread is not None:
            self.receive_thread.join()
            self.receive_thread = None

    def parse_data(self, raw_data, sensor_name):
        try:
            if not raw_data:
                return None

            if sensor_name == '습도계':
                # 습도계 데이터 파싱
                raw_data = raw_data.replace('\n', '').replace('\r', '')
                data_parts = raw_data.split(',')

                if len(data_parts) >= 5:
                    # 온도와 습도 추출
                    temperature_str = data_parts[2].strip()
                    humidity_str = data_parts[4].strip()

                    # 단위를 제거하고 숫자만 추출
                    temperature = float(temperature_str.replace("'C", '').replace("'", "").strip())
                    humidity = float(humidity_str)

                    # 현재 시간을 사람이 읽을 수 있는 형식으로 변환
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    parsed_data = {
                        'temperature': temperature,
                        'humidity': humidity,
                        'timestamp': timestamp
                    }
                    return parsed_data
                else:
                    print(f"데이터 부족: {raw_data}")
                    return None

            elif sensor_name == '기압계':
                # 기압계 데이터 파싱
                pressure = float(raw_data.strip())

                # 데이터 유효성 검사
                if pressure < 800 or pressure > 1100:
                    print(f"압력 값 이상: {pressure}")
                    return None

                # 현재 시간을 사람이 읽을 수 있는 형식으로 변환
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                parsed_data = {
                    'pressure': pressure,
                    'timestamp': timestamp
                }
                return parsed_data

            else:
                print(f"알 수 없는 센서: {sensor_name}")
                return None

        except ValueError as e:
            print(f"{sensor_name} 데이터 변환 오류: {e}. 원본 데이터: {raw_data}")
            return None
        
class PortSettingsGUI:
    def __init__(self, spm):
        self.spm = spm
        self.port_settings = {}

        self.root = tk.Tk()
        self.root.title("포트 및 보드레이트 설정")

        # 프레임 생성
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))

        # 포트 목록 가져오기
        self.spm.scan_ports()
        ports = self.spm.available_ports

        if not ports:
            messagebox.showerror("오류", "사용 가능한 COM 포트가 없습니다.")
            self.root.destroy()
            return

        # 센서 목록
        sensors = ['기압계', '습도계']

        # 보드레이트 옵션
        baudrate_options = [9600, 19200]

        self.port_vars = {}
        self.baudrate_vars = {}

        for idx, sensor in enumerate(sensors):
            ttk.Label(mainframe, text=sensor).grid(row=idx, column=0, sticky=tk.W)

            port_var = tk.StringVar()
            port_menu = ttk.Combobox(mainframe, textvariable=port_var, values=ports, state="readonly")
            port_menu.grid(row=idx, column=1)
            self.port_vars[sensor] = port_var

            baudrate_var = tk.IntVar(value=9600)
            baudrate_menu = ttk.Combobox(mainframe, textvariable=baudrate_var, values=baudrate_options, state="readonly")
            baudrate_menu.grid(row=idx, column=2)
            self.baudrate_vars[sensor] = baudrate_var

        # 실행 버튼
        run_button = ttk.Button(mainframe, text="실행", command=self.on_run)
        run_button.grid(row=len(sensors), column=0, columnspan=3)

    def on_run(self):
        for sensor in self.port_vars:
            port = self.port_vars[sensor].get()
            baudrate = self.baudrate_vars[sensor].get()
            if not port:
                messagebox.showwarning("경고", f"{sensor}의 포트를 선택해야 합니다.")
                return
            self.port_settings[sensor] = {'port': port, 'baudrate': baudrate}

        self.root.destroy()

    def show(self):
        self.root.mainloop()
        return self.port_settings

if __name__ == "__main__":
    # 관측 지점의 고도 설정 (예: 50미터)
    elevation = 50  # 필요에 따라 실제 고도로 수정하세요.

    spm = SerialPortManager()

    # GUI를 통해 포트 설정 가져오기
    gui = PortSettingsGUI(spm)
    port_settings = gui.show()

    if not port_settings:
        print("프로그램이 종료되었습니다.")
        exit()

    # 설정된 포트 열기
    spm.open_ports(port_settings)

    # DataReceiver 인스턴스 생성
    dr = DataReceiver(spm, elevation=elevation)
    dr.start_receiving()

    # DataStorage 인스턴스 생성
    ds = DataStorage(filename='sensor_data.csv')

    # 데이터 수신 및 처리
    try:
        while True:
            if not dr.data_queue.empty():
                data = dr.data_queue.get()
                # 데이터를 저장
                ds.save_data(data)
                # 터미널에 데이터 출력
                print(f"{data['sensor']}에서 수신된 데이터: {data}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        # 리소스 정리
        dr.stop_receiving()
        spm.close_ports()

        # 저장된 데이터 불러오기 예시
        data_list = ds.load_data()
        print(f"저장된 데이터 개수: {len(data_list)}")