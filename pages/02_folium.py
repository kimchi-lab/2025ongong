import streamlit as st
import pandas as pd
import plotly.express as px

# 데이터 로드
df = pd.read_csv("people_gender.csv", encoding="cp949")

# 지역 선택
regions = df[df["행정구역"].str.contains("\\(")]["행정구역"].unique()
selected_region = st.selectbox("지역 선택", regions)

# 연령대 선택
age_min, age_max = st.slider("연령대 범위 선택", min_value=0, max_value=100, value=(0, 100), step=5)

# 선택한 지역의 데이터만 추출
region_data = df[df["행정구역"] == selected_region].iloc[0]

# 남성과 여성 컬럼 분리
male_cols = [col for col in df.columns if "남_" in col and "세" in col]
female_cols = [col for col in df.columns if "여_" in col and "세" in col]
ages = [int(col.split("_")[-1].replace("세", "").replace(" 이상", "100")) for col in male_cols]

# 필터링 및 숫자 정리
male_values = [(age, int(str(region_data[col]).replace(",", ""))) for age, col in zip(ages, male_cols) if age_min <= age <= age_max]
female_values = [(age, -int(str(region_data[col]).replace(",", ""))) for age, col in zip(ages, female_cols) if age_min <= age <= age_max]

# 시각화용 데이터프레임 생성
df_plot = pd.DataFrame(male_values + female_values, columns=["연령", "인구수"])
df_plot["성별"] = ["남성"] * len(male_values) + ["여성"] * len(female_values)

# 인구 피라미드 그리기
fig = px.bar(df_plot, x="인구수", y="연령", color="성별", orientation="h",
             title=f"{selected_region} 인구 피라미드", height=700)
fig.update_layout(yaxis=dict(autorange="reversed"))

# 출력
st.plotly_chart(fig)
