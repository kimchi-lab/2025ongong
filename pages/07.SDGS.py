import streamlit as st
import pandas as pd
import folium
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.extra.rate_limiter import RateLimiter
from streamlit_folium import st_folium

# -------------------------------
# GitHub에서 CSV 불러오기
# -------------------------------
@st.cache_data
def load_data():
    url_waste = "https://raw.githubusercontent.com/kimchi-lab/2025ongong/main/YongIn_Wastewater%20discharge%20facility_20240213.csv"
    url_rain = "https://raw.githubusercontent.com/kimchi-lab/2025ongong/main/YongInFacilitiesUsingRain_20250131.csv"

    waste = pd.read_csv(url_waste, encoding="utf-8")
    rain = pd.read_csv(url_rain, encoding="utf-8")
    return waste, rain

waste_df, rain_df = load_data()

st.title("🌐 MST 기반 폐수-빗물이용시설 최적 연결망 시각화")

# -------------------------------
# 위경도 변환 (geopy)
# -------------------------------
@st.cache_data
def geocode_address(df, address_col):
    geolocator = Nominatim(user_agent="geo_app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    def get_lat_lon(addr):
        try:
            location = geocode(addr)
            if location:
                return pd.Series([location.latitude, location.longitude])
        except:
            return pd.Series([None, None])
        return pd.Series([None, None])

    df[['lat', 'lon']] = df[address_col].apply(get_lat_lon)
    return df.dropna(subset=['lat', 'lon'])

# 실제 주소 컬럼명 지정
waste_df = geocode_address(waste_df, "사업장소재지")
rain_df = geocode_address(rain_df, "시설물주소")

# -------------------------------
# 거리 제한 슬라이더
# -------------------------------
max_dist_km = st.slider("📏 연결 가능한 최대 거리 (km)", 0.5, 10.0, 3.0, step=0.1)
max_dist_m = max_dist_km * 1000

# -------------------------------
# 지도 생성
# -------------------------------
center = [waste_df['lat'].mean(), waste_df['lon'].mean()]
m = folium.Map(location=center, zoom_start=11)

for _, row in waste_df.iterrows():
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"폐수: {row['사업장명']}",
        icon=folium.Icon(color='red')
    ).add_to(m)

for _, row in rain_df.iterrows():
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"빗물: {row['시설물명']}",
        icon=folium.Icon(color='green')
    ).add_to(m)

# -------------------------------
# MST 그래프 구성
# -------------------------------
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
else:
    mst = nx.minimum_spanning_tree(G)

    for u, v, d in mst.edges(data=True):
        u_type, u_idx = u[0], int(u[1:])
        v_type, v_idx = v[0], int(v[1:])
        u_df = waste_df if u_type == 'W' else rain_df
        v_df = waste_df if v_type == 'W' else rain_df

        coord1 = (u_df.iloc[u_idx]['lat'], u_df.iloc[u_idx]['lon'])
        coord2 = (v_df.iloc[v_idx]['lat'], v_df.iloc[v_idx]['lon'])

        folium.PolyLine([coord1, coord2], color='blue', weight=2).add_to(m)

    st.subheader("🔗 MST 연결 정보")
    edge_table = pd.DataFrame([
        {
            "출발지": u,
            "도착지": v,
            "거리 (m)": round(d['weight'], 2)
        } for u, v, d in mst.edges(data=True)
    ])
    st.dataframe(edge_table)

# -------------------------------
# 지도 출력
# -------------------------------
st.subheader("🗺️ MST 지도 시각화")
st_folium(m, width=800, height=600)
