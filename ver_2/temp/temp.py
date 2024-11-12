import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 스타일 적용
plt.style.use('ggplot')

# CSV 파일을 불러오는 코드
file_path = r'C:\Sitech\data\2024-11-03\sensor_data.csv'  # 실제 파일 이름으로 변경하세요
data = pd.read_csv(file_path)

# timestamp 열을 datetime 형식으로 변환
data['timestamp'] = pd.to_datetime(data['timestamp'])

# 오전 데이터만 필터링 (0시부터 11시 59분까지)
morning_data = data[data['timestamp'].dt.hour < 24]

# Y축의 상한과 하한을 temperature_barometer 값으로 자동 계산 (10% 여유 추가)
y_min = morning_data['temperature_barometer'].min()
y_max = morning_data['temperature_barometer'].max()
y_margin = (y_max - y_min) * 0.1  # 10% 여유
y_min -= y_margin
y_max += y_margin

# 필터링된 오전 데이터를 그래프로 그리기
plt.figure(figsize=(12, 6))
plt.plot(morning_data['timestamp'], morning_data['temperature_barometer'], label='Temperature Barometer', marker='o', color='b', linewidth=2)
plt.xlabel('Timestamp')
plt.ylabel('Temperature Barometer')
plt.title('Temperature Barometer Over Time (Morning Data)')

# X축을 데이터 범위에 맞게 자동 간격 조정 및 포맷 지정
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# Y축 범위를 계산된 값으로 설정
ax.set_ylim(y_min, y_max)

plt.xticks(rotation=45)
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.7)
plt.tight_layout()
plt.show()
