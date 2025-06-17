import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("💧 폐수배출시설 ↔ 빗물이용시설 위치 시각화")

# 파일 업로드
waste_file = st.file_uploader("1️⃣ 폐수배출시설 CSV 업로드", type="csv")
rain_file = st.file_uploader("2️⃣ 빗물이용시설 CSV 업로드", type="csv")

if waste_file and rain_file:
    # 데이터 읽기
    try:
        waste_df = pd.read_csv(waste_file, encoding='cp949')
        rain_df = pd.read_csv(rain_file, encoding='cp949')
    except UnicodeDecodeError:
        waste_df = pd.read_csv(waste_file, encoding='utf-8')
        rain_df = pd.read_csv(rain_file, encoding='utf-8')

    # 지오코딩 설정
    geolocator = Nominatim(user_agent="geo_app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    def get_lat_lon(addr):
        try:
            location = geocode(addr)
            if location:
                return pd.Series([location.latitude, location.longitude])
        except:
            return pd.Series([None, None])
        return pd.Series([None, None])

    with st.spinner("⏳ 주소 → 위경도 변환 중..."):
        waste_df[['lat', 'lon']] = waste_df["사업장소재지"].apply(get_lat_lon)
        rain_df[['lat', 'lon']] = rain_df["시설물주소"].apply(get_lat_lon)

    # 지도 생성
    m = folium.Map(location=[37.25, 127.2], zoom_start=11)

    for _, row in waste_df.dropna(subset=['lat', 'lon']).iterrows():
        folium.Marker([row['lat'], row['lon']], tooltip="폐수배출시설", icon=folium.Icon(color='red')).add_to(m)

    for _, row in rain_df.dropna(subset=['lat', 'lon']).iterrows():
        folium.Marker([row['lat'], row['lon']], tooltip="빗물이용시설", icon=folium.Icon(color='blue')).add_to(m)

    st.markdown("### 🌍 시각화된 지도")
    st_data = st_folium(m, width=800, height=600)
