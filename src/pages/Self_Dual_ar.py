import time
import requests
import streamlit as st
from PIL import Image

from utils_ar import save_ar_result  # Arabic utility functions
from constant_ar import TOPICS, CANDIDATE_MODEL_LIST  # Arabic constants

BASE_URL = "http://127.0.0.1:8081/"

def clear_chat_history():
    st.session_state.messages = []

def save_message(messages: list):
    if len(messages) > 6:
        messages = messages[:6]
    
    save_ar_result(preset="duel_base", topic=st.session_state.topic, messages=messages, pos_model=st.session_state.pos_model, neg_model=st.session_state.neg_model)

    st.success("تم حفظ المحادثة بنجاح!")

def app():
    import streamlit as st

# تطبيق CSS لتغيير محاذاة النصوص إلى اليمين
    st.markdown("""
    <style>
    /* تنسيق للعنوان */
    .rtl-title {
        text-align: right;
        direction: rtl;
        font-family: 'Arial', sans-serif;
        font-size: 30px;
        font-weight: bold;
        color: #333;
    }

    /* تنسيق للنص العادي */
    .rtl-sub {
        text-align: right;
        direction: rtl;
        font-family: 'Arial', sans-serif;
        font-size: 24px;
        color: black;
    }
    
        .rtl-text {
        text-align: right;
        direction: rtl;
        font-family: 'Arial', sans-serif;
        font-size: 23px;
        font-weight: bold;

        color: black;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
<style>
/* Larger font size for specific elements */
.rtl-text-large {
    text-align: right;
    direction: rtl;
    font-family: 'Arial', sans-serif;
    font-size: 28px; /* Adjust as desired */
    color: black;
}
</style>
""", unsafe_allow_html=True)


# إضافة العنوان باستخدام فئة "rtl-title"
    st.markdown('<div class="rtl-title">مناظرة </div>', unsafe_allow_html=True)

    # إضافة نصوص عادية باستخدام فئة "rtl-text"

    # إضافة المزيد من النصوص العادية

    # st.info("Agent4Debate Self-Duel يشمل الحجة المؤيدة، الحجة المعارضة، دحض المؤيد، دحض المعارض، ملخص المعارض، وملخص المؤيد.")

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.subheader("مناظرة ذاتية")
        st.caption("نظام متعدد للمناظرة يشمل الحجة، الدحض، والملخص.")
        
        prepared_topic = st.selectbox("المواضيع المتاحة", options=TOPICS, help="اختر موضوع النقاش.")
        input_topic = st.text_input("الموضوع", key="input_topic", help="أدخل موضوع النقاش.")
        
        pos_model = st.selectbox("جانب المؤيد", options=CANDIDATE_MODEL_LIST, index=0, help="اختر النموذج لجانب المؤيد", key="pos_model")
        neg_model = st.selectbox("جانب المعارض", options=CANDIDATE_MODEL_LIST, index=0, help="اختر النموذج لجانب المعارض", key="neg_model")
        
        language = st.radio("اللغة", key="language", options=["ar", "en"], index=0)
        
        topic = input_topic if input_topic else prepared_topic
        st.session_state.topic = topic
        
        pos_input = {
            "Language": "ar",
            "Topic": topic,
            "Position": "positive",
            "Model": pos_model
        }
        neg_input = {
            "Language": "ar",
            "Topic": topic,
            "Position": "negative",
            "Model": neg_model
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.button(label="بدء", key="start_button")
        
        col3, col4 = st.columns(2)
        with col3:
            st.button(label="حفظ", key="save_button", on_click=save_message, args=(st.session_state.messages,), help="حفظ النتيجة.")
        with col4:
            st.button(label="إعادة تعيين", key="reset", on_click=clear_chat_history)

    if st.session_state.start_button:
        if len(st.session_state.messages) >= 6:
            st.error("انتهت المناظرة. يُرجى حفظ النتيجة والضغط على زر إعادة التعيين للبدء مجددًا.")
            for message in st.session_state.messages:
                with st.chat_message(
                    message["role"], 
                    avatar=Image.open(f"figures/logo/pro.png" if message["role"] == "user" else "figures/logo/cooon.png")):
                    st.write(message["content"])
            return 

        st.markdown(f'<div class="rtl-sub">الموضوع: {topic}</div>', unsafe_allow_html=True)
        # st.markdown('<div class="rtl-text">بدأت المناظرة</div>', unsafe_allow_html=True)


        # Argument phase
        with st.chat_message("user", avatar=Image.open("figures/logo/pro.png")):
            with st.spinner("حجة المؤيد "):
                pos_argument_response = requests.post(BASE_URL + "v1/argument", json=pos_input).json()
                pos_argument = pos_argument_response["Result"]
                st.markdown(f'<div class="rtl-text">حجة المويد {pos_argument}</div>', unsafe_allow_html=True)
    
                st.session_state.messages.append({"role": "user", "content": pos_argument})

        with st.chat_message("assistant", avatar=Image.open("figures/logo/cooon.png")):
            with st.spinner("حجة المعارض"):
                neg_argument_response = requests.post(BASE_URL + "v1/argument", json=neg_input).json()
                neg_argument = neg_argument_response["Result"]
                st.markdown(f'<div class="rtl-text"> حجة المعارض \n{neg_argument}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": neg_argument})

        # Rebuttal phase
        with st.chat_message("user", avatar=Image.open("figures/logo/pro.png")):
            pos_input.update({
                "PositiveArgument": pos_argument,
                "NegativeArgument": neg_argument,
                "Reference": pos_argument_response["Reference"]
            })
            with st.spinner("Agent4DB -> دحض المؤيد..."):
                pos_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=pos_input).json()
                pos_rebuttal = pos_rebuttal_response["Result"]
                # st.write("### دحض المؤيد\n", pos_rebuttal)
                st.markdown(f'<div class="rtl-text"> دحض المويد \n{pos_rebuttal}</div>', unsafe_allow_html=True)

                st.session_state.messages.append({"role": "user", "content": pos_rebuttal})

        with st.chat_message("assistant", avatar=Image.open("figures/logo/cooon.png")):
            neg_input.update({
                "PositiveArgument": pos_argument,
                "NegativeArgument": neg_argument,
                "PositiveRebuttal": pos_rebuttal,
                "Reference": neg_argument_response["Reference"]
            })
            with st.spinner("Agent4DB -> دحض المعارض..."):
                neg_rebuttal_response = requests.post(BASE_URL + "v1/rebuttal", json=neg_input).json()
                neg_rebuttal = neg_rebuttal_response["Result"]
                st.markdown(f'<div class="rtl-text"> دحض المعارض \n{neg_rebuttal}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": neg_rebuttal})

        # Summary phase
        with st.chat_message("assistant", avatar=Image.open("figures/logo/cooon.png")):
            neg_input.update({
                "PositiveRebuttal": pos_rebuttal,
                "NegativeRebuttal": neg_rebuttal,
                "Reference": neg_rebuttal_response["Reference"]
            })
            with st.spinner("Agent4DB -> ملخص المعارض..."):
                neg_summary_response = requests.post(BASE_URL + "v1/summary", json=neg_input).json()
                neg_summary = neg_summary_response["Result"]
                st.write("### ملخص المعارض\n", neg_summary)
                st.session_state.messages.append({"role": "assistant", "content": neg_summary})

        with st.chat_message("user", avatar=Image.open("figures/logo/pro.png")):
            pos_input.update({
                "PositiveRebuttal": pos_rebuttal,
                "NegativeRebuttal": neg_rebuttal,
                "NegativeSummary": neg_summary,
                "Reference": pos_rebuttal_response["Reference"]
            })
            with st.spinner("Agent4DB -> ملخص المؤيد..."):
                pos_summary_response = requests.post(BASE_URL + "v1/summary", json=pos_input).json()
                pos_summary = pos_summary_response["Result"]
                st.write("### ملخص المؤيد\n", pos_summary)
                st.session_state.messages.append({"role": "user", "content": pos_summary})

        st.warning("انتهت المناظرة. يُرجى حفظ النتيجة والضغط على زر إعادة التعيين للبدء مجددًا.")

if __name__ == "__main__":
    app()
