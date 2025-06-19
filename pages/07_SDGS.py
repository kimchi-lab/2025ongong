# streamlit_app.py
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from sklearn.cluster import KMeans
from geopy.distance import geodesic

# -----------------------------
st.set_page_config(layout="wide")
st.title("🔥 경상도 산불 히트맵 및 대피소 연결 시각화")

# 샘플 산불 데이터 (경상도 주변 랜덤 생성)
fires = pd.DataFrame({
    "위도": [35.8 + (i % 5) * 0.05 for i in range(50)],
    "경도": [128.5 + (i // 5) * 0.03 for i in range(50)]
})

# 샘플 대피소 데이터 (경상도 주변)
shelters = pd.DataFrame({
    "위도": [35.85, 35.9, 35.95, 36.0, 36.05],
    "경도": [128.55, 128.6, 128.65, 128.7, 128.75]
})

# -----------------------------
# 히트맵 시각화 + 중심점 탐지 (KMeans 클러스터링)
# -----------------------------
fire_coords = fires[["위도", "경도"]].values.tolist()
shelter_coords = shelters[["위도", "경도"]].values.tolist()

kmeans = KMeans(n_clusters=3, random_state=0).fit(fire_coords)
centers = kmeans.cluster_centers_.tolist()

selected_idx = st.selectbox("📍 연결할 중심점을 선택하세요", list(range(1, len(centers)+1)))
selected_center = centers[selected_idx - 1]

# -----------------------------
# 지도 생성
# -----------------------------
m = folium.Map(location=selected_center, zoom_start=10)

# 히트맵 추가
HeatMap(fire_coords, radius=15).add_to(m)

# 중심점 마커 표시
for idx, center in enumerate(centers):
    folium.Marker(center, icon=folium.Icon(color="red"), tooltip=f"중심점 {idx+1}").add_to(m)

# 대피소 마커 추가 + 중심점과의 연결선
for idx, shelter in enumerate(shelter_coords):
    folium.Marker(shelter, icon=folium.Icon(color="blue"), tooltip=f"대피소 {idx+1}").add_to(m)
    folium.PolyLine([selected_center, shelter], color="green", weight=2).add_to(m)

# -----------------------------
# 지도 출력
# -----------------------------
st.subheader("🗺️ 산불 히트맵 및 중심점 기반 대피소 연결 시각화")
st_folium(m, width=1000, height=600)

st.markdown("---")
st.caption("🔥 예시 데이터 기반 | 중심점에서 대피소 연결 시각화 (MST 아님)")
