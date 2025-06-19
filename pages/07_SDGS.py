import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
import networkx as nx
import random

st.set_page_config(page_title="경상도 산불 히트맵", layout="wide")
st.title("🔥 경상도 산불 히트맵 & MST 대피소 연결")

# -------------------------------
# 경상도 내 임의의 산불 발생 좌표
fires = pd.DataFrame({
    "위도": [35.8 + random.uniform(-0.3, 0.3) for _ in range(80)],
    "경도": [128.8 + random.uniform(-0.3, 0.3) for _ in range(80)]
})

# 경상도 주요 대피소 예시 좌표
shelters = pd.DataFrame({
    "위도": [35.85, 35.92, 35.78, 35.74, 35.88, 36.0],
    "경도": [128.95, 129.02, 128.85, 128.78, 129.1, 128.9]
})

# -------------------------------
# 지도 시각화 시작
fire_coords = fires[["위도", "경도"]].values.tolist()
shelter_coords = shelters[["위도", "경도"]].values.tolist()

m = folium.Map(location=[35.85, 128.95], zoom_start=10)
HeatMap(fire_coords, radius=15).add_to(m)

# -------------------------------
# MST 그래프 구성 및 연결
G = nx.Graph()
for i in range(len(shelter_coords)):
    for j in range(i + 1, len(shelter_coords)):
        dist = geodesic(shelter_coords[i], shelter_coords[j]).km
        G.add_edge(i, j, weight=dist)

mst = nx.minimum_spanning_tree(G)

# -------------------------------
# 대피소 마커 및 MST 선 추가
for idx, coord in enumerate(shelter_coords):
    folium.Marker(coord, icon=folium.Icon(color="blue"), tooltip=f"대피소 {idx+1}").add_to(m)

for u, v in mst.edges:
    folium.PolyLine([shelter_coords[u], shelter_coords[v]], color="green").add_to(m)

# -------------------------------
# Streamlit 표시
st.subheader("🗺️ 산불 히트맵 + MST 기반 대피소 연결 (경상도)")
st_folium(m, width=1000, height=600)

st.caption("⚠️ 임의의 경상도 예시 데이터 기반 - 파일 업로드 없이 작동")
