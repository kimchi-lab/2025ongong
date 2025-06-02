import streamlit as st

st.set_page_config(page_title="MBTI 분석기", layout="centered")

st.title("🧠 나의 MBTI 분석기")
st.markdown("당신의 성격을 간단한 설문을 통해 분석해보세요!")

# 질문 세트 정의
questions = {
    "EI": [
        ("사람들과 어울리는 것이 에너지를 준다.", 1),
        ("혼자 있는 시간이 더 편안하다.", -1)
    ],
    "SN": [
        ("사실에 집중하고 실용적인 것이 좋다.", 1),
        ("상상하고 아이디어를 떠올리는 것이 즐겁다.", -1)
    ],
    "TF": [
        ("결정할 때 논리와 사실을 우선시한다.", 1),
        ("결정할 때 감정과 상황을 고려한다.", -1)
    ],
    "JP": [
        ("계획적으로 일하는 것을 선호한다.", 1),
        ("즉흥적으로 유연하게 일하는 것이 좋다.", -1)
    ]
}

# 사용자 응답 수집
st.header("🔍 질문에 응답해주세요")

scores = {"EI": 0, "SN": 0, "TF": 0, "JP": 0}
for axis, qlist in questions.items():
    for q, weight in qlist:
        response = st.radio(q, ["그렇다", "보통", "아니다"], key=q)
        if response == "그렇다":
            scores[axis] += weight
        elif response == "아니다":
            scores[axis] -= weight

# 결과 분석
def get_mbti(scores):
    mbti = ""
    mbti += "E" if scores["EI"] > 0 else "I"
    mbti += "S" if scores["SN"] > 0 else "N"
    mbti += "T" if scores["TF"] > 0 else "F"
    mbti += "J" if scores["JP"] > 0 else "P"
    return mbti

# 결과 출력
if st.button("MBTI 결과 분석하기"):
    mbti_result = get_mbti(scores)
    st.subheader(f"🎯 당신의 MBTI는 **{mbti_result}**입니다!")

    descriptions = {
        "INTJ": "전략적인 사고와 미래 계획에 능한 혁신가.",
        "ENTP": "창의적이고 토론을 좋아하는 발명가.",
        "INFJ": "통찰력 있고 조화로운 비전을 가진 조언자.",
        "ESFP": "활발하고 감각적인 분위기 메이커.",
        # 생략 가능. 필요한 유형만 추가 가능.
    }
    st.markdown("**성격 요약:**")
    st.info(descriptions.get(mbti_result, "아직 등록되지 않은 MBTI 유형입니다."))

    st.markdown("---")
    st.caption("⚠️ 이 분석은 간단한 테스트이며 공식 MBTI 검사와는 다를 수 있습니다.")
