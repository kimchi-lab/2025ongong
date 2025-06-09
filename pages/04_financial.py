import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# 🔹 시가총액 상위 10개 글로벌 기업 (2025 기준 추정)
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

# 🔹 사용자 선택
selected = st.multiselect("기업 선택", list(companies.keys()), default=["Apple (AAPL)", "Microsoft (MSFT)"])

# 예외 처리
if not selected:
    st.warning("최소 1개 이상의 기업을 선택하세요.")
    st.stop()

# 🔹 최근 1년 기간 설정
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 🔹 선택된 티커로 yfinance 주가 다운로드
tickers = [companies[name] for name in selected]
df = yf.download(tickers, start=start_date, end=end_date)["Adj Close"]

# 단일 선택 시 Series → DataFrame 변환
if isinstance(df, pd.Series):
    df = df.to_frame()
    df.columns = [selected[0]]

# 결측치 제거
df = df.dropna()

# 🔸 1. 주가 시각화
st.subheader("📊 주가 추이")

df_price = df.reset_index().melt(id_vars="Date", var_name="기업", value_name="가격")

fig_price = px.line(df_price, x="Date", y="가격", color="기업",
                    title="최근 1년 주가 변화", height=500)
st.plotly_chart(fig_price, use_container_width=True)

# 🔸 2. 누적 수익률 시각화
st.subheader("📈 누적 수익률 (%)")

df_return = (df / df.iloc[0] - 1) * 100
df_return_long = df_return.reset_index().melt(id_vars="Date", var_name="기업", value_name="수익률")

fig_return = px.line(df_return_long, x="Date", y="수익률", color="기업",
                     title="최근 1년 누적 수익률", height=500)
st.plotly_chart(fig_return, use_container_width=True)
