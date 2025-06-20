import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

st.set_page_config(layout="wide")
st.title("🔥 경상북도 산불 위험 예측 및 시각화")

@st.cache_data
def generate_fire_data():
    base_coords = {
        "경상북도 의성군": (36.35, 128.7),
        "경상북도 안동시": (36.57, 128.73),
        "경상북도 청송군": (36.43, 129.06),
        "경상북도 영양군": (36.66, 129.11),
        "경상북도 영덕군": (36.42, 129.37),
        "경상북도 울진군": (36.99, 129.4),
        "대구광역시": (35.87, 128.6),
    }
    fires = []
    for city, (lat, lon) in base_coords.items():
        for _ in range(30):
            fires.append([lat + np.random.uniform(-0.02, 0.02), lon + np.random.uniform(-0.02, 0.02)])
    fires.append([36.3821, 128.6967])
    fires.append([36.3802, 128.6286])
    return pd.DataFrame(fires, columns=["위도", "경도"])

fires = generate_fire_data()

shelters = pd.DataFrame({
    "위도": [36.36, 36.58, 36.44, 36.65, 36.41, 36.97, 35.88, 36.38, 36.37],
    "경도": [128.68, 128.74, 129.05, 129.10, 129.36, 129.39, 128.61, 128.69, 128.63]
})

regions = list(generate_fire_data().drop_duplicates("위도").index)
region_names = list({
    "경상북도 의성군": [36.35, 128.7],
    "경상북도 안동시": [36.57, 128.73],
    "경상북도 청송군": [36.43, 129.06],
    "경상북도 영양군": [36.66, 129.11],
    "경상북도 영덕군": [36.42, 129.37],
    "경상북도 울진군": [36.99, 129.4],
    "대구광역시": [35.87, 128.6]
}.keys())

region_coords = {
    "경상북도 의성군": [36.35, 128.7],
    "경상북도 안동시": [36.57, 128.73],
    "경상북도 청송군": [36.43, 129.06],
    "경상북도 영양군": [36.66, 129.11],
    "경상북도 영덕군": [36.42, 129.37],
    "경상북도 울진군": [36.99, 129.4],
    "대구광역시": [35.87, 128.6]
}

selected_region = st.selectbox("📍 지역 선택", options=region_names)
center = region_coords.get(selected_region, [36.38, 128.69])

coords = fires[["위도", "경도"]].values
kmeans = KMeans(n_clusters=3, random_state=0).fit(coords)
centroids = kmeans.cluster_centers_
selected = st.selectbox("🔍 연결할 중심점 선택 (0~2)", options=list(range(3)))
selected_center = tuple(centroids[selected])

def generate_map_cached():
    if "last_map" not in st.session_state:
        st.session_state.last_map = None
        st.session_state.last_region = None
        st.session_state.last_center_id = None

    if (
        st.session_state.last_map is not None
        and st.session_state.last_region == selected_region
        and st.session_state.last_center_id == selected
    ):
        return st.session_state.last_map

    m = folium.Map(location=selected_center, zoom_start=12)
    heat_data = [[row["위도"], row["경도"], np.random.uniform(60, 100)] for _, row in fires.iterrows()]
    HeatMap(heat_data, radius=15, max_val=100).add_to(m)
    folium.Marker(selected_center, icon=folium.Icon(color="red"), tooltip="위험 중심점").add_to(m)

    G = nx.Graph()
    G.add_node("center")
    shelter_coords = shelters[["위도", "경도"]].values.tolist()
    connected_idxs = []

    for idx, coord in enumerate(shelter_coords):
        distance = geodesic(selected_center, coord).meters
        if distance <= 5000:
            G.add_edge("center", idx, weight=distance)
            connected_idxs.append(idx)

    for idx in connected_idxs:
        coord = shelter_coords[idx]
        dist = G["center"][idx]["weight"]
        folium.Marker(coord, icon=folium.Icon(color="blue"), tooltip=f"Shelter {idx} ({dist:.0f}m)").add_to(m)
        folium.PolyLine([selected_center, coord], color="green").add_to(m)

    st.session_state.last_map = m
    st.session_state.last_region = selected_region
    st.session_state.last_center_id = selected
    return m

st.subheader("🗺️ 산불 히트맵 + 대피소 연결")
m = generate_map_cached()
st_data = st_folium(m, width=900, height=600)

# -------------------------------
st.markdown("---")
st.subheader("📈 산불위험도 선형회귀 분석 (습도편차, 풍량 → 위험도)")

np.random.seed(42)
humidity_diff = np.random.uniform(-10, 10, 100)
wind_speed = np.random.uniform(0, 10, 100)
fire_risk = 100 - (1.5 * humidity_diff + 2 * wind_speed + np.random.normal(0, 5, 100))

X = np.column_stack((humidity_diff, wind_speed))
y = fire_risk

model = LinearRegression().fit(X, y)

x1_range = np.linspace(humidity_diff.min(), humidity_diff.max(), 30)
x2_range = np.linspace(wind_speed.min(), wind_speed.max(), 30)
x1_grid, x2_grid = np.meshgrid(x1_range, x2_range)
x_grid = np.column_stack((x1_grid.ravel(), x2_grid.ravel()))
y_pred_grid = model.predict(x_grid).reshape(x1_grid.shape)

fig = plt.figure(figsize=(8, 5))
ax = fig.add_subplot(111, projection='3d')
ax.view_init(elev=25, azim=135)
ax.scatter(humidity_diff, wind_speed, fire_risk, color='blue', label='Data')
ax.plot_surface(x1_grid, x2_grid, y_pred_grid, alpha=0.5, cmap='rainbow')
ax.set_xlabel("Humidity Deviation")
ax.set_ylabel("Wind Speed")
ax.set_zlabel("Predicted Fire Risk")
ax.set_title("Linear Regression: Humidity/Wind → Fire Risk")
ax.legend()
st.pyplot(fig)
