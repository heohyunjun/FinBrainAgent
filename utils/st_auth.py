import os
import streamlit as st
from dotenv import load_dotenv

def check_token_auth():
    load_dotenv() 

    valid_tokens = os.getenv("VALID_TOKENS", "").split(",")
    token = st.query_params.get("token")

    if token not in valid_tokens:
        st.error("접근 권한이 없습니다.")
        st.stop()

    return token  # 유효한 토큰을 반환할 수도 있음
