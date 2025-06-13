import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import KDTree  # ✅ 알고리즘: K-d 트리 (2차원 좌표 탐색용 트리)
import folium
from streamlit_folium import st_folium
import math

# ✅ 알고리즘: Haversine 공식 – 위도/경도 간 거리(km) 계산 알고리즘
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ✅ 알고리즘: 선택 정렬 (Selection Sort)
# ✅ 자료구조: 리스트 (list) – dict 리스트 형태로 변환 후 수동 정렬
def selection_sort_top_n(df, key, top_n):
    data = df.to_dict(orient='records')  # DataFrame → list[dict]
    n = len(data)
    for i in range(min(top_n, n)):
        max_idx = i
        for j in range(i + 1, n):
            if data[j][key] > data[max_idx][key]:
                max_idx = j
        data[i], data[max_idx] = data[max_idx], data[i]  # swap
    return pd.DataFrame(data[:top_n])

st.set_page_config(layout="wide")
st.title("📍 ESS 적합도 분석 + 선택 정렬 + K-d 트리 탐색")
st.caption("정렬 알고리즘과 탐색 알고리즘을 활용한 공간 기반 데이터 분석 프로젝트")

uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("📊 데이터프레임 미리보기")
    st.dataframe(df.head())

    # ✅ 알고리즘: Min-Max 정규화
    # ✅ 자료구조: DataFrame (2차원 테이블)
    scaler = MinMaxScaler()
    df['온도편차(정규화)'] = scaler.fit_transform(df[['평균기온편차(°C)']])
    df['강수량(정규화)'] = scaler.fit_transform(df[['강수량(mm)']])
    df['ESS_적합도'] = (1 - df['온도편차(정규화)']) * (1 - df['강수량(정규화)'])

    # ✅ 알고리즘: 지도 클릭 기반 탐색
    # ✅ 자료구조: 위도/경도 배열 (2차원 numpy array)
    st.subheader("🖱️ 지도 클릭 → 주변 고적합도 추천")
    base_map = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=7)
    folium.TileLayer("cartodb positron").add_to(base_map)
    clicked = st_folium(base_map, height=400, returned_objects=["last_clicked"])

    if clicked and clicked["last_clicked"]:
        click_lat = clicked["last_clicked"]["lat"]
        click_lon = clicked["last_clicked"]["lng"]
        st.success(f"선택한 좌표: 위도 {click_lat:.4f}, 경도 {click_lon:.4f}")

        # ✅ 알고리즘: K-d 트리 최근접 이웃 탐색 (탐색 알고리즘)
        # ✅ 자료구조: KDTree (sklearn 구현체)
        tree = KDTree(df[['위도', '경도']].values, leaf_size=2)
        dist, idx = tree.query([[click_lat, click_lon]], k=5)

        # ✅ 자료구조: DataFrame 슬라이싱 + 정렬
        nearby_df = df.iloc[idx[0]].copy()
        nearby_df['거리(km 추정)'] = [
            haversine(click_lat, click_lon, r['위도'], r['경도']) for _, r in nearby_df.iterrows()
        ]
        nearby_df = nearby_df.sort_values(by='ESS_적합도', ascending=False)

        st.subheader("📌 주변 추천 지점")
        st.dataframe(nearby_df[['지점정보', 'ESS_적합도', '거리(km 추정)']])

        # ✅ 알고리즘: 지도 시각화 (folium + 거리 선 연결)
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
            folium.PolyLine(
                locations=[[click_lat, click_lon], [row['위도'], row['경도']]],
                color='blue', weight=2
            ).add_to(map2)

        st.subheader("📍 지도 시각화")
        st_folium(map2, height=500)

    # ✅ 선택 정렬 알고리즘으로 ESS 적합도 순위 출력
    st.subheader("🏆 선택 정렬 기반 ESS 적합도 순위 Top 10")
    sorted_top10 = selection_sort_top_n(df, 'ESS_적합도', 10)
    st.dataframe(sorted_top10[['지점정보', 'ESS_적합도', '평균기온편차(°C)', '강수량(mm)']])
