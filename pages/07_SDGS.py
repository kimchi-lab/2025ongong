# streamlit_app.py (경상도 히트맵 + 선택 중심점 연결)
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
from sklearn.cluster import KMeans
import numpy as np
import random

st.set_page_config(layout="wide")
st.title(" 다익스트라 기반 산불 밀집 지역 인근 대피소 '')

# 샘플 산불 좌표 (경상도 인근)
@st.cache_data
def generate_fire_data():
    random.seed(42)
    return pd.DataFrame({
        "위도": [35.7 + random.uniform(-0.05, 0.05) for _ in range(300)],
        "경도": [128.8 + random.uniform(-0.05, 0.05) for _ in range(300)]
    })

fires = generate_fire_data()

# 샘플 대피소 좌표 (경상도 인근)
shelters = pd.DataFrame({
    "위도": [35.72, 35.74, 35.75, 35.76, 35.78, 35.79],
    "경도": [128.82, 128.81, 128.84, 128.86, 128.80, 128.83]
})

# 중심점 추출 (KMeans)
coords = fires[["위도", "경도"]].values
kmeans = KMeans(n_clusters=3, random_state=0).fit(coords)
centroids = kmeans.cluster_centers_

# 사용자 선택
selected = st.selectbox("🔍 연결할 중심점 선택 (0~2)", options=list(range(3)))

# 지도 생성
@st.cache_data
def generate_map(fires, shelters, centroids, selected):
    m = folium.Map(location=[35.75, 128.82], zoom_start=12)

    # 히트맵 전체 표시
    HeatMap(fires[["위도", "경도"]].values.tolist(), radius=15).add_to(m)

    # 중심점 마커 표시
    for i, (lat, lon) in enumerate(centroids):
        color = "red" if i == selected else "gray"
        folium.Marker([lat, lon], icon=folium.Icon(color=color), tooltip=f"중심점 {i}").add_to(m)

    # 대피소 마커 표시
    shelter_coords = shelters[["위도", "경도"]].values.tolist()
    for idx, coord in enumerate(shelter_coords):
        folium.Marker(coord, icon=folium.Icon(color="blue"), tooltip=f"Shelter {idx+1}").add_to(m)

    # 선택 중심점 ↔ 모든 대피소 연결
    selected_center = centroids[selected]
    for coord in shelter_coords:
        folium.PolyLine([selected_center, coord], color="green").add_to(m)

    return m

# 지도 출력
m = generate_map(fires, shelters, centroids, selected)
st.subheader("🗺️ 산불 히트맵과 중심점 ↔ 대피소 연결 시각화")
st_folium(m, width=900, height=600)

st.markdown("---")

