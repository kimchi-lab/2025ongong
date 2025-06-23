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

st.set_page_config(layout="wide")
st.title("다중선형회귀를 통한 산불 위험도 예측 및 다익스트라 대피소 안내 시스템")

# 📁 파일 업로드
st.sidebar.header("📁 데이터 업로드")
fire_file = st.sidebar.file_uploader("① 산불위험지역 CSV 업로드", type="csv")
shelter_file = st.sidebar.file_uploader("② 대피소 위치 CSV 업로드", type="csv")

if fire_file and shelter_file:
    df = pd.read_csv(fire_file)
    shelters = pd.read_csv(shelter_file)

    required_cols = {"위도", "경도", "습도편차", "풍량"}
    if not required_cols.issubset(df.columns):
        st.error("❌ 산불 CSV에 '위도', '경도', '습도편차', '풍량' 열이 모두 포함되어야 합니다.")
        st.stop()

    if not {"위도", "경도"}.issubset(shelters.columns):
        st.error("❌ 대피소 CSV에 '위도', '경도' 열이 포함되어야 합니다.")
        st.stop()

    # 🔢 선형 회귀 예측 (풍속 영향 크게 설정)
    humidity_diff = df["습도편차"].values
    wind_speed = df["풍량"].values
    X = np.column_stack((humidity_diff, wind_speed))
    y = 50 + (1.5 * humidity_diff + 3.5 * wind_speed)
    model = LinearRegression().fit(X, y)
    df["위험도"] = model.predict(X)

    # 🗺️ 지도 시각화
    st.subheader("🗺️ 산불 히트맵 + 위험 중심점 → 반경 2km 대피소 연결")
    m = folium.Map(location=[df["위도"].mean(), df["경도"].mean()], zoom_start=11)
    HeatMap(df[["위도", "경도", "위험도"]].values.tolist(), radius=15).add_to(m)

    # 중심점 표시
    max_idx = df["위험도"].idxmax()
    center_point = (df.loc[max_idx, "위도"], df.loc[max_idx, "경도"])
    folium.Marker(center_point, icon=folium.Icon(color="red"), tooltip="위험 중심점 🔥").add_to(m)

    # 대피소 연결 (반경 2km 이내만)
    for idx, row in shelters.iterrows():
        shelter_coord = (row["위도"], row["경도"])
        dist = geodesic(center_point, shelter_coord).meters
        if dist <= 2000:
            folium.Marker(shelter_coord, icon=folium.Icon(color="blue"),
                          tooltip=f"대피소 {idx} ({dist:.0f}m)").add_to(m)
            folium.PolyLine([center_point, shelter_coord], color="green").add_to(m)

    st_folium(m, width=900, height=600)

    # 📈 선형 회귀 시각화
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
