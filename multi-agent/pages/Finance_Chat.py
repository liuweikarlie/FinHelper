import streamlit as st
# from openai import OpenAI
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_agent_doc import qna

st.set_page_config(
    page_title="Finance Chat",
    page_icon="👋",
)


st.title("💬 Finance Q&A")

if "messages1" not in st.session_state:
    st.session_state["messages1"] = [{"role": "assistant", "content": "You can input anything you want to ask "}]

for msg in st.session_state.messages1:
    st.chat_message(msg["role"]).write(msg["content"])

# change the path
agent=qna()
if prompt := st.chat_input():


    st.session_state.messages1.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    st_callback = StreamlitCallbackHandler(st.container())
    response=agent.run(prompt,st_callback)
    st.write(response)

    # st.write(response['output'])

    st.session_state.messages1.append({"role": "assistant", "content": "DONE"})
    st.chat_message("assistant").write(msg)



