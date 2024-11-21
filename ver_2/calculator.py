import math

class Calculator:
    def __init__(self, hs=0.0, hr=0.0):
        self.hs = hs  # HS 값
        self.hr = hr  # HR 값
        # print(f"HS: {self.hs}, HR: {self.hr}")
        self.L = 0.0065  # 기온 감율(K/m)
        self.T0 = 288.15  # 표준 온도(K)
        self.g = 9.80665  # 중력 가속도(m/s^2)
        self.R = 287.05  # 기체 상수(J/(kg·K))
        self.b = 0.0086  # 기체 상수(J/(kg·K))  
    
    def calculate(self, pressure, temperature):
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
        return round(qnh, 2), round(qfe, 2), round(qff, 2)
    