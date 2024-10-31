import streamlit as st

# with st.sidebar:
#     topic = st.text_input("Topic", type="default", key="topic")

st.set_page_config(page_title="Debate Arena", page_icon=":robot_face:", layout="wide")

st.write("# Welcome to Competitive Debate Arena! :wave:")

st.sidebar.success("Please choose a page. 👆")

st.sidebar.markdown(
    """
    ## 自我对战
    *Self Duel* 
    
    Agent4DB在指定辩题下分别持正方与反方，进行自我对战。
    ## 人机对战
    *Human vs Agent4Debate*
    
    人类与Agent4Debate对战。
    ## 立论助手
    *Constructive Argument Assistant*
    
    输入给定的辩题和持方，生成立论。"""
)
st.markdown(
    """
    Debate Arena is a platform for debating with AI agents. \\
    :point_left: Choose a page from side bar. 从侧边栏选择一个页面，目前支持自我对战，人机对战，立论助手。

    ## Competitive Debate
    """
)

st.image("figures/competitive_debate.png", caption="Competitive Debate")

st.markdown("## Framework")
st.image("figures/framework.png", width=1000, caption="Agent4DB Framework")
