# streamlit_app.py (경상북도 히트맵 + 선택 중심점 연결 + 회귀 기반 위험도 예측)
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import matplotlib.pyplot as plt
import random

st.set_page_config(layout="wide")
st.title("🔥 경상북도 산불 위험 예측 및 대피소 연결 시각화")

# -------------------------------
# 사품 산불 데이터 (Sample)
@st.cache_data
def generate_fire_data():
    base_coords = {
        "의성군": (36.35, 128.7),
        "안동시": (36.57, 128.73),
        "청송군": (36.43, 129.06),
        "영양군": (36.66, 129.11),
        "영덕군": (36.42, 129.37),
        "울진군": (36.99, 129.4),
        "대구광역시": (35.87, 128.6),
    }
    fires = []
    for city, (lat, lon) in base_coords.items():
        for _ in range(30):
            fires.append([lat + random.uniform(-0.02, 0.02), lon + random.uniform(-0.02, 0.02)])

    # 무조건 포함 위험 지점
    fires.append([36.3821, 128.6967])
    fires.append([36.3802, 128.6286])
    return pd.DataFrame(fires, columns=["위도", "경도"])

fires = generate_fire_data()

# -------------------------------
# 대피소 데이터
shelters = pd.DataFrame({
    "위도": [ ... ],  # 기존 생략된 좌표 포함
    "경도": [ ... ]
})

# -------------------------------
# 시군구 선택
regions = [ ... ]  # 동일
region_coords = { ... }  # 동일
selected_region = st.selectbox("📍 지역 선택", options=regions)
center = region_coords[selected_region]

# 중심점 추출
coords = fires[["위도", "경도"]].values
kmeans = KMeans(n_clusters=3, random_state=0).fit(coords)
centroids = kmeans.cluster_centers_
selected = st.selectbox("🔍 연결할 중심점 선택 (0~2)", options=list(range(3)))

# 회귀 예측 모델 생성
@st.cache_data
def generate_regression_data():
    np.random.seed(42)
    X = pd.DataFrame({
        "산불발생이력": np.random.randint(0, 100, 100),
        "기온편차": np.random.uniform(-5, 5, 100),
        "습도편차": np.random.uniform(-10, 10, 100),
        "풍량": np.random.uniform(0, 10, 100)
    })
    y = 100 - (X["습도편차"] + np.random.normal(0, 5, 100))
    model = RandomForestRegressor().fit(X, y)
    preds = model.predict(X)
    return X, preds, model

X, preds, model = generate_regression_data()

risk_scores = model.predict(pd.DataFrame({
    "산불발생이력": np.random.randint(30, 80, len(fires)),
    "기온편차": np.random.uniform(-3, 3, len(fires)),
    "습도편차": np.random.uniform(-8, 5, len(fires)),
    "풍량": np.random.uniform(0, 6, len(fires))
}))
fires["위험도"] = risk_scores

# 지도 생성
@st.cache_data
def generate_map(fires, shelters, centroids, selected, center):
    m = folium.Map(location=center, zoom_start=11)
    heat_data = [[row["위도"], row["경도"], row["위험도"]] for _, row in fires.iterrows()]
    HeatMap(heat_data, radius=15, max_val=100).add_to(m)

    for i, (lat, lon) in enumerate(centroids):
        color = "red" if i == selected else "gray"
        folium.Marker([lat, lon], icon=folium.Icon(color=color), tooltip=f"중심점 {i}").add_to(m)

    selected_center = centroids[selected]
    shelter_coords = shelters[["위도", "경도"]].values.tolist()
    for idx, coord in enumerate(shelter_coords):
        distance = geodesic((selected_center[0], selected_center[1]), (coord[0], coord[1])).meters
        if distance <= 2000:
            folium.Marker(coord, icon=folium.Icon(color="blue"), tooltip=f"Shelter {idx+1} ({distance:.0f}m)").add_to(m)
            folium.PolyLine([selected_center, coord], color="green").add_to(m)

    return m

# 지도 출력
m = generate_map(fires, shelters, centroids, selected, center)
st.subheader("🗌 선택 지역 산불 히트맵 및 대피소 연결 시각화")
st_data = st_folium(m, width=900, height=600)

# 예측 시각화
st.subheader("📊 산불 위험도 예측 결과 (사품)")
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(range(len(preds[:20])), preds[:20], color="salmon")
ax.set_title("사품 지점별 산불 위험도 (0~100)")
ax.set_ylabel("위험도 점수")
st.pyplot(fig)

st.markdown("---")
