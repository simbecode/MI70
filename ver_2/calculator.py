import math

class Calculator:
    def __init__(self, hs=0.0, hr=0.0):
        self.hs = hs  # HS 값
        self.hr = hr  # HR 값
        print(f"HS: {self.hs}, HR: {self.hr}")
        self.L = 0.0065  # 기온 감율(K/m)
        self.T0 = 288.15  # 표준 온도(K)
        self.g = 9.80665  # 중력 가속도(m/s^2)
        self.R = 287.05  # 기체 상수(J/(kg·K))
        self.b = 0.0086  # 기체 상수(J/(kg·K))


    # def calculate_qfe(self, pressure, temperature):
    #     # QFE는 스테이션 압력과 동일
    #     exponent = self.hs / (7996 + 0.0086 * self.hs + 29.33 * temperature)
    #     qfe = pressure * math.exp(exponent)
    #     return qfe
    def calculate_pressure(self, pressure, temperature, humidity):
        """QFE, QNH 및 QFF를 계산하는 함수"""
        
        # 1. QFE 계산
        exponent_qfe = self.hs / (7996 + 0.0086 * self.hs + 29.33 * temperature)
        qfe = pressure * math.exp(exponent_qfe)

        # 2. 온도를 켈빈으로 변환
        temp_k = temperature + 273.15

        # 상수 정의
        c = 0.00325  # °C/m 상수
        
        # d 값 계산
        d = 0.19025 * (math.log(qfe / 1013.2315))
        
        # 지수 계산
        exponent = (0.03416 * self.hr * (1 - d)) / (288.2 + c * self.hr)
        
        # QNH 계산
        qnh = qfe * math.exp(exponent)
        
        # 4. QFF 계산 (온도와 습도 기반)
        b = 0.0086  # °C/m 상수

        # 지수 계산
        exponent = self.hr / (7996 + b * self.hr + 29.33 * temperature)
        
        # QFF 계산
        qff = qfe * math.exp(exponent)
        
        # 결과 반환 (QFE, QNH, QFF)
        return qfe, qnh, qff
    
    # def calculate_qnh(self, pressure, temperature):
        
    #     exponent = self.hs / (7996 + 0.0086 * self.hs + 29.33 * temperature)
    #     qfe = pressure * math.exp(exponent)
        
    #     temp_k = temperature + 273.15
    #     exponent = (self.g) / (self.R * self.L)
    #     factor = 1 - (self.L * self.elevation) / temp_k
    #     qnh = pressure * (factor ** (-exponent)) * (1 + self.hs) * (1 + self.hr)
    #     return qnh

    # def calculate_qff(self, pressure, temperature, humidity):
    #     # QFF 계산은 복잡하며, 여기서는 간단히 실제 온도와 습도를 고려하여 계산
    #     temp_k = temperature + 273.15
    #     # 수증기 분압 계산
    #     e = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5)) * (humidity / 100)
    #     # 습윤 공기의 가상 온도 계산
    #     virtual_temp = temp_k / (1 - (e / pressure) * (1 - 0.622))
    #     exponent = (self.g * self.elevation) / (self.R * virtual_temp)
    #     qff = pressure * math.exp(exponent)
    #     return qff


