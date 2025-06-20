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
st.title("🔥 다중선형회귀법을 통한 산불 위험도 예측과 다익스트라를 통한 대피소 안내 ")

# -------------------------------
# 1. 파일 업로드
uploaded_file = st.file_uploader("📁 CSV 파일 업로드 (위도, 경도, 습도편차, 풍량 포함)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    required_cols = {"위도", "경도", "습도편차", "풍량"}
    if not required_cols.issubset(df.columns):
        st.error("❌ CSV에 '위도', '경도', '습도편차', '풍량' 열이 모두 포함되어야 합니다.")
        st.stop()

    # -------------------------------
    # 2. 선형회귀로 산불위험도 예측
    humidity_diff = df["습도편차"].values
    wind_speed = df["풍량"].values
    coords = df[["위도", "경도"]].values

    X = np.column_stack((humidity_diff, wind_speed))
    model = LinearRegression().fit(X, y := 100 - (1.5 * humidity_diff + 2 * wind_speed))  # 위험도 추정
    df["위험도"] = model.predict(X)

    # -------------------------------
    # 3. 지도 시각화 (히트맵 + 다익스트라)
    st.subheader("🗺️ 산불 히트맵 + 대피소 연결 (위험도 기준)")

    m = folium.Map(location=[df["위도"].mean(), df["경도"].mean()], zoom_start=11)
    heat_data = df[["위도", "경도", "위험도"]].values.tolist()
    HeatMap(heat_data, radius=15, max_val=100).add_to(m)

    # 위험 중심점 = 위험도 가장 높은 지점
    max_idx = df["위험도"].idxmax()
    center_point = (df.loc[max_idx, "위도"], df.loc[max_idx, "경도"])
    folium.Marker(center_point, icon=folium.Icon(color="red"), tooltip="위험 중심점").add_to(m)

    # 대피소 예시 (랜덤 생성 또는 고정 가능)
    shelters = pd.DataFrame({
        "위도": [36.36, 36.58, 36.44, 36.65, 36.41, 36.97],
        "경도": [128.68, 128.74, 129.05, 129.10, 129.36, 129.39]
    })

    # 다익스트라 그래프 구성
    G = nx.Graph()
    G.add_node("center")
    for idx, row in shelters.iterrows():
        shelter_coord = (row["위도"], row["경도"])
        dist = geodesic(center_point, shelter_coord).meters
        if dist <= 5000:
            G.add_edge("center", idx, weight=dist)
            folium.Marker(shelter_coord, icon=folium.Icon(color="blue"), tooltip=f"Shelter {idx} ({dist:.0f}m)").add_to(m)
            folium.PolyLine([center_point, shelter_coord], color="green").add_to(m)

    st_folium(m, width=900, height=600)

    # -------------------------------
    # 4. 회귀 시각화
    st.markdown("---")
    st.subheader("📈 산불위험도 선형회귀 분석 (습도편차, 풍량 → 위험도)")

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
