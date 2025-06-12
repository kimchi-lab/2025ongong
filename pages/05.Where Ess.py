import time
import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt

# 정렬 알고리즘들
def selection_sort(arr, key):
    data = arr.copy()
    for i in range(len(data)):
        max_idx = i
        for j in range(i + 1, len(data)):
            if data[j][key] > data[max_idx][key]:
                max_idx = j
        data[i], data[max_idx] = data[max_idx], data[i]
    return data

def bubble_sort(arr, key):
    data = arr.copy()
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            if data[j][key] < data[j + 1][key]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data

def quick_sort(arr, key):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = [x for x in arr[1:] if x[key] > pivot[key]]
    right = [x for x in arr[1:] if x[key] <= pivot[key]]
    return quick_sort(left, key) + [pivot] + quick_sort(right, key)

# Streamlit 시작
st.set_page_config(layout="wide")
st.title("📍 지역별 ESS 설치 적합도 분석 및 정렬 알고리즘 비교")
st.caption("※ 기온편차↓ 강수량↓ → ESS 설치 적합도↑ / 정렬 알고리즘 비교 시각화 포함")

uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("📊 원본 데이터 미리보기")
    st.dataframe(df.head())

    # 정규화 및 적합도 계산
    scaler = MinMaxScaler()
    df['온도편차(정규화)'] = scaler.fit_transform(df[['평균기온편차(°C)']])
    df['강수량(정규화)'] = scaler.fit_transform(df[['강수량(mm)']])
    df['ESS_적합도'] = (1 - df['온도편차(정규화)']) * (1 - df['강수량(정규화)'])

    # 지도 표시
    st.subheader("🗺️ ESS 적합도 지도 시각화")
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

    # 정렬 알고리즘 비교
    st.subheader("📐 정렬 알고리즘 선택 및 성능 비교")
    algo = st.selectbox("사용할 정렬 알고리즘을 선택하세요", ["선택 정렬", "버블 정렬", "퀵 정렬"])

    sort_functions = {
        "선택 정렬": selection_sort,
        "버블 정렬": bubble_sort,
        "퀵 정렬": quick_sort
    }

    base_data = df[['지점정보', '평균기온편차(°C)', '강수량(mm)', 'ESS_적합도']].to_dict(orient='records')

    time_results = {}
    top10_results = None

    for name, func in sort_functions.items():
        data_copy = base_data.copy()
        start = time.time()
        sorted_data = func(data_copy, 'ESS_적합도')
        end = time.time()
        time_results[name] = end - start
        if name == algo:
            top10_results = pd.DataFrame(sorted_data[:10])

    st.subheader(f"🏆 {algo} 기준 ESS 적합도 TOP 10")
    st.dataframe(top10_results)

    st.subheader("⏱️ 정렬 알고리즘별 실행 시간 (초)")
    st.bar_chart(time_results)
