import time

import requests
import streamlit as st
from constant import TOPICS, CANDIDATE_MODEL_LIST

BASE_URL = "http://127.0.0.1:8081/"

def clear_argument():
    st.session_state.argument_inputs = None
    

st.header("🚘 Argument Assistant")

with st.sidebar:
    st.subheader("Agent4DB 立论助手\nArgument Assistant with Agent4DB")
    st.caption("输入辩题和持方，获取立论内容。")
    
    argument_topic = st.text_input("Topic", key="argument_topic", help="输入辩题", value="教师可以/不可以偏爱优等生")
    argument_model = st.selectbox("Model", key="argument_model", options=CANDIDATE_MODEL_LIST, index=0, help="选择模型")
    argument_position = st.radio("Position", key="argument_position", options=["正方", "反方"], index=0)
    argument_language = st.radio("Language", key="argument_language", options=["zh", "en"], index=0, help="选择语言")
    
    assert argument_language == "zh", "目前只支持中文"
    assert argument_topic is not None and len(argument_topic) > 0, "Topic should not be None"
    
    argument_inputs = {
        "Language": argument_language,
        "Topic": argument_topic,
        "Position": argument_position,
        "Model": argument_model
    }
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button(label="Start", key="start_argument_button")
    with col2:
        st.button(label="Reset", key="argument_reset", on_click = clear_argument)
    with col3:
        st.button(label = "Save", key="argument_save")
    
if st.session_state.start_argument_button:
    st.subheader("Argument Topic: " + argument_topic)
    st.subheader("Position: "+argument_position)
    st.info("Argument Assistant is running... Do not close the page.")
    
    with st.spinner("Argument Assistant is running..."):
        response = requests.post(BASE_URL + "v1/argument", json=argument_inputs).json()
        st.write("### Result\n", response.get("Result"))
        st.write("### Reference\n", response.get("Reference"))
        st.success("Argument Assistant is finished!")
        
        