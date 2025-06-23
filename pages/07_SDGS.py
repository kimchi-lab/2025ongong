import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from mpl_toolkits.mplot3d import Axes3D
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
import networkx as nx

st.set_page_config(layout="wide")
st.title("🔥 다중선형회귀법을 통한 산불 위험도 예측과 다익스트라를 통한 대피소 안내")

# -------------------------------
# 1. CSV 파일 업로드
st.sidebar.header("📁 데이터 업로드")
fire_file = st.sidebar.file_uploader("① 산불위험지역 CSV 업로드", type="csv")
shelter_file = st.sidebar.file_uploader("② 대피소 위치 CSV 업로드", type="csv")

if fire_file and shelter_file:
    df = pd.read_csv(fire_file)
    shelters = pd.read_csv(shelter_file)

    # -------------------------------
    # 2. 입력 검증
    required_cols = {"위도", "경도", "습도편차", "풍량"}
    if not required_cols.issubset(df.columns):
        st.error("❌ 산불 CSV에 '위도', '경도', '습도편차', '풍량' 열이 모두 포함되어야 합니다.")
        st.stop()

    if not {"위도", "경도"}.issubset(shelters.columns):
        st.error("❌ 대피소 CSV에 '위도', '경도' 열이 포함되어야 합니다.")
        st.stop()

    # -------------------------------
    # 3. 다중선형회귀 기반 위험도 예측
    humidity_diff = df["습도편차"].values
    wind_speed = df["풍량"].values
    coords = df[["위도", "경도"]].values

    X = np.column_stack((humidity_diff, wind_speed))
    model = LinearRegression().fit(X, y := 100 - (1.5 * humidity_diff + 2 * wind_speed))
    df["위험도"] = model.predict(X)

    # -------------------------------
    # 4. 지도 시각화
    st.subheader("🗺️ 산불 히트맵 + 위험지역 ↔ 대피소 연결")

    m = folium.Map(location=[df["위도"].mean(), df["경도"].mean()], zoom_start=11)
    HeatMap(df[["위도", "경도", "위험도"]].values.tolist(), radius=15, max_val=100).add_to(m)

    # 위험 중심점 마커
    max_idx = df["위험도"].idxmax()
    center_point = (df.loc[max_idx, "위도"], df.loc[max_idx, "경도"])
    folium.Marker(center_point, icon=folium.Icon(color="red"), tooltip="위험 중심점").add_to(m)

    # -------------------------------
    # 5. 다익스트라 그래프 생성 및 최단경로 계산
    G = nx.Graph()

    # 위험지역 노드
    for i, fire in df.iterrows():
        fire_node = f"fire_{i}"
        G.add_node(fire_node, pos=(fire["위도"], fire["경도"]))

        for j, shelter in shelters.iterrows():
            shelter_node = f"shelter_{j}"
            if shelter_node not in G:
                G.add_node(shelter_node, pos=(shelter["위도"], shelter["경도"]))
            dist = geodesic((fire["위도"], fire["경도"]), (shelter["위도"], shelter["경도"])).meters
            if dist <= 10000:  # 반경 10km
                G.add_edge(fire_node, shelter_node, weight=dist)

    # 최단경로 시각화
    for fire_node in [n for n in G.nodes if n.startswith("fire_")]:
        lengths = nx.single_source_dijkstra_path_length(G, fire_node)
        shelters_only = {k: v for k, v in lengths.items() if k.startswith("shelter_")}
        if shelters_only:
            closest = min(shelters_only.items(), key=lambda x: x[1])
            shelter_node, dist = closest

            fire_pos = G.nodes[fire_node]["pos"]
            shelter_pos = G.nodes[shelter_node]["pos"]

            folium.Marker(fire_pos, icon=folium.Icon(color="orange"), tooltip=fire_node).add_to(m)
            folium.Marker(shelter_pos, icon=folium.Icon(color="blue"), tooltip=shelter_node).add_to(m)
            folium.PolyLine([fire_pos, shelter_pos], color="green", weight=2).add_to(m)

    st_folium(m, width=900, height=600)

    # -------------------------------
    # 6. 회귀 시각화
    st.markdown("---")
    st.subheader("📈 산불위험도 선형회귀 분석")

    x1_range = np.linspace(humidity_diff.min(), humidity_diff.max(), 30)
    x2_range = np.linspace(wind_speed.min(), wind_speed.max(), 30)
    x1_grid, x2_grid = np.meshgrid(x1_range, x2_range)
    x_grid = np.column_stack((x1_grid.ravel(), x2_grid.ravel()))
    y_pred_grid = model.predict(x_grid).reshape(x1_grid.shape)

    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.view_init(elev=25, azim=135)
    ax.scatter(humidity_diff, wind_speed, df["위험도"], color='blue', label='Data')
    ax.plot_surface(x1_grid, x2_grid, y_pred_grid, alpha=0.5, cmap='rainbow')
    ax.set_xlabel("Humidity Deviation")
    ax.set_ylabel("Wind Speed")
    ax.set_zlabel("Predicted Fire Risk")
    ax.set_title("Linear Regression: Humidity/Wind → Fire Risk")
    ax.legend()
    st.pyplot(fig)
