class DataProcessor:
    def process_data(self, data):
        # 기본적으로 쉼표로 구분된 기압과 온도 값을 처리
        if ',' in data:
            try:
                pressure_str, temperature_str = data.split(',')
                pressure = float(pressure_str.strip())
                temperature = float(temperature_str.strip())
                return pressure, temperature
            except ValueError as e:
                print(f"Failed to parse data: {data}, Error: {e}")
                return None, None
        else:
            # 쉼표가 없는 경우 로그로만 처리
            print(f"Received command response: {data}")
            return None, None
