# streamlit_app.py
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
import networkx as nx
import chardet

# -----------------------------
# 파일 업로드
# -----------------------------
st.sidebar.title("📂 CSV 파일 업로드")
fire_file = st.sidebar.file_uploader("🔥 산불 통계 데이터 업로드", type="csv")
shelter_file = st.sidebar.file_uploader("🏠 대피소 목록 업로드", type="csv")

def detect_encoding(file):
    raw = file.read()
    result = chardet.detect(raw)
    file.seek(0)
    return result['encoding']

if fire_file and shelter_file:
    try:
        fire_encoding = detect_encoding(fire_file)
        fires = pd.read_csv(fire_file, encoding=fire_encoding)
    except Exception as e:
        st.error(f"🔥 산불 데이터 파일 로딩 실패: {e}")
        st.stop()

    try:
        shelter_encoding = detect_encoding(shelter_file)
        shelters = pd.read_csv(shelter_file, encoding=shelter_encoding)
    except Exception as e:
        st.error(f"🏠 대피소 데이터 파일 로딩 실패: {e}")
        st.stop()

    # -----------------------------
    # 열 이름 확인 및 정제
    # -----------------------------
    fires.columns = fires.columns.str.strip().str.replace('"', '')
    shelters.columns = shelters.columns.str.strip().str.replace('"', '')

    st.write("🔥 산불 데이터 열 목록:", fires.columns.tolist())
    st.write("🏠 대피소 데이터 열 목록:", shelters.columns.tolist())

    def find_lat_lon(df):
        lat_col = next((col for col in df.columns if "위도" in col), None)
        lon_col = next((col for col in df.columns if "경도" in col), None)
        return lat_col, lon_col

    fire_lat_col, fire_lon_col = find_lat_lon(fires)
    shelter_lat_col, shelter_lon_col = find_lat_lon(shelters)

    if not fire_lat_col or not fire_lon_col:
        st.error(f"🔥 산불 데이터에서 위도/경도 열을 찾을 수 없습니다. 열 목록: {fires.columns.tolist()}")
        st.stop()
    if not shelter_lat_col or not shelter_lon_col:
        st.error(f"🏠 대피소 데이터에서 위도/경도 열을 찾을 수 없습니다. 열 목록: {shelters.columns.tolist()}")
        st.stop()

    fires = fires.dropna(subset=[fire_lat_col, fire_lon_col])
    shelters = shelters.dropna(subset=[shelter_lat_col, shelter_lon_col])
    fire_coords = fires[[fire_lat_col, fire_lon_col]].values.tolist()
    shelter_coords = shelters[[shelter_lat_col, shelter_lon_col]].values.tolist()

    # -----------------------------
    # 지도 생성
    # -----------------------------
    m = folium.Map(location=fire_coords[0], zoom_start=11)
    HeatMap(fire_coords, radius=15).add_to(m)

    # -----------------------------
    # MST (최소신장트리) 계산
    # -----------------------------
    G = nx.Graph()
    for i in range(len(shelter_coords)):
        for j in range(i + 1, len(shelter_coords)):
            dist = geodesic(shelter_coords[i], shelter_coords[j]).km
            G.add_edge(i, j, weight=dist)

    mst = nx.minimum_spanning_tree(G)

    # -----------------------------
    # 대피소 및 MST 연결 시각화
    # -----------------------------
    for idx, coord in enumerate(shelter_coords):
        folium.Marker(coord, icon=folium.Icon(color="blue"), tooltip=f"Shelter {idx+1}").add_to(m)

    for u, v in mst.edges:
        point1 = shelter_coords[u]
        point2 = shelter_coords[v]
        folium.PolyLine([point1, point2], color="green").add_to(m)

    st.subheader("🗺️ 산불 히트맵 및 MST 대피소 연결")
    st_data = st_folium(m, width=900, height=600)

    st.markdown("---")
    st.caption("데이터 출처: 산림청, 환경부, 공공데이터포털")
else:
    st.warning("좌측 사이드바에서 두 개의 CSV 파일을 업로드하세요.")
