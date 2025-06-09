import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# 글로벌 시가총액 Top 10 기업 (2025 기준 대략 추정)
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

# 사용자 입력
selected = st.multiselect("기업 선택", list(companies.keys()), default=["Apple (AAPL)", "Microsoft (MSFT)"])

if not selected:
    st.warning("최소 1개 기업을 선택하세요.")
    st.stop()

# 최근 1년 기간
end = datetime.today()
start = end - timedelta(days=365)

# 주가 데이터 가져오기
tickers = [companies[name] for name in selected]
data = yf.download(tickers, start=start, end=end)["Adj Close"]

# 단일 기업일 경우 DataFrame 형식으로 변환
if isinstance(data, pd.Series):
    data = data.to_frame()
    data.columns = [selected[0]]

# 결측치 제거
data = data.dropna()

# 선 그래프: 주가
st.subheader("📊 주가 추이")
fig_price = px.line(data, x=data.index, y=data.columns, labels={"value": "가격", "variable": "기업"}, title="최근 1년 주가 변화")
st.plotly_chart(fig_price, use_container_width=True)

# 누적 수익률 계산
st.subheader("📈 누적 수익률")
returns = (data / data.iloc[0] - 1) * 100
fig_returns = px.line(returns, x=returns.index, y=returns.columns, labels={"value": "수익률 (%)", "variable": "기업"}, title="최근 1년 누적 수익률")
st.plotly_chart(fig_returns, use_container_width=True)
