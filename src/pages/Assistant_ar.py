import time
import requests
import streamlit as st
from constant_ar import TOPICS, CANDIDATE_MODEL_LIST

BASE_URL = "http://127.0.0.1:8081/"

def clear_argument():
    st.session_state.argument_inputs = None

st.header("🚘 مساعد بناء الحجة")

with st.sidebar:
    st.subheader("مساعد Agent4DB لبناء الحجة")
    st.caption("أدخل موضوع النقاش والجانب الذي تدعمه للحصول على محتوى الحجة.")

    # Input form for the debate topic, model, position, and language
    argument_topic = st.text_input("الموضوع", key="argument_topic", help="أدخل موضوع النقاش", value="ينبغي للمعلم أن يفضل الطلاب المتفوقين / لا ينبغي أن يفضلهم")
    argument_model = st.selectbox("النموذج", key="argument_model", options=CANDIDATE_MODEL_LIST, index=0, help="اختر النموذج")
    argument_position = st.radio("الجانب", key="argument_position", options=["مؤيد", "معارض"], index=0)
    argument_language = st.radio("اللغة", key="argument_language", options=["ar", "en"], index=0, help="اختر اللغة")

    # Ensure Arabic is the default language
    assert argument_language == "ar", "حاليًا، اللغة العربية فقط مدعومة"
    assert argument_topic is not None and len(argument_topic) > 0, "يجب ألا يكون موضوع النقاش فارغًا"
    
    # Prepare argument inputs for the API request
    argument_inputs = {
        "Language": argument_language,
        "Topic": argument_topic,
        "Position": argument_position,
        "Model": argument_model
    }

    # Sidebar buttons to start, reset, or save the argument
    col1, col2, col3 = st.columns(3)
    with col1:
        start_button = st.button(label="ابدأ", key="start_argument_button")
    with col2:
        st.button(label="إعادة تعيين", key="argument_reset", on_click=clear_argument)
    with col3:
        st.button(label="حفظ", key="argument_save")

# Main body content when 'Start' button is clicked
if start_button:
    st.subheader(f"موضوع الحجة: {argument_topic}")
    st.subheader(f"الجانب: {argument_position}")
    st.info("مساعد بناء الحجة قيد التشغيل... يرجى عدم إغلاق الصفحة.")

    with st.spinner("مساعد بناء الحجة قيد التشغيل..."):
        # Sending the request to generate an argument
        response = requests.post(BASE_URL + "v1/argument", json=argument_inputs).json()

        # Displaying the result and references
        st.write("### النتيجة\n", response.get("Result", "لم يتم إرجاع أي نتيجة"))
        st.write("### المراجع\n", response.get("Reference", "لم يتم إرجاع أي مراجع"))
        st.success("تم الانتهاء من مساعد بناء الحجة!")
