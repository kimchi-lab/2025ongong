import streamlit as st
import pandas as pd
import plotly.express as px

# 📁 데이터 로딩
df = pd.read_csv("data.csv", encoding="cp949")

# 📍 지역 선택
region = st.selectbox("📍 지역을 선택하세요", df['행정구역'].unique())

# ✅ 연령 구간 컬럼만 필터링
age_cols = [col for col in df.columns if '세' in col and '계' in col]

# 🔢 슬라이더용 연령 구간 리스트 생성
age_labels = [col.split('_')[-1] for col in age_cols]  # ex) 0~9세, 10~19세...
selected_range = st.slider(
    "🎚️ 시각화할 연령 구간을 선택하세요",
    min_value=0,
    max_value=len(age_labels)-1,
    value=(0, len(age_labels)-1),
    format="%d단계"
)

# 📌 선택 지역 행 가져오기
row = df[df['행정구역'] == region].iloc[0]

# 🧹 인구 수 전처리
selected_labels = age_labels[selected_range[0]:selected_range[1]+1]
cted_range[1]+1]
selected_cols = age_cols[selected_range[0]:selected_range[1]+1]
population = row[selected_cols].astype(str).str.replace(',', '').astype(int)

# 📊 데이터프레임 구성
df_plot = pd.DataFrame({
    "연령구간": selected_labels,
    "인구수": population
})

# 📈 시각화
fig = px.bar(
    df_plot,
    x="연령구간",
