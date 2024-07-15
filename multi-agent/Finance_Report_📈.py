import streamlit as st
from io import BytesIO
import os
# from openai import OpenAI
from upload_pdf import SSHManager
from class_fine_tune_function import MarketAnalysis
# with st.sidebar:
#     openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
#     "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
#     "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
#     "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"
st.set_page_config(
    page_title="Stock Report",
    page_icon="📈",
)

uploaded_file=st.sidebar.file_uploader("Choose a file",type='pdf')
if uploaded_file is not None:
    file_content = uploaded_file.read() 
    temp_file_path = os.path.join("/tmp", uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    temp_file = BytesIO(file_content) 

    host = "region-9.autodl.pro"
    port = 53208 
    username = "root"
    password = "4VJLWZNRq4v2"
    ssh_manager = SSHManager(host, port, username, password)
    ssh_manager.connect()
    ssh_manager.run(filename=uploaded_file.name, local_path=temp_file_path)
    ssh_manager.command("python RAG_main/main.py")
    ssh_manager.close()

st.title("💬 Write the Equity Stock Report")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Please input the stock ticker name, for example Microsoft, input 'MSFT'"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# change the path
Agent=MarketAnalysis()
if prompt := st.chat_input():
    # if not openai_api_key:
    #     st.info("Please add your OpenAI API key to continue.")
    #     st.stop()

    # client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    msg = Agent.run_analysis(prompt)
    #if st.session_state.messages[-1]['role']=="saver" & st.session_state.messages[-1]['content']==("TERMINATE" or "Terminate" or "terminate"):

    st.session_state.messages.append({"role": "assistant", "content": "Report saved to report.md"})
    st.chat_message("assistant").write(msg)