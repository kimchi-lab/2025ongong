import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import re

st.set_page_config(page_title="network MST simulator", layout="wide")


# --- 도분초(DMS) → 십진수 변환 ---
def dms_to_decimal(dms):
    try:
        parts = re.findall(r"\d+(?:\.\d+)?", str(dms))
        if len(parts) == 3:
            d, m, s = map(float, parts)
            return round(d + m / 60 + s / 3600, 6)
        return None
    except:
        return None

st.markdown("""
**CSV 형식 안내:** 기지국, 위도, 경도, 전송속도(Mbps)
- 위도/경도는 도분초(예: `127° 09' 47.65"`) 혹은 십진수 모두 가능
- 전송속도는 숫자 (높을수록 좋음)
""")

uploaded_file = st.file_uploader("📂 CSV 업로드", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except:
        df = pd.read_csv(uploaded_file, encoding="cp949")

    if {"기지국", "위도", "경도", "전송속도"}.issubset(df.columns):

        # 위경도 변환
        if df['위도'].astype(str).str.contains("°").any():
            df['위도'] = df['위도'].apply(dms_to_decimal)
            df['경도'] = df['경도'].apply(dms_to_decimal)

        df = df[
            df['위도'].between(-90, 90) &
            df['경도'].between(-180, 180) &
            df['전송속도'].apply(lambda x: str(x).replace('.', '', 1).isdigit())
        ].reset_index(drop=True)

        if len(df) < 2:
            st.warning("⚠️ 유효한 기지국이 2개 미만입니다.")
            st.stop()

        # --- 그래프 구축 (거리 + 전송속도 기반) ---
        edges = []
        for i in range(len(df)):
            for j in range(i + 1, len(df)):
                coord1 = (df.loc[i, '위도'], df.loc[i, '경도'])
                coord2 = (df.loc[j, '위도'], df.loc[j, '경도'])
                distance = geodesic(coord1, coord2).meters
                speed_i = float(df.loc[i, '전송속도'])
                speed_j = float(df.loc[j, '전송속도'])
                avg_speed = (speed_i + speed_j) / 2
                weight = distance / avg_speed  # 속도가 빠를수록 유리
                edges.append((df.loc[i, '기지국'], df.loc[j, '기지국'], weight))

        G = nx.Graph()
        G.add_weighted_edges_from(edges)
        mst = nx.minimum_spanning_tree(G, algorithm="prim")

        st.subheader("📈 최적 통신망 결과 (속도+거리 기반)")
        mst_edges = [
            {"From": u, "To": v, "가중치": round(d['weight'], 2)}
            for u, v, d in mst.edges(data=True)
        ]
        st.dataframe(pd.DataFrame(mst_edges))

        pos = {row['기지국']: (row['경도'], row['위도']) for _, row in df.iterrows()}

        fig, ax = plt.subplots(figsize=(10, 8))
        nx.draw(G, pos, with_labels=True, node_color='lightgray', edge_color='gray', node_size=500, ax=ax)
        nx.draw(mst, pos, with_labels=True, node_color='skyblue', edge_color='blue', width=2, node_size=700, ax=ax)
        plt.title("MST 최적 통신망 (속도/거리 기반)")
        st.pyplot(fig)

    else:
        st.error("❗ CSV 파일에 '기지국', '위도', '경도', '전송속도' 열이 포함되어야 합니다.")
