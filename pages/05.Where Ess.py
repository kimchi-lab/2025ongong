
import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import KDTree
import folium
from streamlit_folium import st_folium
import math

st.set_page_config(layout="wide")
st.title("📍 ESS 설치 적합도 분석 + K-d 트리 기반 근접 추천 시스템")
st.caption("※ 기온편차↓ 강수량↓ → ESS 설치 적합도↑ / 클릭 기반 위치 선택 + 추천 지점 선 연결 포함")

# 거리 계산 함수 (Haversine)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 파일 업로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("📊 데이터 미리보기")
    st.dataframe(df.head())

    # 정규화 및 적합도 계산
    scaler = MinMaxScaler()
    df['온도편차(정규화)'] = scaler.fit_transform(df[['평균기온편차(°C)']])
    df['강수량(정규화)'] = scaler.fit_transform(df[['강수량(mm)']])
    df['ESS_적합도'] = (1 - df['온도편차(정규화)']) * (1 - df['강수량(정규화)'])

    # 지도 클릭 기반 위치 선택
    st.subheader("🖱️ 지도에서 위치 클릭 → 근처 고적합도 지역 추천")
    base_map = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=7)
    folium.TileLayer("cartodb positron").add_to(base_map)

    clicked = st_folium(base_map, height=400, returned_objects=["last_clicked"])

    if clicked and clicked["last_clicked"]:
        click_lat = clicked["last_clicked"]["lat"]
        click_lon = clicked["last_clicked"]["lng"]

        st.success(f"선택한 위치: 위도 {click_lat:.4f}, 경도 {click_lon:.4f}")

        # K-d 트리로 인접 지점 검색
        tree = KDTree(df[['위도', '경도']].values, leaf_size=2)
        dist, idx = tree.query([[click_lat, click_lon]], k=5)
        nearby_df = df.iloc[idx[0]].copy()
        nearby_df['거리(km 추정)'] = [haversine(click_lat, click_lon, r['위도'], r['경도']) for _, r in nearby_df.iterrows()]
        nearby_df = nearby_df.sort_values(by='ESS_적합도', ascending=False)

        st.subheader("📌 주변 고적합도 지점 추천")
        st.dataframe(nearby_df[['지점정보', 'ESS_적합도', '거리(km 추정)']])

        # 지도에 마커 및 선 추가
        map2 = folium.Map(location=[click_lat, click_lon], zoom_start=8)
        folium.Marker([click_lat, click_lon], tooltip="선택한 위치", icon=folium.Icon(color="green")).add_to(map2)

        for _, row in nearby_df.iterrows():
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=6,
                color='purple',
                fill=True,
                fill_color='orange',
                fill_opacity=row['ESS_적합도'],
                tooltip=(
                    f"{row['지점정보']}<br>"
                    f"ESS 적합도: {row['ESS_적합도']:.3f}<br>"
                    f"거리: {row['거리(km 추정)']:.2f} km"
                )
            ).add_to(map2)

            folium.PolyLine(locations=[[click_lat, click_lon], [row['위도'], row['경도']]],
                            color='blue', weight=2).add_to(map2)

        st.subheader("📍 선택 위치 기준 추천 경로 지도")
        st_folium(map2, height=500)

    # 전체 적합도 순위
    st.subheader("🏆 ESS 적합도 전체 순위 (Top 10)")
    top10 = df.sort_values(by='ESS_적합도', ascending=False).head(10)
    st.dataframe(top10[['지점정보', 'ESS_적합도', '평균기온편차(°C)', '강수량(mm)']])
