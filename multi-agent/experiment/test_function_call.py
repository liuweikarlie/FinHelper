from IPython.display import Image, display
from datetime import datetime
import autogen
from autogen.coding import LocalCommandLineCodeExecutor
import os
import time
from autogen.cache import Cache
import ta
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
# api_key="J6K11U31IPD4B4EX"

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
    system_message="You are a Data Provider. Your task is to provide charts and necessary market information and send the data back to agent who need it.For coding tasks, only use the functions you have been provided with. Don't create code on your own. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    )


market_an = autogen.AssistantAgent(
    name="Market Analyst",
    system_message="You are Market Analyst, please based on the stock price of the company, analayze the stock trend with serveral technical indicator and also make the suggestion. The analysis should follow this framework '[Stock price treand & Technical Indicator (with stock price graph)],[Recommendation & Prediction based on the trend and technical indicator], [Trading Strategy : target buy price and target sell price]'.Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    )

fundemental_an = autogen.AssistantAgent( 
    name="Fundemental Analyst",
    system_message="You are Fundemental Analyst, please make the detail analysis based on the company fundemental information and list the top 2 competitors (stock ticker name) of this company, then make comparison with the competitor. The analysis should follow this framework '[Company Overview],[Company Fundemental Analysis & Valuation],[State the Competitor and make comparison with Competitors (list table and data for comparison)],[Recommendation based on the company fundemental  (Good side and possible risk)], [Investment Strategy based on the Fundementals]'Reply TERMINATE when the task is done.",

    llm_config=llm_config,
    )

macro_en = autogen.AssistantAgent( 
    name="Macro Analyst",
    system_message="You are Macro Analyst, please make the detail analysis based on the macro industry and macro economy, then make conclusion whether the macro situation for industry and economy would influnece the company and how. The analysis should follow this framework '[Current Industry macro situation],[Current macro country economy situation],[Affect for the company],[Recommendation & investment strategy based on the macro situation perspective]'Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    )

writer =autogen.AssistantAgent(
    name="Writer",
    system_message="You are a writer, Your task is to write a report based on the analysis provided by the market analyst, fundemental analyst and macro analyst. The report should totally copy from the previous analyst's work and then rewrite it based on the format. Also if receiving feedback from your boss, you should be able to revise the report based on the feedback. The output should always follow the format: [Introduction of company]/n.../n/n[Company Financial performance & Valuation & Comparison with Competitors (with table and detailed data comparison)]/n.../n/n [Recent market news analysis & Relationship between news and stock price]/n.../n/n[How the recent macro industry and economy view would affect company]/n/n.../n/n[Recent stock price trend & Technical Indicator (add stock price graph with markdown format :'![](stock_price.png)')]/n/n.../n/n[Risk]/n/n.../n/n[Forecast]/n/n.../n/n[Recommendation & Trading or Investment Strategy]/n/n.../n. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
    
)


boss=autogen.AssistantAgent(
    name="Boss",
    system_message="You are a boss, Your task is to review the report written by your writer and provide feedback on the report. Your feedback should include detail suggestions for improvement, additional information that should be included, and any corrections that need to be made. all the suggestions should be made based on current data and content, don't ask for extra content. Your feedback should be written in English and be at least 100 words long.",
    llm_config=llm_config,
)


saver = autogen.AssistantAgent(
    name="Saver",
    system_message="You are a file saver, Your task is save the analysis to markdown file. Only use the functions you have been provided with. Don't create code on your own. Reply TERMINATE when the task is done.",
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
    

def get_company_news(ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ]) -> str:
    apac_api_key="PK7YXQROBU7QJQ9RWH9X"
    apac_secret_key="ucwKckj0mwJsYNsGZNeqkXgX9P87nHfZuKpMzxcm"

    params={
        "symbols":ticker_symbol,
        "limit":50,
        "include_content":False,
    }
    headers={
        'Apca-Api-Key-Id':apac_api_key,
        'Apca-Api-Secret-Key':apac_secret_key,
    }
    url="https://data.alpaca.markets/v1beta1/news"
    response = requests.get(url,headers=headers,params=params)
    if response.status_code==200:
        result=response.json()['news']
        save_dict=[]
        for i in result:
            save_dict.append({"headline":i['headline'],"time":i['created_at'],'symbol':i['symbols']})


        return save_dict
        
    else:
        return "no news found for the company"

def get_macro_info(topic: Annotated[
        str, "The topic of the industry macro information (e.g., 'technology', 'retail_wholesale', 'manufacturing','life_sciences')"
    ]) -> str:
    url=f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topic={topic}&apikey={api_key}"
    response = requests.request("GET", url)
    result=response.json()
    print(result)
    result=result['feed']
    if len(result)>0:
        text=""
        titles = [item['title'] for item in result]
        summaries = [item['summary'] for item in result]

        # Create DataFrame
        for i in range(len(result)):
            text=text+"[News Title]:"+titles[i]+"[News Content]:"+summaries[i]
        return text
        
    else:
        return "no macro news found "

def get_fundemental_info(ticker_symbol: Annotated[
        str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
    ]) -> str:
    url=f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_symbol}&apikey={api_key}"
    response = requests.request("GET", url)
    result=response.json()
    print(result)
    if result:
        return {
            
  "Symbol": result['Symbol'],
  "Description": result['Description'],
  "Sector": result['Sector'],
  "PERatio": result['PERatio'],
  "PEGRatio": result['PEGRatio'],
  "DividendYield": result['DividendYield'],
  "Earning Per Share": result['EPS'],
  "ProfitMargin": result['ProfitMargin'],
  "OperatingMarginTTM": result['OperatingMarginTTM'],
  "ReturnOnAssetsTTM": result['ReturnOnAssetsTTM'],
  "ReturnOnEquityTTM": result['ReturnOnEquityTTM'],
  "QuarterlyEarningsGrowthYOY": result['QuarterlyEarningsGrowthYOY'],
  "QuarterlyRevenueGrowthYOY": result['QuarterlyRevenueGrowthYOY'],
  "AnalystTargetPrice": result['AnalystTargetPrice'],
#   "AnalystRatings": {
#     "StrongBuy": result['AnalystRecommendation']['StrongBuy'],
#     "Buy": result['AnalystRecommendation']['Buy'],
#     "Hold": result['AnalystRecommendation']['Hold'],
#     "Sell": result['AnalystRecommendation']['Sell'],
#     "StrongSell": result['AnalystRecommendation']['StrongSell']
#   },
  "TrailingPE": result['TrailingPE'],
  "ForwardPE": result['ForwardPE'],
  "PriceToSalesRatioTTM": result['PriceToSalesRatioTTM'],
  "PriceToBookRatio": result['PriceToBookRatio'],
  "EVToRevenue": result['EVToRevenue'],
  "EVToEBITDA": result['EVToEBITDA'],
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
    stock_data['date'].astype(str)
    stock_data['date'].dt.strftime('%Y-%m-%d')

    if stock_data.empty:
        print("No data found for the given date range.")
        return
    

    plt.figure(figsize=(10, 6))
    plt.plot(stock_data['date'],stock_data['close'], label=ticker_symbol+' Stock Price')
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
    df['date'].astype(str)
    df['date'].dt.strftime('%Y-%m-%d')

    df.set_index('date', inplace=True)

    # Calculating MACD
    df['MACD'] = ta.trend.macd(df['close'])
    df['MACD_Signal'] = ta.trend.macd_signal(df['close'])
    df['MACD_Diff'] = ta.trend.macd_diff(df['close'])

    # Calculating RSI
    df['RSI'] = ta.momentum.rsi(df['close'])

    # Calculating EMA
    df['EMA'] = ta.trend.ema_indicator(df['close'])
    df['ADI']=ta.volume.AccDistIndexIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume']).acc_dist_index()
    df['FI']=ta.volume.ForceIndexIndicator(df['close'], df['volume']).force_index() 

    # Calculating Bollinger Bands
    indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['BB_High'] = indicator_bb.bollinger_hband()
    df['BB_Low'] = indicator_bb.bollinger_lband()
    df['BB_Middle'] = indicator_bb.bollinger_mavg()
    return df.tail(10).to_json()

autogen.agentchat.register_function(
    get_price,
    caller=data_provider,
    executor=user_proxy,
    description="get the stock price data for a company and a series of technical indicator including MACD, RSI, EMA, ADI, FI, Bollinger Bands. The data will be returned as a JSON string.",
    name="get_stock_price", 
    )

autogen.agentchat.register_function(
    get_company_news,
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
    get_macro_info,
    caller=data_provider,
    executor=user_proxy,
    description="get the macro information for a specific industry",
    name="get_macro_info"
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






planner = autogen.AssistantAgent(
    name="Planner",
    system_message="""Planner. Given a task, please determine what the overall framework for finish the task based on the history data sended, don't give any detail data.
Please note that don't write any python code. Reply TERMINATE at the end. 
""",
    llm_config=llm_config,

)



with Cache.disk(cache_seed=31) as cache:

    result=autogen.initiate_chats(

       [
            {
                "sender": user_proxy,
                "recipient": data_provider,
                "message": "Gather information for MSFT, including plot the stock price trend, news stock price. Save the graph in stock_price.png",           
                "clear_history": False,
                "silent": False,
                "summary_method": "last_msg",
            },
            
        ]
    )
    if len(result[0].chat_history)>0:
        for i in  result[0].chat_history:
            if i['content'] :
                # print(i['content'])
                user_proxy.send(message=i['content'],recipient=market_an,request_reply=False,silent=True)
                user_proxy.send(message=i['content'],recipient=planner,request_reply=False,silent=True)

    time.sleep(10)
    
    # planner=autogen.initiate_chats(

    #    [
    #         {
    #             "sender": user_proxy,
    #             "recipient": market_an,
    #             "message": "give the framework of analyse the stock MSFT. Please Reply TERMINATE when the task is done",           
    #             "clear_history": False,
    #             "silent": False,
    #             "summary_method": "last_msg",
    #             "max_turn":1
    #         },
            
    #     ]
    # )


    # if len(planner[0].chat_history)>0:
    #     for i in  planner[0].chat_history:
    #         if i['content'] :
    #             # print(i['content'])
    #             user_proxy.send(message=i['content'],recipient=market_an,request_reply=False,silent=True)

    # time.sleep(10)




    market_content=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": market_an,
                    "message": "With the stock price chart provided, along with recent market news of the company, analyze the recent fluctuations of the stock and the potential relationship with market news. and write the report based on the framework provide from the planner, all the information should be based on the data provided in the history chat. ",
                    "max_turns": 1,  # max number of turns for the conversation
                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    

    if len(market_content[0].chat_history)>0:
        # for i in  market_content[0].chat_history:
        #     if i['content'] :
        #print(market_content[0].chat_history[-1]['content'])
        user_proxy.send(message=market_content[0].chat_history[-1]['content'],recipient=writer,request_reply=False,silent=True)
        user_proxy.send(message=market_content[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)
    time.sleep(10)


    # fun_data=autogen.initiate_chats(

    #    [
    #         {
    #             "sender": user_proxy,
    #             "recipient": data_provider,
    #             "message": "Gather fundemental info for MSFT ",           
    #             "clear_history": False,
    #             "silent": False,
    #             "summary_method": "last_msg",
    #         },
            
    #     ]
    # )
    # if len(fun_data[0].chat_history)>0:
    #     for i in  fun_data[0].chat_history:
    #         if i['content'] :
    #             # print(i['content'])
    #             user_proxy.send(message=i['content'],recipient=fundemental_an,request_reply=False,silent=True)

    # time.sleep(10)


    fun_data1=autogen.initiate_chats(

       [
            {
                "sender": user_proxy,
                "recipient": data_provider,
                "message": "Gather fundemental info for MSFT and its top 1 competitor.",           
                "clear_history": True,
                "silent": False,
                "summary_method": "last_msg",
            },
            
        ]
    )
    if len(fun_data1[0].chat_history)>0:
        for i in  fun_data1[0].chat_history:
            if i['content'] :
                # print(i['content'])
                user_proxy.send(message=i['content'],recipient=fundemental_an,request_reply=False,silent=True)

    time.sleep(10)

    fundemental_content=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": fundemental_an,
                    "message": "The company is MSFT, analyzing the company's fundemental and make comparison with the competitor. All the information should be based on the data provided in the history chat. Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation
                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    
    if len(fundemental_content[0].chat_history)>0:
        # for i in  fundemental_content[0].chat_history:
        #     if i['content'] :
        #print(fundemental_content[0].chat_history[-1]['content'])
        user_proxy.send(message=fundemental_content[0].chat_history[-1]['content'],recipient=writer,request_reply=False,silent=True)
        user_proxy.send(message=fundemental_content[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)

    time.sleep(10)

    macro_data=autogen.initiate_chats(

       [
            {
                "sender": user_proxy,
                "recipient": data_provider,
                "message": "Gather macro info for MSFT's industry",           
                "clear_history": False,
                "silent": False,
                "summary_method": "last_msg",
            },
            
        ]
    )
    if len(macro_data[0].chat_history)>0:
        for i in  macro_data[0].chat_history:
            if i['content'] :
                # print(i['content'])
                user_proxy.send(message=i['content'],recipient=macro_en,request_reply=False,silent=True)

    time.sleep(10)

    macro_content=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": macro_en,
                    "message": "Our company is MSFT,Based on the macro industry info, analyze the how the current macro industry situation would influence the company. All the information should be based on the data provided in the history chat. Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation
                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    
    if len(macro_content[0].chat_history)>0:
        # for i in  macro_content[0].chat_history:
        #     if i['content'] :
        #print(macro_content[0].chat_history[-1]['content'])
        user_proxy.send(message=macro_content[0].chat_history[-1]['content'],recipient=writer,request_reply=False,silent=True)
        user_proxy.send(message=macro_content[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)

    time.sleep(10)

    report=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": writer,
                    "message": "Please used the analysis provided by the market analyst, fundemental analyst and macro analyst, write a report for the MSFT (you can totaly copy the writing from these three persons and then rewrite it to fit the format). Please totally rely on the information provided from the history chat to make opinion, don't make your own fact. Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation
                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    


    if len(market_content[0].chat_history)>0:
        user_proxy.send(message=report[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)
        #user_proxy.send(message=report[0].chat_history[-1]['content'],recipient=saver,request_reply=False,silent=True)
    

    time.sleep(10)


    reflection=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": boss,
                    "message": "Provide suggestions for the report, Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation

                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    
    if len(reflection[0].chat_history)>0:
        user_proxy.send(message=reflection[0].chat_history[-1]['content'],recipient=writer,request_reply=False,silent=True)
        # user_proxy.send(message=reflection[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)

    time.sleep(10)

    report1=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": writer,
                    "message": "Please revise the report based on the feedback provided by the boss and the report should follow the format rules. Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation
                   
                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    

    if len(market_content[0].chat_history)>0:
        # user_proxy.send(message=report1[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)
        user_proxy.send(message=report1[0].chat_history[-1]['content'],recipient=saver,request_reply=False,silent=True)

    time.sleep(20)

    

    autogen.initiate_chats(
        [{
                    "sender": user_proxy,
                    "recipient":saver,
                    "message":"Store all the analyse in markdown format with filepath 'report.md' using the function 'save_markdown_report' and run it",
                    "summary_method": "last_msg",
                    "clear_history": False,
                    # cheated here for stability
                }])
    


