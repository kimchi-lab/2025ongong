# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🔥 강원도 산불 위험도 예측 및 인근 대피소")

# -------------------------------
# 1. 지역 선택 기반 지도 시각화
# -------------------------------
region_coords = {
    "강릉": [37.75, 128.9],
    "삼척": [37.45, 129.17],
    "속초": [38.2, 128.6]
}

region = st.selectbox("📍 산불 집중 지역 선택", list(region_coords.keys()))
center = region_coords[region]

# 샘플 산불 데이터 생성 (선택 지역 주변에 생성)
np.random.seed(42)
fires = pd.DataFrame({
    "위도": center[0] + np.random.normal(0, 0.015, 300),
    "경도": center[1] + np.random.normal(0, 0.015, 300)
})

# 샘플 대피소 데이터 생성
shelters = pd.DataFrame({
    "위도": center[0] + np.random.normal(0.01, 0.01, 6),
    "경도": center[1] + np.random.normal(0.01, 0.01, 6)
})

# 중심점 (클러스터 중심) 3개 추출
coords = fires[["위도", "경도"]].values
kmeans = KMeans(n_clusters=3, random_state=0).fit(coords)
centroids = kmeans.cluster_centers_

selected = st.selectbox("🔍 연결할 중심점 선택 (0~2)", options=list(range(3)))

# 지도 생성 함수
@st.cache_data

def generate_map(center, fires, shelters, centroids, selected):
    m = folium.Map(location=center, zoom_start=12)
    HeatMap(fires[["위도", "경도"]].values.tolist(), radius=15).add_to(m)
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

m = generate_map(center, fires, shelters, centroids, selected)
st.subheader("🗺️ 선택 지역 산불 히트맵 및 중심점 ↔ 대피소 연결")
st_folium(m, width=900, height=600)

# -------------------------------
# 2. Random Forest 산불 위험도 예측
# -------------------------------
st.markdown("---")
st.header("랜덤포레스트회귀를 통한 산불 위험도 예측")

# 샘플 데이터 (학습용)
np.random.seed(42)
train_X = pd.DataFrame({
    "산불발생이력": np.random.randint(0, 10, 100),
    "기온편차": np.random.normal(0, 2, 100),
    "습도편차": np.random.normal(0, 5, 100),
    "풍량": np.random.normal(2, 1, 100)
})
train_y = 80 - 5*train_X["습도편차"] + 3*train_X["기온편차"] + 2*train_X["산불발생이력"] + np.random.normal(0, 5, 100)
train_y = np.clip(train_y, 0, 100)

# 모델 학습
model = RandomForestRegressor(n_estimators=100, random_state=0)
model.fit(train_X, train_y)

st.markdown("#### 🔢 입력 변수 설정")
x1 = st.slider("산불발생이력 (최근 5년)", 0, 10, 5)
x2 = st.slider("기온편차 (℃)", -5.0, 5.0, 0.0)
x3 = st.slider("습도편차 (%)", -20.0, 20.0, 0.0)
x4 = st.slider("풍량 (m/s)", 0.0, 10.0, 2.0)

input_df = pd.DataFrame({
    "산불발생이력": [x1],
    "기온편차": [x2],
    "습도편차": [x3],
    "풍량": [x4]
})

# 예측
risk = model.predict(input_df)[0]

# 시각화
st.markdown("#### 📊 산불 위험도 예측 결과")
fig, ax = plt.subplots()
ax.bar(["예측 위험도"], [risk], color="crimson")
ax.set_ylim(0, 100)
ax.set_ylabel("위험도 점수")
st.pyplot(fig)

if risk > 70:
    st.error(f"🚨 매우 높은 위험도: {risk:.1f}점")
elif risk > 40:
    st.warning(f"⚠️ 중간 이상 위험도: {risk:.1f}점")
else:
    st.success(f"🟢 낮은 위험도: {risk:.1f}점")
