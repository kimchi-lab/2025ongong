import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import re
import pydeck as pdk

st.set_page_config(page_title="MST 통신망 최적화 시뮬레이터", layout="wide")
st.title("📡 MST 통신망 최적 구축 경로 시뮬레이션")

# --- DMS to Decimal Converter ---
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
**CSV 형식 예시:** 기지국, 위도, 경도, 전송속도 (Mbps)
- 위도/경도는 도분초 또는 소수형 모두 지원
- 전송속도는 숫자 (클수록 빠름)
""")

uploaded_file = st.file_uploader("📂 CSV 파일 업로드", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except:
        df = pd.read_csv(uploaded_file, encoding="cp949")

    if {"기지국", "위도", "경도", "전송속도"}.issubset(df.columns):

        # Convert coordinates
        if df['위도'].astype(str).str.contains("°").any():
            df['위도'] = df['위도'].apply(dms_to_decimal)
            df['경도'] = df['경도'].apply(dms_to_decimal)

        df = df[
            df['위도'].between(-90, 90) &
            df['경도'].between(-180, 180) &
            df['전송속도'].apply(lambda x: str(x).replace('.', '', 1).isdigit())
        ].reset_index(drop=True)

        if len(df) < 2:
            st.warning("⚠️ 최소 2개 이상의 기지국이 필요합니다.")
            st.stop()

        # --- Build graph with distance and speed ---
        edges = []
        coord_dict = {}
        for i in range(len(df)):
            coord_dict[df.loc[i, '기지국']] = (df.loc[i, '위도'], df.loc[i, '경도'])
            for j in range(i + 1, len(df)):
                coord1 = (df.loc[i, '위도'], df.loc[i, '경도'])
                coord2 = (df.loc[j, '위도'], df.loc[j, '경도'])
                distance = geodesic(coord1, coord2).meters
                speed_i = float(df.loc[i, '전송속도'])
                speed_j = float(df.loc[j, '전송속도'])
                avg_speed = (speed_i + speed_j) / 2
                weight = distance / avg_speed
                edges.append((df.loc[i, '기지국'], df.loc[j, '기지국'], weight))

        G = nx.Graph()
        G.add_weighted_edges_from(edges)
        mst = nx.minimum_spanning_tree(G, algorithm="prim")

        st.subheader("📈 MST 결과 테이블")
        mst_edges = [
            {"From": u, "To": v, "Weight": round(d['weight'], 2)}
            for u, v, d in mst.edges(data=True)
        ]
        st.dataframe(pd.DataFrame(mst_edges))

        # --- 지도 위에 MST 연결선까지 시각화 ---
        st.subheader("🗺️ 지도 기반 MST 연결 시각화")
        line_data = []
        for u, v in mst.edges():
            coord_u = coord_dict[u]
            coord_v = coord_dict[v]
            line_data.append({
                "from_lat": coord_u[0], "from_lon": coord_u[1],
                "to_lat": coord_v[0], "to_lon": coord_v[1]
            })

        midpoint = df[['위도', '경도']].mean().values.tolist()

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=midpoint[0],
                longitude=midpoint[1],
                zoom=14,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df,
                    get_position='[경도, 위도]',
                    get_fill_color='[0, 128, 255, 160]',
                    get_radius=30,
                ),
                pdk.Layer(
                    "LineLayer",
                    data=line_data,
                    get_source_position='[from_lon, from_lat]',
                    get_target_position='[to_lon, to_lat]',
                    get_width=3,
                    get_color='[0, 255, 0, 180]',
                    pickable=True,
                ),
            ]
        ))

        # --- Graph Visualization ---
        st.subheader("📊 네트워크 그래프")
        pos = {row['기지국']: (row['경도'], row['위도']) for _, row in df.iterrows()}

        fig, ax = plt.subplots(figsize=(10, 8))
        nx.draw(G, pos, with_labels=True, node_color='lightgray', edge_color='gray', node_size=500, ax=ax)
        nx.draw(mst, pos, with_labels=True, node_color='skyblue', edge_color='blue', width=2, node_size=700, ax=ax)
        plt.title("MST 네트워크 그래프")
        st.pyplot(fig)

    else:
        st.error("❗ CSV 파일에 '기지국', '위도', '경도', '전송속도' 열이 필요합니다.")
