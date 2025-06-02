import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="스택과 큐 시각화", layout="centered")
st.title("📚 스택과 큐 (Stack & Queue) 시각화")

st.markdown("""
## 🧱 자료구조 소개
**스택(Stack)**: 후입선출(LIFO)의 구조입니다. 마지막에 들어온 데이터가 먼저 나갑니다.  
**큐(Queue)**: 선입선출(FIFO)의 구조입니다. 먼저 들어온 데이터가 먼저 나갑니다.
""")

# 데이터 초기화
if "stack" not in st.session_state:
    st.session_state.stack = []

if "queue" not in st.session_state:
    st.session_state.queue = []

# 데이터 조작 UI
st.sidebar.header("📥 자료 추가/삭제")
selected_ds = st.sidebar.radio("자료구조 선택", ("Stack", "Queue"))

input_val = st.sidebar.text_input("추가할 값", "")

if st.sidebar.button("➕ 추가"):
    if input_val:
        if selected_ds == "Stack":
            st.session_state.stack.append(input_val)
        else:
            st.session_state.queue.append(input_val)

if st.sidebar.button("➖ 삭제"):
    if selected_ds == "Stack":
        if st.session_state.stack:
            st.session_state.stack.pop()
    else:
        if st.session_state.queue:
            st.session_state.queue.pop(0)

# 시각화 함수
def draw_structure(structure, title):
    fig = go.Figure()

    for i, val in enumerate(reversed(structure)):
        fig.add_shape(
            type="rect",
            x0=0, x1=1,
            y0=i, y1=i+1,
            line=dict(color="RoyalBlue"),
            fillcolor="LightSkyBlue"
        )
        fig.add_trace(go.Scatter(
            x=[0.5],
            y=[i + 0.5],
            text=[val],
            mode="text",
            textfont=dict(size=20)
        ))

    fig.update_layout(
        height=400,
        width=200,
        title=title,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        margin=dict(t=50, l=10, r=10, b=10)
    )
    return fig

# 출력
if selected_ds == "Stack":
    st.subheader("🧱 Stack 시각화")
    fig = draw_structure(st.session_state.stack, "스택 구조 (LIFO)")
    st.plotly_chart(fig)
else:
    st.subheader("🧱 Queue 시각화")
    fig = draw_structure(st.session_state.queue, "큐 구조 (FIFO)")
    st.plotly_chart(fig)
