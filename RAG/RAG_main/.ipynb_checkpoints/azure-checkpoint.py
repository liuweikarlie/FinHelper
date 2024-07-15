import getpass
import os

os.environ["AZURE_OPENAI_API_KEY"] = "ebc76beedf89486382e773d3b4cf0b10"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://gpgpt.openai.azure.com/"

from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(
    azure_deployment="test",
    api_version="2024-05-01-preview",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
print(ai_msg)