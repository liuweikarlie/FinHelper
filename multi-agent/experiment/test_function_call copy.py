from IPython.display import Image, display
from datetime import datetime
import autogen
from autogen.coding import LocalCommandLineCodeExecutor
import os
import time
from autogen.cache import Cache

import pandas as pd
import yfinance as yf
from matplotlib import pyplot as plt
from typing import Annotated, List, Tuple
from pandas import DateOffset
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests
import json
import akshare as ak

api_key="LS5RN88HLIZU7NOH"

config_list = [

    {
    'model': 'llama3-70b-8192', #model here is your model name in the LM studio
    'api_key': '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',
    'base_url': "https://api.groq.com/openai/v1",
    }

#         {
#     'model' : 'test2',
#     'api_key':'ebc76beedf89486382e773d3b4cf0b10',
#     'base_url' : 'https://gpgpt.openai.azure.com/',
#     'api_type' : 'azure',
#     'api_version' : '2024-05-01-preview',
#  }

]

config_list = config_list
llm_config={
       
        "config_list": config_list,
        "timeout": 120,
        "temperature": 0.0, 

    }

data_provider = autogen.AssistantAgent(
    name="Data Provider",
    system_message="You are a Data Provider. Your task is to provide charts and necessary market information and send the data back to agent who need it .For coding tasks, only use the functions you have been provided with. Don't create code on your own. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    )

writer=autogen.AssistantAgent(
    name="Writer",
    system_message='You are a writer, your task is to write the report based on the analysis chat history, in the report please follow the framework design by the planner and present the all the stock price and fundemental data from data provider. Reply TERMINATE when the task is done.',
    llm_config=llm_config,
    )


market_an = autogen.AssistantAgent(
    name="Market Analyst",
    system_message="You are Market Analyst, Your task is analyzing the stock trend with serveral technical indicator and also making the suggestion. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    )

fundemental_an = autogen.AssistantAgent(
    name="Fundemental Analyst",
    system_message="You are Fundemental Analyst, please make the detail analysis based on the company fundemental information and list the top 2 competitors (stock ticker name) of this company, then make comparison with the competitor. You can ask the data provider to collect the fundemental information of the company and competitor seperatively and then based on all data collected ((please reply in the format 'data provider' + the function you want to call and the ticker name), then make the comparison expaination with table (shown the data). Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    )


saver = autogen.AssistantAgent(
    name="Saver",
    system_message="You are a file saver, Your task is save the analysis to markdown file (filename is the stock ticker name). Don't write any code, please use the function call 'save_markdown_report' to save the analysis to a markdown file. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    )



# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "") is not None and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        # the executor to run the generated code
        "executor": LocalCommandLineCodeExecutor(work_dir="coding"),

    },
)

planner = autogen.AssistantAgent(
    name="Planner",
    system_message="""Planner. Given a task, please determine what information is needed to complete the task.
Please note that don't write any python code. 
""",
    llm_config={"config_list": config_list, "cache_seed": None},
    human_input_mode="NEVER",
)



# @user_proxy.register_for_execution()
# @saver.register_for_llm(name="save_markdown_report", description="Save the analysis to a markdown file. The function should be used once the analysis generation is complete")
def save_markdown_report(report: Annotated[
        str, "The report content. The content should include detail explaination of the analysis based on the previous function output."
    ], file_path: Annotated[
        str, "The file path where the report should be saved (e.g., 'report.md')"
    ]) -> str:
    with open(file_path, "w") as f:
        f.write(report)
    return f"Report saved to {file_path}"


# @user_proxy.register_for_execution()
# @data_provider.register_for_llm(name="get_company_news", description="get the latest news for a company")
def get_news_alpha_vintage(ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ]) -> str:
    url=f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker_symbol}&apikey={api_key}"
    #print(url)
    response = requests.request("GET", url)
    result=response.json()
    #print(result)
    result=result['feed']
    if len(result)>0:
        text=""
        titles = [item['title'] for item in result]
        summaries = [item['summary'] for item in result]

        for i in range(len(result)):
            text=text+"[News Title]:"+titles[i]+"[News Content]:"+summaries[i]
        return text
        
    else:
        return "no news found for the company"
    

def get_fundemental_info(ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ]) -> str:
    url=f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_symbol}&apikey={api_key}"
    response = requests.request("GET", url)
    result=response.json()
    if result:
        return {
            "Symbol": result['Symbol'],
            "Industry": result['Industry'],
            "Description": result['Description'],
            "Sector": result['Sector'],
            "PERatio": result['PERatio'],
            "PEGRatio": result['PEGRatio'],
            "ProfitMargin": result['ProfitMargin'],
            "ReturnOnEquityTTM": result['ReturnOnEquityTTM'],
            "QuarterlyEarningsGrowthYOY": result['QuarterlyEarningsGrowthYOY'],
            "QuarterlyRevenueGrowthYOY": result['QuarterlyRevenueGrowthYOY'],
            "AnalystTargetPrice": result['AnalystTargetPrice'],
            "TrailingPE": result['TrailingPE'],
            "Beta": result['Beta'],
        }
    else:
        return "no data found for the company"


# @user_proxy.register_for_execution()
# @data_provider.register_for_llm(name="plot_stock_price", description="plot the stock price chart and save it to a file")
def plot_stock_price_chart(
    ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ],
   
    save_path: Annotated[str, "File path where the plot should be saved"],
) -> str:
    """
    Plot a stock price chart using mplfinance for the specified stock and time period,
    and save the plot to a file.
    """
    # Fetch historical data
    stock_data = ak.stock_us_daily(symbol=ticker_symbol, adjust="").tail(10)

    if stock_data.empty:
        print("No data found for the given date range.")
        return
    

    plt.figure(figsize=(10, 6))
    plt.plot(stock_data['close'], label=ticker_symbol+' Stock Price')
    plt.title('sStock Price Movement')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path)
    return f"{ticker_symbol} chart saved to <img {save_path}>"



# @user_proxy.register_for_execution()
# @data_provider.register_for_llm(name="get_stock_price", description="get the stock price data for a company")
def get_price(ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ]) -> str:
   
    df = ak.stock_us_daily(symbol=ticker_symbol, adjust="")
    

    return df.tail(10).to_json()

autogen.agentchat.register_function(
    get_price,
    caller=data_provider,
    executor=user_proxy,
    description="get the stock price data for a company",
    name="get_stock_price", 

     
    )

autogen.agentchat.register_function(
    get_news_alpha_vintage,
    caller=data_provider,
    executor=user_proxy,
    description="get the latest news for a company",
    name="get_company_news"
)

autogen.agentchat.register_function(
    plot_stock_price_chart,
    caller=data_provider,
    executor=user_proxy,
    description="plot the stock price chart and save it to a file",
    name="plot_stock_price"
)

autogen.agentchat.register_function(
    save_markdown_report,
    caller=saver,
    executor=user_proxy,
    description="Save the analysis to a markdown file",
    name="save_markdown_report"
)
autogen.agentchat.register_function(
    get_fundemental_info,
    caller=data_provider,
    executor=user_proxy,
    description="get the fundemental information of the company,it includes company overview, PE ratio, P/E ratio, Profit margin, Return on equity TTM, Quarterly earnings growth YOY, Quarterly revenue growth YOY, Analyst target price, Trailing PE, Beta",
    name="get_fundemental_info"
)



def custom_speaker_selection_func(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
    """Define a customized speaker selection function for function call-based interactions.

    Returns:
        Return an `Agent` class or a string from ['auto', 'manual', 'random', 'round_robin'] to select a default method to use.
    """
    messages = groupchat.messages
    print(groupchat.messages)

    if len(messages) <= 1:
        # First, let the planner determine the task
        return planner

    if last_speaker is planner:
        # If the last message is from planner, let the market analyst analyze the market
        return market_an
    elif last_speaker is market_an:
        if "data provider" in messages[-1]['content']:
        # If the last message is from market analyst, let the data provider provide the data
            return data_provider
        else:
            return writer
    elif last_speaker is data_provider:
        # If the last message is from data provider, send the data back to the requesting analyst
        if "Market Analyst" in messages[-1]["content"]:
            return market_an
        elif "Fundamental Analyst" in messages[-1]["content"]:
            return fundemental_an
        else:
            return user_proxy
    elif last_speaker is fundemental_an:
        if "data provider" in messages[-1]['content']:
        # If the last message is from fundamental analyst, let the data provider provide the data
            return data_provider
        else:
            return writer
    elif last_speaker is writer:
        return saver
    
    elif last_speaker is user_proxy:
        return writer
        
    else:
        # Default to auto speaker selection method
        return "auto"
    

groupchat = autogen.GroupChat(
    agents=[user_proxy, planner, market_an, fundemental_an, data_provider, saver,writer],
    messages=[],
    max_round=20,
    speaker_selection_method=custom_speaker_selection_func,
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list, "cache_seed": None})




task="write an equity stock report for MSFT"

with Cache.disk(cache_seed=31) as cache:
        result=autogen.initiate_chats(

       [
            {
                "sender": user_proxy,
                "recipient": data_provider,
                "message": "Gather information for MSFT, including plot the stock price trend, news, stock price and fundemental information. Save the graph in stock_price.png",           
                "clear_history": False,
                "silent": False,
                "summary_method": "last_msg",
            },
            
        ]
    )
        
        if len(result[0].chat_history)>0:
            for i in  result[0].chat_history:
                if i['content'] :
                    user_proxy.send(message=i['content'],recipient=manager,request_reply=False,silent=True)
        time.sleep(10)


        groupchat_history_custom = autogen.initiate_chats(
       [{
           "sender":user_proxy,
           "recipient":manager,
           "message":task,
           "max_turns":5,
           "summary_method":"last_msg",
           "clear_history":False,
           "silent":False,
       }]
    )

    

    #    [
    #         {
    #             "sender": user_proxy,
    #             "recipient": data_provider,
    #             "message": "Gather information for MSFT, including plot the stock price trend, news stock price. Save the graph in stock_price.png",           
    #             "clear_history": False,
    #             "silent": False,
    #             "summary_method": "last_msg",
    #         },
            
    #     ]
    # )
    # if len(result[0].chat_history)>0:
    #     for i in  result[0].chat_history:
    #         if i['content'] :
    #             # print(i['content'])
    #             user_proxy.send(message=i['content'],recipient=market_an,request_reply=False,silent=True)
    # time.sleep(10)

    # market_content=autogen.initiate_chats(
    # [{
    #                 "sender": user_proxy,
    #                 "recipient": market_an,
    #                 "message": "With the stock price chart provided, along with recent market news of the company, analyze the recent fluctuations of the stock and the potential relationship with market news. ",
    #                 "max_turns": 1,  # max number of turns for the conversation
    #                 "summary_method": "last_msg",
    #                 "clear_history": False,

    #                 # cheated here for stability
    #             }])
    

    # if len(market_content[0].chat_history)>0:
    #     # for i in  market_content[0].chat_history:
    #     #     if i['content'] :
    #     #print(market_content[0].chat_history[-1]['content'])
    #     user_proxy.send(message=market_content[0].chat_history[-1]['content'],recipient=saver,request_reply=False,silent=True)
    # time.sleep(10)
    
    # autogen.initiate_chats(
    #     [{
    #                 "sender": user_proxy,
    #                 "recipient":saver,
    #                 "message":"Store all the analyse in markdown format with filepath 'report.md' using the function 'save_markdown_report' and run it",
    #                 "summary_method": "last_msg",
    #                 "clear_history": False,
    #                 # cheated here for stability
    #             }])
    


