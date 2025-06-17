import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# 🔁 CSV 파일 불러오기
df = pd.read_csv("폐수배출시설.csv")  # 또는 빗물이용시설.csv

# 🧭 주소 컬럼명 확인 후 여기에 맞게 수정하세요
address_column = "사업장소재지"  # 또는 '시설물주소'

# 🌍 지오코더 설정 (OpenStreetMap Nominatim)
geolocator = Nominatim(user_agent="geo_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# 📍 위경도 추출 함수
def get_lat_lon(addr):
    try:
        location = geocode(addr)
        if location:
            return pd.Series([location.latitude, location.longitude])
        else:
            return pd.Series([None, None])
    except:
        return pd.Series([None, None])

# 📌 적용
df[['lat', 'lon']] = df[address_column].apply(get_lat_lon)

# 💾 저장
df.to_csv("폐수배출시설_with_coords.csv", index=False)  # 결과 파일

print("✅ 위경도 추출 완료 및 저장 완료!")
