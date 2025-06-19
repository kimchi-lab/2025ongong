# streamlit_app.py (되기만 하게 만든 버전)
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
import networkx as nx
import random

# -----------------------------
# 예제 데이터 사용 (업로드 없이 동작)
# -----------------------------
st.title("🔥 산불 히트맵 & MST 대피소 연결")

# 샘플 산불 좌표 (서울 인근)
fires = pd.DataFrame({
    "위도": [37.55 + random.uniform(-0.03, 0.03) for _ in range(50)],
    "경도": [126.98 + random.uniform(-0.03, 0.03) for _ in range(50)]
})

# 샘플 대피소 좌표 (서울 인근)
shelters = pd.DataFrame({
    "위도": [37.56, 37.57, 37.54, 37.55, 37.58],
    "경도": [126.97, 126.99, 126.96, 126.95, 126.98]
})

# -----------------------------
# 히트맵 시각화
# -----------------------------
fire_coords = fires[["위도", "경도"]].values.tolist()
shelter_coords = shelters[["위도", "경도"]].values.tolist()

m = folium.Map(location=fire_coords[0], zoom_start=12)
HeatMap(fire_coords, radius=15).add_to(m)

# -----------------------------
# MST 연결
# -----------------------------
G = nx.Graph()
for i in range(len(shelter_coords)):
    for j in range(i + 1, len(shelter_coords)):
        dist = geodesic(shelter_coords[i], shelter_coords[j]).km
        G.add_edge(i, j, weight=dist)

mst = nx.minimum_spanning_tree(G)

# -----------------------------
# 대피소 마커 및 선 그리기
# -----------------------------
for idx, coord in enumerate(shelter_coords):
    folium.Marker(coord, icon=folium.Icon(color="blue"), tooltip=f"Shelter {idx+1}").add_to(m)

for u, v in mst.edges:
    point1 = shelter_coords[u]
    point2 = shelter_coords[v]
    folium.PolyLine([point1, point2], color="green").add_to(m)

st.subheader("🗺️ 산불 발생 히트맵 + MST 대피소 연결")
st_folium(m, width=900, height=600)

st.markdown("---")
st.caption("⚠️ 예시 데이터 기반 - 업로드 없이 작동되도록 구현됨")
