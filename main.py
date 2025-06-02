import streamlit as st
st.title('나의첫웹서비스만들기!')
name = st.text_input(' 이름을입력하세요:')
st.selectbox('좋아하는음식을선택해주요 :', ['망고빙수', '아몬드봉봉'])
if st.button('인사말 생성'):
   st.write(name + '님 당신이 좋아하는음식은 '+ menu +  '이군요?저도좋아요')
