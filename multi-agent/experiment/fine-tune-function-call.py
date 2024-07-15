from IPython.display import Image, display
from datetime import datetime
import autogen
from autogen.coding import LocalCommandLineCodeExecutor
import os
from bing_news import BingSearch
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
ticker="MSFT"
# api_key="J6K11U31IPD4B4EX"


fine_tune_config_list=[{
    'model': 'example', #model here is your model name in the LM studio
    'api_key': 'ollama',
    'base_url': "http://localhost:4000",
}]




config_list1 = [

    {
    'model': 'llama3-8b-8192', #model here is your model name in the LM studio
    'api_key': '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',
    'base_url': "https://api.groq.com/openai/v1",
    }

]


config_list2 = [

    {
    'model': 'llama3-8b-8192', #model here is your model name in the LM studio
    'api_key': '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',
    'base_url': "https://api.groq.com/openai/v1",
    }

]


llm_config1={
       
        "config_list": config_list1,
        "timeout": 120,
        "temperature": 0.0, 

    }


llm_config2={
       
        "config_list": config_list2,
        "timeout": 120,
        "temperature": 0.0, 

    }

data_provider = autogen.AssistantAgent(
    name="Data Provider",
    system_message="You are a Data Provider. Your task is to provide charts and necessary market information. For coding tasks, only use the functions you have been provided with. Don't create code on your own. Reply TERMINATE when the task is done.",
    llm_config=llm_config1,
    )


market_an = autogen.AssistantAgent(
    name="Market Analyst",
    system_message="You are Market Analyst, please based on the stock price of the company, analayze the stock trend with serveral technical indicator and also make the suggestion. The analysis should follow this framework '[Stock price treand & Technical Indicator (with stock price graph)],[Recommendation & Prediction based on the trend and technical indicator], [Trading Strategy : target buy price and target sell price]'.Reply TERMINATE when the task is done.",
    llm_config=llm_config1,
    )

fundemental_an = autogen.AssistantAgent( 
    name="Fundemental Analyst",
    system_message="You are Fundemental Analyst, please make the detail analysis based on the company fundemental information and list the top 2 competitors (stock ticker name) of this company, then make comparison with the competitor. The analysis should follow this framework '[Company Overview],[Company Fundemental Analysis & Valuation],[State the Competitor and make comparison with Competitors (list table and data for comparison)],[Recommendation based on the company fundemental  (Good side and possible risk)], [Investment Strategy based on the Fundementals]'Reply TERMINATE when the task is done.",

    llm_config=llm_config2,
    )

macro_en = autogen.AssistantAgent( 
    name="Macro Analyst",
    system_message="You are Macro Analyst, please make the detail analysis based on the macro industry and macro economy, then make conclusion whether the macro situation for industry and economy would influnece the company and how. The analysis should follow this framework '[Current Industry macro situation],[Current macro country economy situation],[Affect for the company],[Recommendation & investment strategy based on the macro situation perspective]'Reply TERMINATE when the task is done.",
    llm_config=llm_config1,
    )

writer =autogen.AssistantAgent(
    name="Writer",
    system_message="You are a writer, Your task is to write a report based on the analysis provided by  market analyst, fundemental analyst and macro analyst.  The report should totally copy from the previous analyst's work and then rewrite it based on the format. Also if receiving feedback from your boss, you should be able to revise the report based on the feedback. The output should always follow the format: [Introduction of company]/n.../n/n[Company Financial performance & Valuation & Comparison with Competitors (with table and detailed data comparison)]/n.../n/n [Recent market news analysis & Relationship between news and stock price]/n.../n/n[How the recent macro industry and economy view would affect company]/n/n.../n/n[Recent stock price trend & Technical Indicator (add stock price graph with markdown format :'![](stock_price.png)')]/n/n.../n/n[Risk]/n/n.../n/n[Forecast]/n/n.../n/n[Recommendation & Trading or Investment Strategy]/n/n.../n. Reply TERMINATE when the task is done.",
    llm_config=llm_config1,
    
)


boss=autogen.AssistantAgent(
    name="Boss",
    system_message="You are a boss, Your task is to review the report written by your writer and provide feedback on the report. Your feedback should include detail suggestions for improvement, additional information that should be included, and any corrections that need to be made. all the suggestions should be made based on current data and content, don't ask for extra content. Your feedback should be written in English and be at least 100 words long.",
    llm_config=llm_config2,
)



saver = autogen.AssistantAgent(
    name="Saver",
    system_message="You are a file saver, Your task is save the analysis to markdown file. Only use the functions you have been provided with. Don't create code on your own. Reply TERMINATE when the task is done.",
    llm_config=llm_config1,
    )

finetune = autogen.AssistantAgent(
    name="Fine-tune",
    system_message=(
        "You are a seasoned stock market analyst. Your task is to list the positive developments and potential concerns for companies based on relevant news and basic financials from the past weeks, "
        "then provide an analysis and prediction for the companies' stock price movement for the upcoming week. \n\n"
        "Your answer format should be as follows:\n\n[Positive Developments]:\n1. ...\n\n[Potential Concerns]:\n1. ...\n\n[Prediction & Analysis]:\n..."
        "Reply TERMINATE at the end of your response."
    ),
    llm_config={
        "config_list": fine_tune_config_list,
        "temperature": 0.0,
    }
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
        "limit":10,
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
            save_dict.append({"headline":i['headline'],"time":i['created_at']})


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
        count=0
        for i in range(len(result)):
            count=count+1
            if count>10:
                break
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
        return result
#     {
#   "Name":result['Name'],          
#   "Symbol": result['Symbol'],
#   "Description": result['Description'],
#   "Sector": result['Sector'],
#   "PERatio": result['PERatio'],
#   "PEGRatio": result['PEGRatio'],
#   "DividendYield": result['DividendYield'],
#   "Earning Per Share": result['EPS'],
#   "ProfitMargin": result['ProfitMargin'],
#   "OperatingMarginTTM": result['OperatingMarginTTM'],
#   "ReturnOnAssetsTTM": result['ReturnOnAssetsTTM'],
#   "ReturnOnEquityTTM": result['ReturnOnEquityTTM'],
#   "QuarterlyEarningsGrowthYOY": result['QuarterlyEarningsGrowthYOY'],
#   "QuarterlyRevenueGrowthYOY": result['QuarterlyRevenueGrowthYOY'],
#   "AnalystTargetPrice": result['AnalystTargetPrice'],

#   "TrailingPE": result['TrailingPE'],
#   "ForwardPE": result['ForwardPE'],
#   "PriceToSalesRatioTTM": result['PriceToSalesRatioTTM'],
#   "PriceToBookRatio": result['PriceToBookRatio'],
#   "EVToRevenue": result['EVToRevenue'],
#   "EVToEBITDA": result['EVToEBITDA'],
#   "Beta": result['Beta'],
# }
        
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
    # df['date'].astype(str)
    df['date']=df['date'].dt.strftime('%Y-%m-%d')


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
    return df.tail(14).to_json()

def test_price(ticker,start_date,end_date):
    df=ak.stock_us_daily(symbol=ticker, adjust="")
    df.set_index('date', inplace=True)

    return df.loc[start_date:end_date]

def get_finetune_prompt(ticker):
    today=datetime.today().strftime('%Y-%m-%d')
    one_week_later = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    fundem_info=get_fundemental_info(ticker)
    #print(type(fundem_info))
    # fundem_info=json.loads(get_fundemental_info(ticker))
    company_profile="[Company Introduction]:\n\n "+fundem_info['Name']+" is a "+fundem_info['Sector']+" company. As of today, "+fundem_info['Name']+" has market capitalization of $"+fundem_info['MarketCapitalization']+" USD with "+ fundem_info['SharesOutstanding']+" shares outstanding."+ fundem_info['Name']+ "trades under the ticker "+ticker +"\n\n"
    financial="[Basic Financials]:\n\nReporting Period"+ fundem_info['LatestQuarter']+"\nQuarterly Revenue Growth YOY: "+str(float(fundem_info['QuarterlyRevenueGrowthYOY'])*100)+"%\nQuarterly Earnings Growth YOY: "+str(float(fundem_info['QuarterlyEarningsGrowthYOY'])*100)+"%\nProfit Margin: "+fundem_info['ProfitMargin']+"\n\n"

    ending="Based on all the information before "+today+", let's first analyze the positive developments and potential concerns for "+ticker+". Come up with 2-4 most important factors respectively and keep them concise. Most factors should be inferred from company related news. Then make your prediction of the "+ ticker+" stock price movement for next week ("+today+" - "+one_week_later+" ). Provide a summary analysis to support your prediction."
    two_week_ago=(datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
    one_week_ago=(datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
    first_stock=test_price(ticker,two_week_ago,one_week_ago)
    first_fluctuate=(first_stock['close'].iloc[-1]-first_stock['close'].iloc[0])/first_stock['close'].iloc[0]
    second_stock=test_price(ticker,one_week_ago,today)
    second_fluctuate=(second_stock['close'].iloc[-1]-second_stock['close'].iloc[0])/second_stock['close'].iloc[0]
    if first_fluctuate>0 :
        first_trend="up"
    else:
        first_trend="down"
    if second_fluctuate>0 :
        second_trend="up"
    else:
        second_trend="down"
    first_news_start="[News] From "+two_week_ago+" to "+one_week_ago+", the stock price of "+ticker+" went "+first_trend+" from "+str(first_stock['close'].iloc[0])+" to "+str(first_stock['close'].iloc[-1])+", a"+ first_trend+" by "+str(first_fluctuate*100)+"%. Company news during this period are listed below:\n\n"
    second_news_start="[News] From "+one_week_ago+" to "+today+", the stock price of "+ticker+" went "+second_trend+" from "+str(second_stock['close'].iloc[0])+" to "+str(second_stock['close'].iloc[-1])+", a"+ second_trend+" by "+str(second_fluctuate*100)+"%. Company news during this period are listed below:\n\n"
    first_new=""
    second_new=""
    bing_search = BingSearch(ticker)
    first_news=bing_search.formulate(two_week_ago)
    second_news=bing_search.formulate(one_week_ago)


    for i in first_news.head(5).to_dict(orient='records'):
        first_new=first_new+"[Headline]:"+i['name']+"\n[Content]:"+i['description']+"\n\n"
    
    for i in second_news.head(5).to_dict(orient='records'):
        second_new=second_new+"[Headline]:"+i['name']+"\n[Content]:"+i['description']+"\n\n"
    return company_profile+first_news_start+first_new+second_news_start+second_new+financial+ending

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
    llm_config=llm_config1,

)

# 
with Cache.disk(cache_seed=31) as cache:
    first_opinion=autogen.initiate_chats(
        [{
            "sender": user_proxy,
            "recipient": finetune,
            "message": get_finetune_prompt(ticker),
            # "message": "[Company Introduction]:\n\nMicrosoft Corporation is a TECHNOLOGY company. As of today, Microsoft Corporation has market capitalization of $3465240117000 USD with 7432310000 shares outstanding.Microsoft Corporationtrades under the ticker MSFT.\n\n[News] From 2024-06-25 to 2024-07-02, the stock price of MSFT went up from 450.95 to 459.28, aup by 1.8472114425102528%. Company news during this period are listed below:\n\n[Headline]:EXCLUSIVE: Tech Valuations 'Pricey', Cybersecurity 'Top Of Mind' Ahead Of US Elections. \n\n[Content]:The tech sector has been the engine driving stock market gains this year, with giants like Apple Inc (NASDAQ:AAPL), Microsoft Corp (NASDAQ:MSFT) and Nvidia Corp (NASDAQ:\n\n[Headline]:Tech giants face tough task to sustain second half stock rally\n\n[Content]:The world’s largest technology stocks drove a banner first half for the SandP 500. The question for the rest of the year is whether their strength continues. \n\n[Headline]:Microsoft (MSFT) Price Prediction and Forecast\n\n[Content]:Everyone knows Microsoft (NASDAQ: MSFT) and its best known products, including Windows operating system, Microsoft 365 suite of productivity apps but its growing cloud computing platform, Azure is the future of the company. \n\n[Headline]:Goldman Sachs Questions the Economic Payoff of Generative AI\n\n[Content]:The anticipated economic benefits of generative AI investments are under significant scrutiny, according to the latest research newsletter from Goldman\n\n[Headline]:Why Apple’s stock may lack upside after a 38% climb off this year’s lows\n\n[Content]:Piper Sandler says investors are right to be excited about AI but thinks they should also consider potential consumer-spending risk. \n\n[News] From 2024-07-02 to 2024-07-09, the stock price of MSFT went up from 459.28 to 466.24, aup by 1.5154154328514275%. Company news during this period are listed below: \n\n[Headline]:EXCLUSIVE: Tech Valuations 'Pricey', Cybersecurity 'Top Of Mind' Ahead Of US Elections\n\n [Content]:The tech sector has been the engine driving stock market gains this year, with giants like Apple Inc (NASDAQ:AAPL), Microsoft Corp (NASDAQ:MSFT) and Nvidia Corp (NASDAQ:[Headline]:Tech giants face tough task to sustain second half stock rally\n\n[Content]:The world’s largest technology stocks drove a banner first half for the SandP 500. The question for the rest of the year is whether their strength continues. \n\n[Headline]:Microsoft (MSFT) Price Prediction and Forecast\n\n[Content]:Everyone knows Microsoft (NASDAQ: MSFT) and its best known products, including Windows operating system, Microsoft 365 suite of productivity apps but its growing cloud computing platform, Azure is the future of the company. \n\n[Basic Financials]: \n\n Reporting Period 2024-03-31\n\nQuarterly Revenue Growth YOY: 17.0%\n\nQuarterly Earnings Growth YOY: 20.0%\n\nProfit Margin: 0.364\n\nBased on all the information before 2024-07-09, let's first analyze the positive developments and potential concerns for MSFT. Come up with 2-4 most important factors respectively and keep them concise. Most factors should be inferred from company related news. Then make your prediction of the MSFT stock price movement for next week (2024-07-09 - 2024-07-16 ). Provide a summary analysis to support your prediction.",
            "clear_history": True,
            "silent": False,
            "max-turns": 1,

        }]
    )
    print(first_opinion[0].chat_history[1])
    if len(first_opinion[0].chat_history)>0:
  
        user_proxy.send(message=first_opinion[0].chat_history[1]['content'],recipient=writer,request_reply=False,silent=True)
    time.sleep(10)

    result=autogen.initiate_chats(

       [
            {
                "sender": user_proxy,
                "recipient": data_provider,
                "message": f"Gather information for {ticker}, including plot the stock graph, news and stock price. Save the graph in stock_price.png. Reply TERMINATE (not tool used) when the task is done.",           
                "clear_history": False,
                "silent": False,
                "summary_method": "last_msg",
                "max-turns": 1,
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
  
        user_proxy.send(message=market_content[0].chat_history[-1]['content'],recipient=writer,request_reply=False,silent=True)
        user_proxy.send(message=market_content[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)
    time.sleep(30)


 


    fun_data1=autogen.initiate_chats(

       [
            {
                "sender": user_proxy,
                "recipient": data_provider,
                "message": f"Gather fundemental info for {ticker} and its top 1 competitor.",           
                "clear_history": True,
                "silent": False,
                "summary_method": "last_msg",
            },
            
        ]
    )
    if len(fun_data1[0].chat_history)>0:
        for i in  fun_data1[0].chat_history:
            if i['content'] :
                user_proxy.send(message=i['content'],recipient=fundemental_an,request_reply=False,silent=True)

    time.sleep(60)

    fundemental_content=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": fundemental_an,
                    "message": f"The company is {ticker}, analyzing the company's fundemental and make comparison with the competitor. All the information should be based on the data provided in the history chat. Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation
                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    
    if len(fundemental_content[0].chat_history)>0:
     
        user_proxy.send(message=fundemental_content[0].chat_history[-1]['content'],recipient=writer,request_reply=False,silent=True)
        user_proxy.send(message=fundemental_content[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)

    time.sleep(240)

    macro_data=autogen.initiate_chats(

       [
            {
                "sender": user_proxy,
                "recipient": data_provider,
                "message": f"Gather macro info for {ticker}'s industry",           
                "clear_history": False,
                "silent": False,
                "summary_method": "last_msg",
            },
            
        ]
    )
    time.sleep(60)


    if len(macro_data[0].chat_history)>0:
        for i in  macro_data[0].chat_history:
            if i['content'] :
                user_proxy.send(message=i['content'],recipient=macro_en,request_reply=False,silent=True)

    time.sleep(60)

    macro_content=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": macro_en,
                    "message": f"Our company is {ticker},Based on the macro industry info, analyze the how the current macro industry situation would influence the company. All the information should be based on the data provided in the history chat. Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation
                    "summary_method": "last_msg",
                    "clear_history": False,

                }])
    
    if len(macro_content[0].chat_history)>0:
    
        user_proxy.send(message=macro_content[0].chat_history[-1]['content'],recipient=writer,request_reply=False,silent=True)
        user_proxy.send(message=macro_content[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)

    time.sleep(10)

    report=autogen.initiate_chats(
    [{
                    "sender": user_proxy,
                    "recipient": writer,
                    "message": f"Please used the analysis provided by the market analyst, fundemental analyst and macro analyst, write a report for the {ticker} (you can totaly copy the writing from these three persons and then rewrite it to fit the format). Please totally rely on the information provided from the history chat to make opinion, don't make your own fact. Reply TERMINATE when the task is done.",
                    "max_turns": 1,  # max number of turns for the conversation
                    "summary_method": "last_msg",
                    "clear_history": False,

                    # cheated here for stability
                }])
    


    if len(market_content[0].chat_history)>0:
        user_proxy.send(message=report[0].chat_history[-1]['content'],recipient=boss,request_reply=False,silent=True)
    

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
    


