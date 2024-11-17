import time
from typing import List
import requests
import streamlit as st
from PIL import Image
from utils_ar import save_ar_result  # Updated utils for Arabic
from constant_ar import TOPICS, CANDIDATE_MODEL_LIST  # Updated constants for Arabic

POS_LOGO = "figures/logo/pos.png"
HUMAN_LOGO = "figures/logo/human.png"
NEG_LOGO = "figures/logo/neg.png"

BASE_URL = "http://127.0.0.1:8081/"

def clear_chat_history():
    st.session_state.human_messages = []
    st.session_state.button_state = False

def save_human_versus_msg(messages: List):
    if len(messages) > 6:
        st.error("عدد الرسائل في المحفوظات أكثر من 6، يرجى التحقق.")
    
    if st.session_state.human_position in ["مؤيد", "positive"]:
        pos_model = "human"
        neg_model = st.session_state.model
    else:
        neg_model = "human"
        pos_model = st.session_state.model

    preset = "baseline" if st.session_state.is_baseline else "human"
    save_ar_result(preset=preset, topic=st.session_state.topic, messages=messages, pos_model=pos_model, neg_model=neg_model)
    st.success("تم الحفظ بنجاح!")

# Initialize Streamlit UI
st.header("⚔️ المواجهة بين الإنسان والوكيل الذكي Agent4DB")
st.info("👈 يرجى إدخال حجتك في مربع الدردشة.")

if "human_messages" not in st.session_state:
    st.session_state.human_messages = []
if "button_state" not in st.session_state:
    st.session_state.button_state = False

with st.sidebar:
    st.subheader("المواجهة بين الإنسان و Agent4DB")
    prepare_topic = st.selectbox("المواضيع المتاحة", options=TOPICS, help="اختر موضوعاً.")
    input_topic = st.text_input("موضوع النقاش", key="input_topic", help="أدخل موضوع النقاش.")
    bot_model = st.selectbox("النموذج", key="model", options=CANDIDATE_MODEL_LIST, help="اختر نموذجاً.")
    is_base_line = st.radio("اختيار القاعدة الأساسية", key="is_baseline", options=[True, False], index=1)
    
    st.radio("موقف الإنسان", key="human_position", options=["مؤيد", "معارض", "positive", "negative"], help="اختر موقف الإنسان.")
    st.radio("اللغة", key="language", options=["ar", "en"], index=0)

    topic = input_topic if input_topic else prepare_topic
    st.session_state.topic = topic

    col1, col2, col3 = st.columns(3)
    with col1:
        st.button(label="بدء", key="start")
    with col2:
        st.button(label="إعادة تعيين", key="reset", on_click=clear_chat_history)
    with col3:
        st.button(label="حفظ", key="save", on_click=save_human_versus_msg, args=(st.session_state.human_messages,), help="حفظ نتيجة النقاش.")

    if st.session_state.start:
        st.session_state.button_state = True

st.subheader(f"⚖️ موضوع النقاش: {topic}")

ARGUMENT_LABEL = "حجة المؤيد" if st.session_state.language == "ar" else "Pro Argument"
REBUTTAL_LABEL = "دحض المؤيد" if st.session_state.language == "ar" else "Pro Rebuttal"
SUMMARY_LABEL = "ملخص المؤيد" if st.session_state.language == "ar" else "Pro Summary"
NEG_POSITION = "معارض" if st.session_state.language == "ar" else "negative"
POS_POSITION = "مؤيد" if st.session_state.language == "ar" else "positive"

if st.session_state.button_state:
    st.info("النقاش بدأ!")
    for idx, msg in enumerate(st.session_state.human_messages):
        temp_avatar = HUMAN_LOGO if msg["role"] == "user" else (POS_LOGO if idx % 2 == 0 else NEG_LOGO)
        with st.chat_message(msg["role"], avatar=Image.open(temp_avatar)):
            st.write(msg["round"] + msg["content"])

    if st.session_state.human_position in ["مؤيد", "positive"]:
        neg_input_data = {
            "Language": st.session_state.language,
            "Topic": topic,
            "Position": NEG_POSITION,
            "Model": bot_model,
        }
        msg_len = len(st.session_state.human_messages)
        if prompt := st.chat_input("إدخال المستخدم"):
            if msg_len == 0:
                round = f"### {ARGUMENT_LABEL}\n"
                st.session_state.pos_argument = prompt
                st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
                with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                    st.write(round + prompt)
                
                with st.spinner(f"Agent4DB -> {NEG_POSITION} حجة..."):
                    neg_argument_response = requests.post(BASE_URL + "v1/argument", json=neg_input_data).json()
                    st.session_state.neg_argument = neg_argument_response["Result"]
                    st.session_state.neg_reference = neg_argument_response["Reference"]
                    round = f"### حجة {NEG_POSITION}\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.neg_argument, "round": round})
                    with st.chat_message("assistant", avatar=Image.open(NEG_LOGO)):
                        st.write(round + st.session_state.neg_argument)

            elif msg_len == 2:
                round = f"### {REBUTTAL_LABEL}\n"
                st.session_state.pos_rebuttal = prompt
                st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
                with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                    st.write(round + prompt)
                    
                neg_input_data.update({
                    "PositiveArgument": st.session_state.pos_argument,
                    "NegativeArgument": st.session_state.neg_argument,
                    "PositiveRebuttal": prompt,
                    "Reference": st.session_state.neg_reference,
                })
                with st.spinner(f"Agent4DB -> دحض {NEG_POSITION}..."):
                    neg_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=neg_input_data).json()
                    st.session_state.neg_rebuttal = neg_rebuttal_response["Result"]
                    st.session_state.neg_reference = neg_rebuttal_response["Reference"]
                    round = f"### دحض {NEG_POSITION}\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.neg_rebuttal, "round": round})
                    with st.chat_message("assistant", avatar=Image.open(NEG_LOGO)):
                        st.write(round + st.session_state.neg_rebuttal)
            
                neg_input_data.update({
                    "PositiveArgument": st.session_state.pos_argument,
                    "NegativeArgument": st.session_state.neg_argument,
                    "PositiveRebuttal": st.session_state.pos_rebuttal,
                    "NegativeRebuttal": st.session_state.neg_rebuttal,
                    "Reference": st.session_state.neg_reference,
                })
                with st.spinner(f"Agent4DB -> ملخص {NEG_POSITION}..."):
                    neg_summary_response = requests.post(BASE_URL + "v1/summary", json=neg_input_data).json()
                    st.session_state.neg_summary = neg_summary_response["Result"]
                    st.session_state.neg_reference = neg_summary_response["Reference"]
                    
                    round = f"### ملخص {NEG_POSITION}\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.neg_summary, "round": round})
                    with st.chat_message("assistant", avatar=Image.open(NEG_LOGO)):
                        st.write(round + st.session_state.neg_summary)
                        
            elif msg_len >= 4:
                round = f"### {SUMMARY_LABEL}\n"    
                st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
                with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                    st.write(round + prompt)

            else:
                st.warning("تم انتهاء النقاش! يمكنك حفظ النتيجة باستخدام زر الحفظ.")
    else:
        pos_input_data = {
            "Language": st.session_state.language,
            "Topic": topic,
            "Position": POS_POSITION,
            "Model": bot_model,
        }
        msg_len = len(st.session_state.human_messages)
        if msg_len == 0:
            with st.spinner(f"Agent4DB -> {POS_POSITION} حجة..."):
                pos_argument_response = requests.post(BASE_URL + "v1/argument", json=pos_input_data).json()
                st.session_state.pos_argument = pos_argument_response["Result"]
                st.session_state.pos_reference = pos_argument_response["Reference"]
                with st.chat_message("assistant", avatar=Image.open(POS_LOGO)):
                    round = f"### {ARGUMENT_LABEL}\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.pos_argument, "round": round})
                    st.write(round + st.session_state.pos_argument)
        elif msg_len == 2:
            pos_input_data.update({
                "PositiveArgument": st.session_state.pos_argument,
                "NegativeArgument": st.session_state.neg_argument,
                "Reference": st.session_state.pos_reference,
            })
            with st.spinner(f"Agent4DB -> {REBUTTAL_LABEL}..."):
                pos_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=pos_input_data).json()
                st.session_state.pos_rebuttal = pos_rebuttal_response["Result"]
                st.session_state.pos_reference = pos_rebuttal_response["Reference"]
                with st.chat_message("assistant", avatar=Image.open(POS_LOGO)):
                    round = f"### {REBUTTAL_LABEL}\n"
                    st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.pos_rebuttal, "round": round})
                    st.write(round + st.session_state.pos_rebuttal)
        elif msg_len >= 6:
            st.warning("تم انتهاء النقاش! يمكنك حفظ النتيجة باستخدام زر الحفظ.")

        if prompt := st.chat_input("إدخال المستخدم"):
            if len(st.session_state.human_messages) == 1:
                round = f"### حجة {NEG_POSITION}\n"
                st.session_state.neg_argument = prompt
            elif len(st.session_state.human_messages) == 3:
                round = f"### دحض {NEG_POSITION}\n"
                st.session_state.neg_rebuttal = prompt
            elif len(st.session_state.human_messages) == 4:
                round = f"### ملخص {NEG_POSITION}\n"
                st.session_state.neg_summary = prompt

            st.session_state.human_messages.append({"role": "user", "content": prompt, "round": round})
            with st.chat_message("user", avatar=Image.open(HUMAN_LOGO)):
                st.write(round + prompt)
            
            if round == f"### ملخص {NEG_POSITION}\n":
                pos_input_data.update({
                    "PositiveArgument": st.session_state.pos_argument,
                    "NegativeArgument": st.session_state.neg_argument,
                    "PositiveRebuttal": st.session_state.pos_rebuttal,
                    "NegativeRebuttal": st.session_state.neg_rebuttal,
                    "NegativeSummary": prompt,
                    "Reference": st.session_state.pos_reference,
                })
                with st.spinner(f"Agent4DB -> {SUMMARY_LABEL}..."):
                    pos_summary_rebuttal_response = requests.post(BASE_URL + "v1/summary", json=pos_input_data).json()
                    st.session_state.pos_summary = pos_summary_rebuttal_response["Result"]
                    st.session_state.pos_reference = pos_summary_rebuttal_response["Reference"]
                    with st.chat_message("assistant", avatar=Image.open(POS_LOGO)):
                        round = f"### {SUMMARY_LABEL}\n"
                        st.session_state.human_messages.append({"role": "assistant", "content": st.session_state.pos_summary, "round": round})
                        st.write(round + st.session_state.pos_summary)
            
            st.rerun()
