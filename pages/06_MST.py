import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import re

st.set_page_config(page_title="MST Network Simulator", layout="wide")
st.title("📡 Optimized MST Communication Network")

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
**CSV Format:** Station, Latitude, Longitude, Transmission Speed (Mbps)
- Latitude/Longitude supports both DMS (e.g., `127° 09' 47.65"`) and decimal format
- Transmission speed must be a number (higher is better)
""")

uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

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
            st.warning("⚠️ At least two valid stations are required.")
            st.stop()

        # --- Build graph with distance and speed ---
        edges = []
        for i in range(len(df)):
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

        st.subheader("📈 MST Result (Based on Speed and Distance)")
        mst_edges = [
            {"From": u, "To": v, "Weight": round(d['weight'], 2)}
            for u, v, d in mst.edges(data=True)
        ]
        st.dataframe(pd.DataFrame(mst_edges))

        # --- Map Visualization ---
        st.subheader("🗺️ Station Map")
        map_df = df.rename(columns={"기지국": "Station", "위도": "lat", "경도": "lon"})
        st.map(map_df[['lat', 'lon']])

        # --- Graph Visualization ---
        pos = {row['기지국']: (row['경도'], row['위도']) for _, row in df.iterrows()}

        fig, ax = plt.subplots(figsize=(10, 8))
        nx.draw(G, pos, with_labels=True, node_color='lightgray', edge_color='gray', node_size=500, ax=ax)
        nx.draw(mst, pos, with_labels=True, node_color='skyblue', edge_color='blue', width=2, node_size=700, ax=ax)
        plt.title("MST Graph View")
        st.pyplot(fig)

    else:
        st.error("❗ CSV must contain columns: '기지국', '위도', '경도', '전송속도'")
