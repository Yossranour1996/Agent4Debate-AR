import time

import requests
import streamlit as st
from PIL import Image

from utils import save_zh_result
from constant import TOPICS, CANDIDATE_MODEL_LIST

BASE_URL = "http://127.0.0.1:8081/"

def clear_chat_history():
    st.session_state.messages = []

def save_message(messages: list):
    if len(messages) > 6:
        messages = messages[:6]
    
    save_zh_result(preset="duel_base", topic = st.session_state.topic, messages = messages, pos_model=st.session_state.pos_model, neg_model=st.session_state.neg_model)

    st.success("对话已保存！")
    
def app():
    st.header(":crossed_swords: Self Duel. 自我对战")
    st.info("Agent4Debate 自我对战，包括正方立论、反方立论、正方驳论、反方驳论、反方总结、正方总结。")
    # 初始化会话状态
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.subheader("Agent4DB 自我对战\nSelf-Duel Debater with Agent4DB")
        st.caption("Agent4DB: A multi-agent system of debate process, include argument, rebuttal and summary agent.")
        prepare_topic = st.selectbox("Prepared Topic", options=TOPICS, help="choose a topic.")
        input_topic = st.text_input("Topic", key="input_topic", help="输入辩题")
        pos_model = st.selectbox("Pro side", options=CANDIDATE_MODEL_LIST, index=0, help="选择正方模型", key="pos_model")
        neg_model = st.selectbox("Con side", options=CANDIDATE_MODEL_LIST, index=0, help="选择反方模型", key="neg_model")
        
        language = st.radio("Language", key = "language", options=["zh", "en"], index=0)
        
        if input_topic is None or len(input_topic) == 0:
            topic = prepare_topic
        else:
            topic = input_topic
        st.session_state.topic = topic    
        
        assert language == "zh", "目前只支持中文对战"
        assert topic is not None and len(topic) > 0, "Topic should not be None"
        
        pos_input = {
            "Language": "zh",
            "Topic": topic,
            "Position": "正方",
            "Model": pos_model
        }
        neg_input = {
            "Language": "zh",
            "Topic": topic,
            "Position": "反方",
            "Model": neg_model,
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.button(label="Start", key="start_button")
        # with col2:
        #     st.button(label="Show Messages", key="show_messages")
        
        col3, col4 = st.columns(2)
        with col3:
            st.button(label = "Save", key="save_button", on_click=save_message, args=(st.session_state.messages,), help="save the result.")
        with col4:
            st.button(label="Reset", key="reset", on_click=clear_chat_history)
            
    if st.session_state.start_button:
        if len(st.session_state.messages) >= 6:
            st.error("对话已结束，请保存结果然后点击重置按钮重新开始")
            st.exception("The debate is over. Please save result and click the reset button to start again.")
            # 显示历史消息
            for message in st.session_state.messages:
                with st.chat_message(
                    message["role"], 
                    avatar=Image.open(f"figures/logo/pos.png" if message["role"] == "user" else "figures/logo/neg.png")):
                    st.write(message["content"]
                )
            return 
        
        st.subheader("⚖️ Topic: " + topic)
        st.success("Agent4DB 自我对战. *目前只支持中文.*")
        st.info("辩论开始！请等待信息生成，不要关闭页面！\n Debate start! Please wait for the agent to generate the message, do not close the pages.")

        # argument
        with st.chat_message("user", avatar=Image.open("figures/logo/pos.png")):
            with st.spinner("Ageng4DB -> 正方立论中..."):
                pos_argument_response = requests.post(BASE_URL + "v1/argument", json=pos_input).json()
                pos_argument = pos_argument_response["Result"]
                st.write("### 正方立论\n", pos_argument)
                st.session_state.messages.append({"role": "user", "content": pos_argument})
                    
        with st.chat_message("assistant", avatar=Image.open("figures/logo/neg.png")):
            with st.spinner("Agent4DB -> 反方立论中..."):
                neg_argument_response = requests.post(BASE_URL + "v1/argument", json=neg_input).json()
                neg_argument = neg_argument_response["Result"]
                st.write("### 反方立论\n", neg_argument)
                st.session_state.messages.append({"role": "assistant", "content": neg_argument})
        
        # rebuttal  
        with st.chat_message("user", avatar=Image.open("figures/logo/pos.png")):
            pos_input.update(
                {
                    "PositiveArgument": pos_argument,
                    "NegativeArgument": neg_argument,
                    "Reference": pos_argument_response["Reference"]
                }
            )
            with st.spinner("Agent4DB -> 正方驳论中..."):
                pos_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=pos_input).json()
                pos_rebuttal = pos_rebuttal_response["Result"]
                st.write("### 正方驳论\n", pos_rebuttal)
                st.session_state.messages.append({"role": "user", "content": pos_rebuttal})
        
        with st.chat_message("assistant", avatar=Image.open("figures/logo/neg.png")):
            neg_input.update(
                {
                    "PositiveArgument": pos_argument,
                    "NegativeArgument": neg_argument,
                    "PositiveRebuttal": pos_rebuttal,
                    "Reference": neg_argument_response["Reference"]
                }
            )
            with st.spinner("Agent4DB -> 反方驳论中..."):
                neg_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=neg_input).json()
                neg_rebuttal = neg_rebuttal_response["Result"]
                st.write("### 反方驳论\n", neg_rebuttal)
                st.session_state.messages.append({"role": "assistant", "content": neg_rebuttal})
        
        # summary
        with st.chat_message("assistant", avatar=Image.open("figures/logo/neg.png")):
            neg_input.update(
                {
                    "PositiveRebuttal": pos_rebuttal,
                    "NegativeRebuttal": neg_rebuttal,
                    "Reference": neg_rebuttal_response["Reference"]
                }
            )
            with st.spinner("Agent4DB -> 反方总结中..."):
                neg_summary_response = requests.post(BASE_URL + "v1/summary", json=neg_input).json()
                neg_summary = neg_summary_response["Result"]
                st.write("### 反方总结\n", neg_summary)
                st.session_state.messages.append({"role": "assistant", "content": neg_summary})
            
        with st.chat_message("user", avatar=Image.open("figures/logo/pos.png")):
            pos_input.update(
                {
                    "PositiveRebuttal": pos_rebuttal,
                    "NegativeRebuttal": neg_rebuttal,
                    "NegativeSummary": neg_summary,
                    "Reference": pos_rebuttal_response["Reference"]
                }
            )
            with st.spinner("Agent4DB -> 正方总结中..."):
                pos_summary_response = requests.post(BASE_URL + "v1/summary", json=pos_input).json()
                pos_summary = pos_summary_response["Result"]
                st.write("### 正方总结\n", pos_summary)
                st.session_state.messages.append({"role": "user", "content": pos_summary})
                
        st.warning("对话已结束，请保存结果然后点击重置按钮重新开始")
if __name__ == "__main__":
    app()