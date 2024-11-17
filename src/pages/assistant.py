import time
import requests
import streamlit as st
from constant_eng import TOPICS, CANDIDATE_MODEL_LIST

BASE_URL = "http://127.0.0.1:8081/"

def clear_argument():
    st.session_state.argument_inputs = None

st.header("🚘 Argument Assistant")

with st.sidebar:
    st.subheader("argument Assistant with Agent4DB")
    st.caption("(Input topic and position to get arguments)")

    # Input form for the debate topic, model, position, and language
    argument_topic = st.text_input("Topic", key="argument_topic", help="输入辩题 (Enter the debate topic)", value="教师可以/不可以偏爱优等生")
    argument_model = st.selectbox("Model", key="argument_model", options=CANDIDATE_MODEL_LIST, index=0, help="选择模型 (Choose a model)")
    argument_position = st.radio("Position", key="argument_position", options=["正方", "反方", "positive", "negative"], index=0)
    argument_language = st.radio("Language", key="argument_language", options=["zh", "en"], index=0, help="选择语言 (Choose language)")

    # Ensure topic is provided
    assert argument_topic is not None and len(argument_topic) > 0, "Topic should not be None"

    # Input dictionary for the request
    argument_inputs = {
        "Language": argument_language,
        "Topic": argument_topic,
        "Position": argument_position,
        "Model": argument_model
    }

    # Sidebar buttons to start, reset, or save the argument
    col1, col2, col3 = st.columns(3)
    with col1:
        start_button = st.button(label="Start", key="start_argument_button")
    with col2:
        st.button(label="Reset", key="argument_reset", on_click=clear_argument)
    with col3:
        st.button(label="Save", key="argument_save")

# Main body content when 'Start' button is clicked
if start_button:
    st.subheader(f"Argument Topic: {argument_topic}")
    st.subheader(f"Position: {argument_position}")
    st.info("Argument Assistant is running... Do not close the page.")

    with st.spinner("Argument Assistant is running..."):
        # Sending the request to generate an argument
        response = requests.post(BASE_URL + "v1/argument", json=argument_inputs).json()

        # Displaying the result and references
        st.write("### Result\n", response.get("Result", "No result returned"))
        st.write("### Reference\n", response.get("Reference", "No references returned"))
        st.success("Argument Assistant is finished!")
