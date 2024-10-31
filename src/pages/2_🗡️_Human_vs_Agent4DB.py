import time
from typing import List

import requests
import streamlit as st
from PIL import Image

from utils import save_zh_result
from constant import TOPICS, CANDIDATE_MODEL_LIST

POS_LOGO="figures/logo/pos.png"
HUMAN_LOGO="figures/logo/human.png"
NEG_LOGO="figures/logo/neg.png"

BASE_URL = "http://127.0.0.1:8081/"

def clear_chat_history():
    st.session_state.human_messages = []
    st.session_state.button_state = False

def save_human_versus_msg(messages: List):
    if len(messages) > 6:
        st.error("the length of history messages is more than 6, please check it.")
    
    if st.session_state.human_position == "正方" or st.session_state.human_position == "position":
        postfix = "pos"
        pos_model = "human"
        if st.session_state.is_baseline:
            pos_model = "baseline"
        neg_model = st.session_state.model
    else:
        postfix = "neg"
        neg_model = "human"
        if st.session_state.is_baseline:
            neg_model = "baseline"
        pos_model = st.session_state.model
    
    if st.session_state.is_baseline:
        preset = "baseline"
    else:
        preset = "human"
        
    save_zh_result(preset = preset, topic=st.session_state.topic, messages=messages, pos_model=pos_model, neg_model=neg_model)
    
    st.success("Save successfully!")
    
st.header("⚔️ Human vs Agent4DB")
st.info("👈 Please input your argument in the chat box.")

if "human_messages" not in st.session_state:
    st.session_state.human_messages = []
if "button_state" not in st.session_state:
    st.session_state.button_state = False
    
with st.sidebar:
    st.subheader("人机对战\nHuman vs Agent4DB")
    prepare_topic = st.selectbox("Prepared Topic", options=TOPICS, help="choose a topic.")
    input_topic = st.text_input("Topic", key = "input_topic", help = "输入辩题")
    bot_model = st.selectbox("Model", key="model", options=CANDIDATE_MODEL_LIST, help="choose a model.")
    is_base_line = st.radio("Baseline Optional", key="is_baseline", options=[True, False], index=1)
    
    st.radio("Human Position", key = "human_position", options=["正方", "反方"], help = "选择人类的持方 Choose the human's position.", index=0)
    st.radio("Language", key = "language", options=["zh", "en"], index=0)
    
    if input_topic is None or len(input_topic) == 0:
            topic = prepare_topic
    else:
        topic = input_topic
    st.session_state.topic = topic
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button(label="Start", key = "start")
    with col2:
        st.button(label="Reset", key = "reset", on_click=clear_chat_history)
    with col3:
        st.button(label="Save", key="save", on_click=save_human_versus_msg, args=(st.session_state.human_messages,), help="save the debate result.")
        
    if st.session_state.start:
        st.session_state.button_state = True
    
st.subheader("⚖️ Topic: " + topic)

if st.session_state.button_state is True:
    st.info("Debate start!")
    # show history messages
    for idx, msg in enumerate(st.session_state.human_messages):
        # st.text(msg["content"])
        if msg["role"] == "user":
            temp_avator = HUMAN_LOGO
        else:
            if idx % 2 == 0:
                temp_avator = POS_LOGO
            else:
                temp_avator = NEG_LOGO
                
        with st.chat_message(msg["role"], avatar=Image.open(temp_avator)):
            st.write(msg["round"] + msg["content"])
            
    if st.session_state.human_position == "正方":
        neg_input_data = {
            "Language": "zh",
            "Topic": topic,
            "Position": "反方",
            "Model": bot_model,
        }
        msg_len = len(st.session_state.human_messages)
        if prompt := st.chat_input("User input"):
            if msg_len == 0:
                # 立论
                round = "### 正方立论\n"
                st.session_state.pos_argument = prompt
                st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
                with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                    st.write(round+prompt)
            
                with st.spinner("Agent4DB -> 反方立论中..."):
                    neg_argument_response = requests.post(BASE_URL + "v1/argument", json=neg_input_data).json()
                    st.session_state.neg_argument = neg_argument_response["Result"]
                    st.session_state.neg_reference = neg_argument_response["Reference"]
                    round = "### 反方立论\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.neg_argument, "round": round})
                    with st.chat_message("assistant", avatar=Image.open(NEG_LOGO)):
                        st.write(round+st.session_state.neg_argument)
                        
            elif msg_len == 2:
                round = "### 正方驳论\n"
                st.session_state.pos_rebuttal = prompt
                st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
                with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                    st.write(round+prompt)
                    
                neg_input_data.update({
                    "PositiveArgument": st.session_state.pos_argument,
                    "NegativeArgument": st.session_state.neg_argument,
                    "PositiveRebuttal": prompt,
                    "Reference": st.session_state.neg_reference,
                })
                with st.spinner("Agent4DB -> 反方驳论中..."):
                    neg_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=neg_input_data).json()
                    st.session_state.neg_rebuttal = neg_rebuttal_response["Result"]
                    st.session_state.neg_reference = neg_rebuttal_response["Reference"]
                    round = "### 反方驳论\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.neg_rebuttal, "round": round})
                    with st.chat_message("assistant", avatar=Image.open(NEG_LOGO)):
                        st.write(round+st.session_state.neg_rebuttal)
            
                neg_input_data.update({
                    "PositiveArgument": st.session_state.pos_argument,
                    "NegativeArgument": st.session_state.neg_argument,
                    "PositiveRebuttal": st.session_state.pos_rebuttal,
                    "NegativeRebuttal": st.session_state.neg_rebuttal,
                    "Reference": st.session_state.neg_reference,
                })
                with st.spinner("Agent4DB -> 反方总结中..."):
                    neg_summary_response = requests.post(BASE_URL + "v1/summary", json=neg_input_data).json()
                    st.session_state.neg_summary = neg_summary_response["Result"]
                    st.session_state.neg_reference = neg_summary_response["Reference"]
                    
                    round = "### 反方总结\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.neg_summary, "round": round})
                    with st.chat_message("assistant", avatar=Image.open(NEG_LOGO)):
                        st.write(round+st.session_state.neg_summary)
                        
            elif msg_len >= 4:
                round = "### 正方总结\n"    
                st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
                with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                    st.write(round+prompt)

            else:
                st.warning("Debate is over! You can save result by the Save button.")
            
    else:
        pos_input_data = {
            "Language": "zh",
            "Topic": topic,
            "Position": "正方",
            "Model": bot_model,
        }
        msg_len = len(st.session_state.human_messages)
        if msg_len == 0:
        # 立论
            with st.spinner("Agent4DB -> 正方立论中..."):
                pos_argument_response = requests.post(BASE_URL + "v1/argument", json=pos_input_data).json()
                st.session_state.pos_argument = pos_argument_response["Result"]
                st.session_state.pos_reference = pos_argument_response["Reference"]
                with st.chat_message("assistant", avatar=Image.open(POS_LOGO)):
                    round = "### 正方立论\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.pos_argument, "round": round})
                    st.write(round+st.session_state.pos_argument)
        elif msg_len == 2:
            pos_input_data.update({
                "PositiveArgument": st.session_state.pos_argument,
                "NegativeArgument": st.session_state.neg_argument,
                "Reference": st.session_state.pos_reference,
            })
            with st.spinner("Agent4DB -> 正方驳论中..."):
                pos_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=pos_input_data).json()
                st.session_state.pos_rebuttal = pos_rebuttal_response["Result"]
                st.session_state.pos_reference = pos_rebuttal_response["Reference"]
                with st.chat_message("assistant", avatar=Image.open(POS_LOGO)):
                    round = "### 正方驳论\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.pos_rebuttal, "round": round})
                    st.write(round+st.session_state.pos_rebuttal)
        elif msg_len >= 6:
            st.warning("Debate is over! You can save result by the Save button.")
                
        if prompt := st.chat_input("User input"):
            if len(st.session_state.human_messages) == 1:
                round = "### 反方立论\n"
                st.session_state.neg_argument = prompt
            elif len(st.session_state.human_messages) == 3:
                round = "### 反方驳论\n"
                st.session_state.neg_rebuttal = prompt
                ## 反方驳论之后直接总结
            elif len(st.session_state.human_messages) == 4:
                round = "### 反方总结\n"
                st.session_state.neg_summary = prompt
            # save the message
            st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
            # show the message
            with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                st.write(round+prompt)
            
            if round == "### 反方总结\n":
                pos_input_data.update({
                    "PositiveArgument": st.session_state.pos_argument,
                    "NegativeArgument": st.session_state.neg_argument,
                    "PositiveRebuttal": st.session_state.pos_rebuttal,
                    "NegativeRebuttal": st.session_state.neg_rebuttal,
                    "NegativeSummary": prompt,
                    "Reference": st.session_state.pos_reference,
                })
                with st.spinner("Agent4DB -> 正方总结中..."):
                    pos_summary_rebuttal_response = requests.post(BASE_URL + "v1/summary", json=pos_input_data).json()
                    st.session_state.pos_summary = pos_summary_rebuttal_response["Result"]
                    st.session_state.pos_reference = pos_summary_rebuttal_response["Reference"]
                    with st.chat_message("assistant", avatar=Image.open(POS_LOGO)):
                        round = "### 正方总结\n"
                        st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.pos_summary, "round": round})
                        st.write(round+st.session_state.pos_summary)
                
            st.rerun()
                    

            