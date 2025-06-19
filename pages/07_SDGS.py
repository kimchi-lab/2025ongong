import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from sklearn.linear_model import LogisticRegression
from geopy.distance import geodesic
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import random
import chardet
from io import BytesIO

# ---------------------
# CSV 인코딩 자동 감지
# ---------------------
def read_csv_with_detected_encoding(uploaded_file):
    raw = uploaded_file.read()
    result = chardet.detect(raw)
    encoding = result['encoding']
    return pd.read_csv(BytesIO(raw), encoding=encoding)

# ---------------------
# Streamlit UI
# ---------------------
st.title("🌲 산불 위험 예측 및 화학사고 대피소 안내 시스템")

uploaded_fire = st.file_uploader("🔥 산불 데이터 (fire_data.csv)", type="csv")
uploaded_shelter = st.file_uploader("🏠 대피소 데이터 (chemical_shelters.csv)", type="csv")

if uploaded_fire is not None and uploaded_shelter is not None:
    try:
        fires = read_csv_with_detected_encoding(uploaded_fire)
        shelters = read_csv_with_detected_encoding(uploaded_shelter)

        # ---------------------
        # 기후 변수 샘플 추가
        # ---------------------
        fires = fires.dropna(subset=["발생장소_시도", "발생장소_시군구"])
        fires = fires.sample(50, random_state=0)

        random.seed(42)
        fires["기온(℃)"] = [round(random.uniform(10, 30), 1) for _ in range(len(fires))]
        fires["습도(%)"] = [random.randint(30, 90) for _ in range(len(fires))]
        fires["풍속(m/s)"] = [round(random.uniform(0.5, 5.0), 1) for _ in range(len(fires))]
        fires["강수량(mm)"] = [round(random.uniform(0, 10), 1) for _ in range(len(fires))]
        fires["산불발생여부"] = fires["피해면적_합계"].apply(lambda x: 0 if pd.isna(x) or x == 0 else 1)

        # ---------------------
        # 로지스틱 회귀 모델 학습
        # ---------------------
        X = fires[["기온(℃)", "습도(%)", "풍속(m/s)", "강수량(mm)"]]
        y = fires["산불발생여부"]
        model = LogisticRegression().fit(X, y)

        # ---------------------
        # 사용자 입력
        # ---------------------
        selected_city = st.selectbox("시도 선택", sorted(fires["발생장소_시도"].unique()))
        selected_gu = st.selectbox("시군구 선택", sorted(fires[fires["발생장소_시도"] == selected_city]["발생장소_시군구"].unique()))

        temp = st.slider("기온 (℃)", 10, 35, 25)
        humidity = st.slider("습도 (%)", 20, 100, 50)
        wind = st.slider("풍속 (m/s)", 0, 10, 2)
        rain = st.slider("강수량 (mm)", 0, 20, 1)

        X_input = pd.DataFrame([[temp, humidity, wind, rain]], columns=X.columns)
        pred = model.predict(X_input)[0]
        pred_proba = model.predict_proba(X_input)[0][1]

        st.subheader("🌡️ 산불 위험도 예측")
        st.write(f"예측 결과: {'🔥 위험' if pred else '✅ 낮음'} (확률: {pred_proba:.2%})")

        # ---------------------
        # 현재 위치 좌표 설정
        # ---------------------
        geolocator = Nominatim(user_agent="fire_app")
        location = geolocator.geocode(f"{selected_city} {selected_gu}")
        user_coord = (location.latitude, location.longitude)

        # ---------------------
        # 가장 가까운 대피소 찾기
        # ---------------------
        shelters = shelters.dropna(subset=["위도", "경도"])
        shelters["거리(km)"] = shelters.apply(lambda row: geodesic(user_coord, (row["위도"], row["경도"])).km, axis=1)
        closest_shelters = shelters.sort_values("거리(km)").head(5)

        # ---------------------
        # 지도 시각화
        # ---------------------
        m = folium.Map(location=user_coord, zoom_start=12)
        folium.Marker(user_coord, tooltip="현재 위치", icon=folium.Icon(color="red")).add_to(m)

        for _, row in closest_shelters.iterrows():
            folium.Marker(
                [row["위도"], row["경도"]],
                tooltip=f"대피소: {row['시설명'] if '시설명' in row else '이름없음'}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)
            folium.PolyLine([user_coord, (row["위도"], row["경도"])]).add_to(m)

        # 위험지역 HeatMap (위도/경도 존재할 경우만)
        if "위도" in fires.columns and "경도" in fires.columns:
            heat_data = fires.dropna(subset=["위도", "경도"])
            if not heat_data.empty:
                HeatMap(heat_data[["위도", "경도"]].values, radius=15).add_to(m)

        st.subheader("🗺️ 지도 시각화")
        st_folium(m, width=700, height=500)

        st.markdown("---")
        st.caption("데이터 출처: 산림청, 환경부, 공공데이터포털")

    except Exception as e:
        st.error(f"❌ 오류 발생: {e}")
else:
    st.info("CSV 파일 두 개를 모두 업로드해주세요.")
