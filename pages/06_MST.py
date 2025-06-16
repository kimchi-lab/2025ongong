import streamlit as st
import pandas as pd
import networkx as nx
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="통신망 MST 시뮬레이터", layout="wide")
st.title("📡 Prim 알고리즘 기반 최적 통신망 구축")

# --- 도분초(DMS) -> 십진수 변환 함수 ---
def dms_to_decimal(dms):
    parts = re.findall(r"[\d.]+", dms)
    if len(parts) == 3:
        d, m, s = map(float, parts)
        return round(d + m / 60 + s / 3600, 6)
    return None

# --- 파일 업로드 ---
uploaded_file = st.file_uploader("기지국 위치 CSV 파일 업로드 (기지국, 위도, 경도)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
        if df.empty:
            st.error("❗ CSV 파일이 비어 있습니다. 데이터를 확인해주세요.")
            st.stop()
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(uploaded_file, encoding="cp949")
            if df.empty:
                st.error("❗ CSV 파일이 비어 있습니다. 데이터를 확인해주세요.")
                st.stop()
        except Exception as e:
            st.error(f"❗ 파일을 읽는 중 오류 발생: {e}")
            st.stop()
    except Exception as e:
        st.error(f"❗ 파일을 읽는 중 오류 발생: {e}")
        st.stop()

    if {"기지국", "위도", "경도"}.issubset(df.columns):

        # DMS 형식이라면 변환
        if df['위도'].dtype == object:
            df['위도'] = df['위도'].apply(dms_to_decimal)
            df['경도'] = df['경도'].apply(dms_to_decimal)

        # 좌표가 유효한 경우만 필터링
        df = df[
            df['위도'].between(-90, 90) &
            df['경도'].between(-180, 180)
        ].reset_index(drop=True)

        # --- 거리 기반 그래프 생성 ---
        edges = []
        for i in range(len(df)):
            for j in range(i + 1, len(df)):
                coord1 = (df.loc[i, '위도'], df.loc[i, '경도'])
                coord2 = (df.loc[j, '위도'], df.loc[j, '경도'])
                dist = geodesic(coord1, coord2).meters
                edges.append((df.loc[i, '기지국'], df.loc[j, '기지국'], dist))

        # --- Prim MST 생성 ---
        G = nx.Graph()
        G.add_weighted_edges_from(edges)
        mst = nx.minimum_spanning_tree(G, algorithm="prim")

        # --- 결과 출력 ---
        st.subheader("📊 MST 최적 통신망 결과")
        mst_edges = [
            {"From": u, "To": v, "Distance (m)": round(d['weight'], 2)}
            for u, v, d in mst.edges(data=True)
        ]
        st.dataframe(pd.DataFrame(mst_edges))

        # --- 시각화 ---
        pos = {row['기지국']: (row['경도'], row['위도']) for _, row in df.iterrows()}

        fig, ax = plt.subplots(figsize=(10, 8))
        nx.draw(G, pos, with_labels=True, node_color='lightgray', node_size=500, edge_color='lightgray', ax=ax)
        nx.draw(mst, pos, with_labels=True, node_color='skyblue', node_size=700, edge_color='blue', width=2, ax=ax)
        plt.title("MST 기반 최적 통신망")
        st.pyplot(fig)

    else:
        st.error("❗ CSV 파일은 반드시 '기지국', '위도', '경도' 열을 포함해야 합니다.")
