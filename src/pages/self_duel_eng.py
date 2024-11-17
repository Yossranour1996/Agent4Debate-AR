import time
import requests
import streamlit as st
from PIL import Image

from utils_eng import save_eng_result
from constant_eng import TOPICS, CANDIDATE_MODEL_LIST

BASE_URL = "http://127.0.0.1:8081/"

def clear_chat_history():
    st.session_state.messages = []

def save_message(messages: list):
    if len(messages) > 6:
        messages = messages[:6]
    
    save_eng_result(preset="duel_base", topic=st.session_state.topic, messages=messages, pos_model=st.session_state.pos_model, neg_model=st.session_state.neg_model)

    st.success("Conversation saved!")

def app():
    st.markdown(
    """
    <style>
    .subsubheader {
        font-size: 18px;
        font-weight: bold;
        color: #333;
    }
    </style>
    """,
    unsafe_allow_html=True
)

    # st.markdown('<p class="subsubheader">This is a Sub-subheader</p>', unsafe_allow_html=True)

    st.header("Debate")
    # st.info("Agent4Debate Self-Duel includes pro argument, con argument, pro rebuttal, con rebuttal, con summary, and pro summary.")

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.subheader("Agent4DB Self-Duel Debater")
        st.caption("Agent4DB: A multi-agent debate system including argument, rebuttal, and summary.")
        
        prepared_topic = st.selectbox("Prepared Topic", options=TOPICS, help="Choose a debate topic.")
        input_topic = st.text_input("Topic", key="input_topic", help="Enter your topic.")
        
        pos_model = st.selectbox("Pro side", options=CANDIDATE_MODEL_LIST, index=0, help="Choose the model for the pro side", key="pos_model")
        neg_model = st.selectbox("Con side", options=CANDIDATE_MODEL_LIST, index=0, help="Choose the model for the con side", key="neg_model")
        
        language = st.radio("Language", key="language", options=["en", "zh"], index=0)
        
        topic = input_topic if input_topic else prepared_topic
        st.session_state.topic = topic
        
        pos_input = {
            "Language": "en",
            "Topic": topic,
            "Position": "positive",
            "Model": pos_model
        }
        neg_input = {
            "Language": "en",
            "Topic": topic,
            "Position": "negative",
            "Model": neg_model
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.button(label="Start", key="start_button")
        
        col3, col4 = st.columns(2)
        with col3:
            st.button(label="Save", key="save_button", on_click=save_message, args=(st.session_state.messages,), help="Save the result.")
        with col4:
            st.button(label="Reset", key="reset", on_click=clear_chat_history)

    if st.session_state.start_button:
        if len(st.session_state.messages) >= 6:
            st.error("Debate is over. Please save the result and click the reset button to start again.")
            for message in st.session_state.messages:
                with st.chat_message(
                    message["role"], 
                    avatar=Image.open(f"figures/logo/pro.png" if message["role"] == "user" else "figures/logo/cooon.png")):
                    st.write(message["content"])
            return 

        st.markdown(f'<p class="subsubheader">Topic: {topic}</p>', unsafe_allow_html=True)
        st.success("Debate start!")

        # Argument phase
        with st.chat_message("user", avatar=Image.open("figures/logo/pro.png")):
            with st.spinner("Agent4DB -> Pro Argument..."):
                pos_argument_response = requests.post(BASE_URL + "v1/argument", json=pos_input).json()
                pos_argument = pos_argument_response["Result"]
                st.markdown(f"### Pro side argument\n{pos_argument}", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "user", "content": pos_argument})

        with st.chat_message("assistant", avatar=Image.open("figures/logo/cooon.png")):
            with st.spinner("Agent4DB -> Con Argument..."):
                neg_argument_response = requests.post(BASE_URL + "v1/argument", json=neg_input).json()
                neg_argument = neg_argument_response["Result"]
                st.markdown(f"### Con side argument\n{neg_argument}", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": neg_argument})

        # Rebuttal phase
        with st.chat_message("user", avatar=Image.open("figures/logo/pro.png")):
            pos_input.update({
                "PositiveArgument": pos_argument,
                "NegativeArgument": neg_argument,
                "Reference": pos_argument_response["Reference"]
            })
            with st.spinner("Agent4DB -> Pro Rebuttal..."):
                pos_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=pos_input).json()
                print("Rebuttal Response:", pos_rebuttal_response)
                pos_rebuttal = pos_rebuttal_response["Result"]
                st.write("### Pro Rebuttal\n", pos_rebuttal)
                st.session_state.messages.append({"role": "user", "content": pos_rebuttal})

        with st.chat_message("assistant", avatar=Image.open("figures/logo/cooon.png")):
            neg_input.update({
                "PositiveArgument": pos_argument,
                "NegativeArgument": neg_argument,
                "PositiveRebuttal": pos_rebuttal,
                "Reference": neg_argument_response["Reference"]
            })
            with st.spinner("Agent4DB -> Con Rebuttal..."):
                neg_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=neg_input).json()
                neg_rebuttal = neg_rebuttal_response["Result"]
                st.write("### Con Rebuttal\n", neg_rebuttal)
                st.session_state.messages.append({"role": "assistant", "content": neg_rebuttal})

        # Summary phase
        with st.chat_message("assistant", avatar=Image.open("figures/logo/cooon.png")):
            neg_input.update({
                "PositiveRebuttal": pos_rebuttal,
                "NegativeRebuttal": neg_rebuttal,
                "Reference": neg_rebuttal_response["Reference"]
            })
            with st.spinner("Agent4DB -> Con Summary..."):
                neg_summary_response = requests.post(BASE_URL + "v1/summary", json=neg_input).json()
                neg_summary = neg_summary_response["Result"]
                st.write("### Con Summary\n", neg_summary)
                st.session_state.messages.append({"role": "assistant", "content": neg_summary})

        with st.chat_message("user", avatar=Image.open("figures/logo/pro.png")):
            pos_input.update({
                "PositiveRebuttal": pos_rebuttal,
                "NegativeRebuttal": neg_rebuttal,
                "NegativeSummary": neg_summary,
                "Reference": pos_rebuttal_response["Reference"]
            })
            with st.spinner("Agent4DB -> Pro Summary..."):
                pos_summary_response = requests.post(BASE_URL + "v1/summary", json=pos_input).json()
                pos_summary = pos_summary_response["Result"]
                st.write("### Pro Summary\n", pos_summary)
                st.session_state.messages.append({"role": "user", "content": pos_summary})

        st.warning("Debate is over. Please save the result and click the reset button to start again.")

if __name__ == "__main__":
    app()
