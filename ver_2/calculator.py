import math

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
        temp_k = temperature + 273.15
        # 수증기 분압 계산
        e = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5)) * (humidity / 100)
        # 습윤 공기의 가상 온도 계산
        virtual_temp = temp_k / (1 - (e / pressure) * (1 - 0.622))
        exponent = (self.g * self.elevation) / (self.R * virtual_temp)
        qff = pressure * math.exp(exponent)
        return qff
