import os
from datetime import datetime
from typing import Callable, Dict, Literal, Optional, Union

from typing_extensions import Annotated

from autogen import (
    Agent,
    AssistantAgent,
    ConversableAgent,
    GroupChat,
    GroupChatManager,
    UserProxyAgent,
    config_list_from_json,
    register_function,
)
from autogen.agentchat.contrib import agent_builder
from autogen.cache import Cache
from autogen.coding import DockerCommandLineCodeExecutor, LocalCommandLineCodeExecutor

config_list = [
#     {
#     'model' : 'test',
#     'api_key':'ebc76beedf89486382e773d3b4cf0b10',
#     'base_url' : 'https://gpgpt.openai.azure.com/',
#     'api_type' : 'azure',
#     'api_version' : '2024-05-01-preview',
#  }

 {
    'model': 'llama3-8b-8192', #model here is your model name in the LM studio
    'api_key': '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',
    'base_url': "https://api.groq.com/openai/v1",}
 ]

task = (
        f"write a equity stock report for MSFT"

)
print(task)

user_proxy = UserProxyAgent(
    name="Admin",
    system_message="A human admin. Give the task, and send instructions to writer to refine the blog post.",
    code_execution_config=False,
)

planner = AssistantAgent(
    name="Planner",
    system_message="""Planner. Given a task, please determine what information is needed to complete the task.
Please note that don't write any python code. If you want to get the data, such as stock price, company fundemental information, plot stock price graph, please ask the data provider to use the function call to get the data.
""",
    llm_config={"config_list": config_list, "cache_seed": None},
)



writer = AssistantAgent(
    name="Writer",
    llm_config={"config_list": config_list, "cache_seed": None},
    system_message="""Writer. Please write blogs in markdown format (with relevant titles) and put the content in pseudo ```md``` code block. You will write it for a task based on previous chat history. """,
)




def custom_speaker_selection_func(last_speaker: Agent, groupchat: GroupChat):
    """Define a customized speaker selection function.
    A recommended way is to define a transition for each speaker in the groupchat.

    Returns:
        Return an `Agent` class or a string from ['auto', 'manual', 'random', 'round_robin'] to select a default method to use.
    """
    messages = groupchat.messages
    print(groupchat.messages)

    if len(messages) <= 1:
        # first, let the engineer retrieve relevant data
        return planner

    if last_speaker is planner:
        # if the last message is from planner, let the engineer to write code
        return engineer
    elif last_speaker is user_proxy:
        if messages[-1]["content"].strip() != "":
            # If the last message is from user and is not empty, let the writer to continue
            return writer

    elif last_speaker is engineer:
        if "```python" in messages[-1]["content"]:
            # If the last message is a python code block, let the executor to speak
            return code_executor
        else:
            # Otherwise, let the engineer to continue
            return engineer

    elif last_speaker is code_executor:
        if "exitcode: 1" in messages[-1]["content"]:
            # If the last message indicates an error, let the engineer to improve the code
            return engineer
        else:
            # Otherwise, let the writer to speak
            return writer

    elif last_speaker is writer:
        # Always let the user to speak after the writer
        return user_proxy

    else:
        # default to auto speaker selection method
        return "auto"


groupchat = GroupChat(
    agents=[user_proxy, engineer, writer, code_executor, planner],
    messages=[],
    max_round=20,
    speaker_selection_method=custom_speaker_selection_func,
)
manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list, "cache_seed": None})

with Cache.disk(cache_seed=41) as cache:
    groupchat_history_custom = user_proxy.initiate_chat(
        manager,
        message=task,
        cache=cache,
    )