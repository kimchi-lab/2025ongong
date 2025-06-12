import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import KDTree
import folium
from streamlit_folium import folium_static

st.set_page_config(layout="wide")
st.title("📍 ESS 설치 적합도 분석 + K-d 트리 기반 근접 추천 시스템")

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

    # 지도 시각화
    st.subheader("🗺️ 전체 ESS 적합도 지도")
    m = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=7)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=7,
            color='blue',
            fill=True,
            fill_color='red',
            fill_opacity=row['ESS_적합도'],
            tooltip=(
                f"<b>{row['지점정보']}</b><br>"
                f"기온편차: {row['평균기온편차(°C)']}°C<br>"
                f"강수량: {row['강수량(mm)']} mm<br>"
                f"<b>ESS 적합도: {row['ESS_적합도']:.2f}</b>"
            )
        ).add_to(m)
    folium_static(m)

    # K-d 트리 생성
    coords = df[['위도', '경도']].values
    tree = KDTree(coords, leaf_size=2)

    # 지점 선택 → 주변 추천
    st.subheader("📌 지점 선택 → 근처 고적합도 지점 추천")
    selected_site = st.selectbox("지점을 선택하세요", df['지점정보'].tolist())

    selected_row = df[df['지점정보'] == selected_site].iloc[0]
    selected_coord = [[selected_row['위도'], selected_row['경도']]]

    distances, indices = tree.query(selected_coord, k=5)
    nearby_df = df.iloc[indices[0]].copy()
    nearby_df['거리(km 추정)'] = distances[0] * 111
    nearby_df = nearby_df.sort_values(by='ESS_적합도', ascending=False)

    st.markdown(f"**선택 지점:** {selected_site} (위도 {selected_row['위도']}, 경도 {selected_row['경도']})")
    st.dataframe(nearby_df[['지점정보', 'ESS_적합도', '거리(km 추정)']])

    # 추천 지점 지도 표시
    st.subheader("📍 추천 지점 지도 시각화")
    m2 = folium.Map(location=[selected_row['위도'], selected_row['경도']], zoom_start=8)
    folium.Marker(
        location=[selected_row['위도'], selected_row['경도']],
        tooltip=f"선택 지점: {selected_site}",
        icon=folium.Icon(color='green')
    ).add_to(m2)

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
        ).add_to(m2)

    folium_static(m2)
