import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import folium
from streamlit_folium import folium_static

st.title("📍 지역별 ESS 설치 적합도 지도")

uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("📊 데이터 미리보기")
    st.dataframe(df.head())

    scaler = MinMaxScaler()
    df['온도편차(정규화)'] = scaler.fit_transform(df[['평균기온편차(°C)']])
    df['강수량(정규화)'] = scaler.fit_transform(df[['강수량(mm)']])
    df['ESS_적합도'] = df['온도편차(정규화)'] * (1 - df['강수량(정규화)'])

    st.subheader("📍 ESS 설치 적합도 지도")

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
                f"강수량: {row['강수량(mm)']}mm<br>"
                f"ESS 적합도: {row['ESS_적합도']:.2f}"
            )
        ).add_to(m)

    folium_static(m)

    st.subheader("🏆 ESS 적합도 상위 지역")
    st.dataframe(df.sort_values(by='ESS_적합도', ascending=False).head(10))

