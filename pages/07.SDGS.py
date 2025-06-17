import streamlit as st
import pandas as pd
import folium
import networkx as nx
from geopy.distance import geodesic
from streamlit_folium import st_folium
import chardet

st.set_page_config(page_title="MST 기반 환경시설 연결망", layout="wide")
st.title("🌐 MST 기반 폐수-빗물이용시설 최적 연결망 시각화")

# -----------------------------------
# CSV 인코딩 자동 판별하여 읽기
# -----------------------------------
def read_uploaded_csv(uploaded_file):
    rawdata = uploaded_file.read()
    result = chardet.detect(rawdata)
    encoding = result["encoding"]
    uploaded_file.seek(0)
    return pd.read_csv(uploaded_file, encoding=encoding)

# -----------------------------------
# CSV 업로드 받기
# -----------------------------------
waste_file = st.file_uploader("1️⃣ 폐수배출시설 CSV 업로드", type=["csv"])
rain_file = st.file_uploader("2️⃣ 빗물이용시설 CSV 업로드", type=["csv"])

if waste_file and rain_file:
    # CSV 읽기
    waste_df = read_uploaded_csv(waste_file)
    rain_df = read_uploaded_csv(rain_file)

    # lat/lon 필드 확인
    if 'lat' not in waste_df.columns or 'lon' not in waste_df.columns:
        st.error("폐수배출시설 CSV에 'lat', 'lon' 열이 없습니다.")
        st.stop()
    if 'lat' not in rain_df.columns or 'lon' not in rain_df.columns:
        st.error("빗물이용시설 CSV에 'lat', 'lon' 열이 없습니다.")
        st.stop()

    # 거리 제한 설정
    max_dist_km = st.slider("📏 연결 가능한 최대 거리 (km)", 0.5, 10.0, 3.0, step=0.1)
    max_dist_m = max_dist_km * 1000

    # -----------------------------------
    # 지도 생성 및 마커 추가
    # -----------------------------------
    center = [waste_df['lat'].mean(), waste_df['lon'].mean()]
    m = folium.Map(location=center, zoom_start=11)

    for _, row in waste_df.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=f"폐수: {row.get('사업장명', '')}",
            icon=folium.Icon(color='red')
        ).add_to(m)

    for _, row in rain_df.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=f"빗물: {row.get('시설물명', '')}",
            icon=folium.Icon(color='green')
        ).add_to(m)

    # -----------------------------------
    # MST 생성
    # -----------------------------------
    edges = []
    for i, w_row in waste_df.iterrows():
        for j, r_row in rain_df.iterrows():
            coord1 = (w_row['lat'], w_row['lon'])
            coord2 = (r_row['lat'], r_row['lon'])
            dist = geodesic(coord1, coord2).meters
            if dist <= max_dist_m:
                edges.append((f"W{i}", f"R{j}", dist))

    G = nx.Graph()
    G.add_weighted_edges_from(edges)

    if len(G.edges) == 0:
        st.warning("❌ 조건을 만족하는 연결이 없습니다. 거리 제한을 늘려보세요.")
        st.stop()

    mst = nx.minimum_spanning_tree(G)

    for u, v, d in mst.edges(data=True):
        u_type, u_idx = u[0], int(u[1:])
        v_type, v_idx = v[0], int(v[1:])
        u_df = waste_df if u_type == 'W' else rain_df
        v_df = waste_df if v_type == 'W' else rain_df

        coord1 = (u_df.iloc[u_idx]['lat'], u_df.iloc[u_idx]['lon'])
        coord2 = (v_df.iloc[v_idx]['lat'], v_df.iloc[v_idx]['lon'])

        folium.PolyLine([coord1, coord2], color='blue', weight=2).add_to(m)

    # -----------------------------------
    # MST 연결 정보 출력
    # -----------------------------------
    st.subheader("📊 MST 연결 정보")
    edge_table = pd.DataFrame([
        {
            "출발지": u,
            "도착지": v,
            "거리 (m)": round(d['weight'], 2)
        } for u, v, d in mst.edges(data=True)
    ])
    st.dataframe(edge_table, use_container_width=True)

    # 지도 출력
    st.subheader("🗺️ MST 지도 시각화")
    st_folium(m, width=900, height=600)

else:
    st.info("👆 위의 두 CSV 파일을 업로드하면 분석이 시작됩니다.")
