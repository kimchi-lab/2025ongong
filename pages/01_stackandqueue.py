import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="스택과 큐 시각화", layout="centered")
st.title("📚 Stack & Queue 시각화")

# 초기 상태 설정
if "stack" not in st.session_state:
    st.session_state.stack = []
if "queue" not in st.session_state:
    st.session_state.queue = []

# UI
st.sidebar.header("📥 조작 패널")
data_structure = st.sidebar.radio("자료구조 선택", ("Stack", "Queue"))
element = st.sidebar.text_input("추가할 값", key="element")

if st.sidebar.button("➕ 추가"):
    if element:
        if data_structure == "Stack":
            st.session_state.stack.append(element)
        else:
            st.session_state.queue.append(element)

if st.sidebar.button("➖ 삭제"):
    if data_structure == "Stack" and st.session_state.stack:
        st.session_state.stack.pop()
    elif data_structure == "Queue" and st.session_state.queue:
        st.session_state.queue.pop(0)

# 시각화 함수
def visualize_stack(stack):
    fig = go.Figure()
    height = len(stack)
    for i, val in enumerate(reversed(stack)):
        fig.add_shape(
            type="rect",
            x0=0, y0=i, x1=1, y1=i+1,
            line=dict(color="black"),
            fillcolor="skyblue"
        )
        fig.add_trace(go.Scatter(
            x=[0.5],
            y=[i + 0.5],
            text=[val],
            mode="text",
            textfont=dict(size=18)
        ))
    fig.update_layout(
        height=max(300, 60 * height),
        width=300,
        title="Stack (LIFO)",
        xaxis=dict(showticklabels=False, range=[0, 1]),
        yaxis=dict(showticklabels=False, range=[0, height]),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    return fig

def visualize_queue(queue):
    fig = go.Figure()
    width = len(queue)
    for i, val in enumerate(queue):
        fig.add_shape(
            type="rect",
            x0=i, y0=0, x1=i+1, y1=1,
            line=dict(color="black"),
            fillcolor="lightgreen"
        )
        fig.add_trace(go.Scatter(
            x=[i + 0.5],
            y=[0.5],
            text=[val],
            mode="text",
            textfont=dict(size=18)
        ))
    fig.update_layout(
        height=200,
        width=max(300, 100 * width),
        title="Queue (FIFO)",
        xaxis=dict(showticklabels=False, range=[0, width]),
        yaxis=dict(showticklabels=False, range=[0, 1]),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    return fig

# 시각화 출력
if data_structure == "Stack":
    st.plotly_chart(visualize_stack(st.session_state.stack), use_container_width=True)
else:
    st.plotly_chart(visualize_queue(st.session_state.queue), use_container_width=True)

