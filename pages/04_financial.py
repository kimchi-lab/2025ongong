import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# 시가총액 상위 10개 기업
companies = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Saudi Aramco (2222.SR)": "2222.SR",
    "Alphabet (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN",
    "NVIDIA (NVDA)": "NVDA",
    "Berkshire Hathaway (BRK-B)": "BRK-B",
    "Meta (META)": "META",
    "TSMC (TSM)": "TSM",
    "Tesla (TSLA)": "TSLA"
}

st.title("📈 글로벌 시가총액 Top 10 기업 주가 및 누적 수익률 시각화")

selected = st.multiselect("기업 선택", list(companies.keys()), default=["Apple (AAPL)", "Microsoft (MSFT)"])
if not selected:
    st.warning("최소 1개 이상의 기업을 선택하세요.")
    st.stop()

tickers = [companies[name] for name in selected]
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# yfinance 데이터 다운로드
raw_data = yf.download(tickers, start=start_date, end=end_date, group_by="ticker", auto_adjust=True)

# 기업별 주가 데이터 정리
df_close = pd.DataFrame()
for name in selected:
    ticker = companies[name]
    try:
        if len(tickers) == 1:
            # 단일 종목은 컬럼 구조 없음
            df_close[name] = raw_data["Close"]
        else:
            df_close[name] = raw_data[ticker]["Close"]
    except Exception as e:
        st.warning(f"{name}의 데이터를 가져오지 못했습니다: {e}")

# 유효 데이터 없으면 중단
if df_close.empty:
    st.error("선택한 기업의 유효한 데이터를 가져오지 못했습니다.")
    st.stop()

# 결측 제거
df_close = df_close.dropna()

# 📊 주가 시각화
st.subheader("📊 주가 추이")
df_price = df_close.reset_index().melt(id_vars="Date", var_name="기업", value_name="가격")
fig_price = px.line(df_price, x="Date", y="가격", color="기업", title="최근 1년 주가 변화")
st.plotly_chart(fig_price, use_container_width=True)

# 📈 누적 수익률 시각화
st.subheader("📈 누적 수익률 (%)")
df_return = (df_close / df_close.iloc[0] - 1) * 100
df_return_long = df_return.reset_index().melt(id_vars="Date", var_name="기업", value_name="수익률")
fig_return = px.line(df_return_long, x="Date", y="수익률", color="기업", title="최근 1년 누적 수익률")
st.plotly_chart(fig_return, use_container_width=True)

