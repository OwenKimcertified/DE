from dotenv import load_dotenv
import pymysql

HOST = "localhost"
USER = "root"
PASS = 'root'

import requests, pandas as pd
from io import StringIO
from datetime import datetime

timePeriod = "tm1=20250101&tm2=20250308"
authKey = "a"
url = f"https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php?{timePeriod}&stn=108&help=1&authKey={authKey}"

dataObject = requests.get(url)

colnames = {
    "TM":           "관측일 (KST)",
    "STN":          "국내 지점번호",
    "WS_AVG":       "일 평균 풍속 (m/s)",
    "WR_DAY":       "일 풍정 (m)",
    "WD_MAX":       "최대풍향",
    "WS_MAX":       "최대풍속 (m/s)",
    "WS_MAX_TM":    "최대풍속 시각 (시분)",
    "WD_INS":       "최대순간풍향",
    "WS_INS":       "최대순간풍속 (m/s)",
    "WS_INS_TM":    "최대순간풍속 시각 (시분)",
    "TA_AVG":       "일 평균기온 (C)",
    "TA_MAX":       "최고기온 (C)",
    "TA_MAX_TM":    "최고기온 시각 (시분)",
    "TA_MIN":       "최저기온 (C)",
    "TA_MIN_TM":    "최저기온 시각 (시분)",
    "TD_AVG":       "일 평균 이슬점온도 (C)",
    "TS_AVG":       "일 평균 지면온도 (C)",
    "TG_MIN":       "일 최저 초상온도 (C)",
    "HM_AVG":       "일 평균 상대습도 (%)",
    "HM_MIN":       "최저습도 (%)",
    "HM_MIN_TM":    "최저습도 시각 (시분)",
    "PV_AVG":       "일 평균 수증기압 (hPa)",
    "EV_S":         "소형 증발량 (mm)",
    "EV_L":         "대형 증발량 (mm)",
    "FG_DUR":       "안개 계속시간 (hr)",
    "PA_AVG":       "일 평균 현지기압 (hPa)",
    "PS_AVG":       "일 평균 해면기압 (hPa)",
    "PS_MAX":       "최고 해면기압 (hPa)",
    "PS_MAX_TM":    "최고 해면기압 시각 (시분)",
    "PS_MIN":       "최저 해면기압 (hPa)",
    "PS_MIN_TM":    "최저 해면기압 시각 (시분)",
    "CA_TOT":       "일 평균 전운량 (1/10)",
    "SS_DAY":       "일조합 (hr)",
    "SS_DUR":       "가조시간 (hr)",
    "SS_CMB":       "캄벨 일조 (hr)",
    "SI_DAY":       "일사합 (MJ/m2)",
    "SI_60M_MAX":   "최대 1시간일사 (MJ/m2)",
    "SI_60M_MAX_TM": "최대 1시간일사 시각 (시분)",
    "RN_DAY":       "일 강수량 (mm)",
    "RN_D99":       "9-9 강수량 (mm)",
    "RN_DUR":       "강수 계속시간 (hr)",
    "RN_60M_MAX":   "1시간 최다강수량 (mm)",
    "RN_60M_MAX_TM":"1시간 최다강수량 시각 (시분)",
    "RN_10M_MAX":   "10분간 최다강수량 (mm)",
    "RN_10M_MAX_TM":"10분간 최다강수량 시각 (시분)",
    "RN_POW_MAX":   "최대 강우강도 (mm/h)",
    "RN_POW_MAX_TM":"최대 강우강도 시각 (시분)",
    "SD_NEW":       "최심 신적설 (cm)",
    "SD_NEW_TM":    "최심 신적설 시각 (시분)",
    "SD_MAX":       "최심 적설 (cm)",
    "SD_MAX_TM":    "최심 적설 시각 (시분)",
    "TE_05":        "0.5m 지중온도 (C)",
    "TE_10":        "1.0m 지중온도 (C)",
    "TE_15":        "1.5m 지중온도 (C)",
    "TE_30":        "3.0m 지중온도 (C)",
    "TE_50":        "5.0m 지중온도 (C)"
}

data_lines = []
for line in dataObject.text.splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    data_lines.append(line)

cleaned_text = "\n".join(data_lines)

df = pd.read_csv(
    StringIO(cleaned_text),
    sep=r"\s+",
    header=None
)

colname_values = list(colnames.values())
df.columns = colname_values[:df.shape[1]]

df['국내 지점번호'] = df['국내 지점번호'].astype(str)
df.loc[df['국내 지점번호'] == '108', '국내 지점번호'] = "Seoul"

df = df[['관측일 (KST)', '일 강수량 (mm)', '일 평균 상대습도 (%)', '최저기온 시각 (시분)', '국내 지점번호']]

conn = pymysql.connect(
    host=HOST, 
    user=USER, 
    password=PASS, 
    database="Weather"
)
cursor = conn.cursor()


_table = """
CREATE TABLE IF NOT EXISTS weather_data (
  observation_date DATE NOT NULL,
  precipitation FLOAT,
  avg_humidity FLOAT,
  min_temp_time VARCHAR(5),
  station VARCHAR(50),
  PRIMARY KEY (observation_date, station)
);
"""
cursor.execute(_table)
conn.commit()

# (4) UPSERT용 SQL
upsert_sql = """
INSERT INTO weather_data (observation_date, precipitation, avg_humidity, min_temp_time, station)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    precipitation = VALUES(precipitation),
    avg_humidity = VALUES(avg_humidity),
    min_temp_time = VALUES(min_temp_time)
"""
# station은 PK 일부라서 UPDATE 항목에는 굳이 안 넣음 (키 자체는 변경 불가)

# (5) 예시 DataFrame (이미 df가 있다고 가정)
# df = pd.DataFrame([...])  # 이 부분은 예시

# (6) df를 순회하여 DB에 UPSERT
for idx, row in df.iterrows():
    # 6.1) 관측일: "20250101" 형태 -> datetime.date 변환
    date_str = str(row['관측일 (KST)'])   # 예: '20250101'
    date_obj = datetime.strptime(date_str, '%Y%m%d').date()  # 2025-01-01 형태로 변환

    # 6.2) 일 강수량 & 일 평균 상대습도: float 변환
    precipitation = float(row['일 강수량 (mm)'])
    avg_humidity = float(row['일 평균 상대습도 (%)'])

    # 6.3) 최저기온 시각 (시분): 문자열로 저장 (예: 441 -> '441')
    min_temp_time = str(row['최저기온 시각 (시분)'])

    # 6.4) 국내 지점번호 (예: 'Seoul')
    station = str(row['국내 지점번호'])

    # 6.5) UPSERT 실행
    cursor.execute(upsert_sql, (date_obj, precipitation, avg_humidity, min_temp_time, station))

# (7) 커밋 & 연결 종료
conn.commit()
cursor.close()
conn.close()