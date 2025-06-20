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
# 샘플 산불 데이터 (경상북도 내 지역)
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

    # 반드시 포함될 위험 지점 추가
    fires.append([36.3821, 128.6967])  # 의성군 안평면 괴산리 산61 근처
    fires.append([36.3802, 128.6286])  # 의성군 안계면 용기리 297-3 근처
    return pd.DataFrame(fires, columns=["위도", "경도"])

fires = generate_fire_data()

# -------------------------------
# 샘플 대피소 데이터 (확대: 각 지역 5~7개 수준 추가)
shelters = pd.DataFrame({
    "위도": [
        36.36, 36.355, 36.358, 36.353, 36.35,  # 의성군
        36.58, 36.575, 36.572, 36.57, 36.568,  # 안동시
        36.45, 36.448, 36.444, 36.442,         # 청송군
        36.65, 36.653, 36.657, 36.66,          # 영양군
        36.4, 36.403, 36.406, 36.41,           # 영덕군
        36.98, 36.983, 36.986, 36.989,         # 울진군
        35.88, 35.882, 35.884, 35.886,         # 대구광역시
        36.3840, 36.3830, 36.3850              # 위험지점 인근
    ],
    "경도": [
        128.71, 128.712, 128.715, 128.717, 128.72,
        128.74, 128.742, 128.745, 128.747, 128.75,
        129.05, 129.052, 129.055, 129.058,
        129.1, 129.103, 129.107, 129.11,
        129.38, 129.383, 129.386, 129.39,
        129.42, 129.423, 129.426, 129.429,
        128.59, 128.592, 128.595, 128.598,
        128.6950, 128.6975, 128.6985
    ]
})

# -------------------------------
# 사용자 선택: 시군구
regions = ["의성군", "안동시", "청송군", "영양군", "영덕군", "울진군", "대구광역시"]
region_coords = {
    "의성군": [36.35, 128.7],
    "안동시": [36.57, 128.73],
    "청송군": [36.43, 129.06],
    "영양군": [36.66, 129.11],
    "영덕군": [36.42, 129.37],
    "울진군": [36.99, 129.4],
    "대구광역시": [35.87, 128.6],
}
selected_region = st.selectbox("📍 지역 선택", options=regions)
center = region_coords[selected_region]

# -------------------------------
# 중심점 추출 (KMeans)
coords = fires[["위도", "경도"]].values
kmeans = KMeans(n_clusters=3, random_state=0).fit(coords)
centroids = kmeans.cluster_centers_

# 사용자 중심점 선택
selected = st.selectbox("🔍 연결할 중심점 선택 (0~2)", options=list(range(3)))

# -------------------------------
# 회귀 모델로 위험도 예측 (임의 데이터)
@st.cache_data
def generate_regression_data():
    np.random.seed(42)
    X = pd.DataFrame({
        "산불발생이력": np.random.randint(0, 100, 100),
        "기온편차": np.random.uniform(-5, 5, 100),
        "습도편차": np.random.uniform(-10, 10, 100),
        "풍량": np.random.uniform(0, 10, 100)
    })
    y = 100 - (X["습도편차"] + np.random.normal(0, 5, 100))  # 습도편차가 낮을수록 높게
    model = RandomForestRegressor().fit(X, y)
    preds = model.predict(X)
    return X, preds, model

X, preds, model = generate_regression_data()

# 예측 위험도와 히트맵에 매핑될 위험도 점수 생성
risk_scores = model.predict(pd.DataFrame({
    "산불발생이력": np.random.randint(30, 80, len(fires)),
    "기온편차": np.random.uniform(-3, 3, len(fires)),
    "습도편차": np.random.uniform(-8, 5, len(fires)),
    "풍량": np.random.uniform(0, 6, len(fires))
}))
fires["위험도"] = risk_scores

# -------------------------------
# 지도 시각화 함수
@st.cache_data
def generate_map(fires, shelters, centroids, selected, center):
    m = folium.Map(location=center, zoom_start=11)
    heat_data = [[row["위도"], row["경도"], row["위험도"]] for _, row in fires.iterrows()]
    HeatMap(heat_data, radius=15, max_val=100).add_to(m)

    for i, (lat, lon) in enumerate(centroids):
        color = "red" if i == selected else "gray"
        folium.Marker([lat, lon], icon=folium.Icon(color=color), tooltip=f"중심점 {i}").add_to(m)

    shelter_coords = shelters[["위도", "경도"]].values.tolist()
    for idx, coord in enumerate(shelter_coords):
        folium.Marker(coord, icon=folium.Icon(color="blue"), tooltip=f"Shelter {idx+1}").add_to(m)

    selected_center = centroids[selected]
    for coord in shelter_coords:
        folium.PolyLine([selected_center, coord], color="green").add_to(m)

    return m

# -------------------------------
# 지도 출력
m = generate_map(fires, shelters, centroids, selected, center)
st.subheader("🗺️ 선택 지역 산불 히트맵 및 대피소 연결 시각화")
st_data = st_folium(m, width=900, height=600)

# -------------------------------
# 예측 결과 시각화
st.subheader("📊 산불 위험도 예측 결과 (샘플)")
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(range(len(preds[:20])), preds[:20], color="salmon")
ax.set_title("샘플 지점별 산불 위험도 (0~100)")
ax.set_ylabel("위험도 점수")
st.pyplot(fig)

st.markdown("---")
