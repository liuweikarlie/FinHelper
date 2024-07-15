from IPython.display import Image, display
from datetime import datetime
import autogen
from autogen.coding import LocalCommandLineCodeExecutor
import os
import streamlit as st
import requests

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
from functools import wraps
from bing_news import BingSearch

from autogen import AssistantAgent, UserProxyAgent

class TrackableAssistantAgent(AssistantAgent):
    """
    A custom AssistantAgent that tracks the messages it receives.

    This is done by overriding the `_process_received_message` method.
    """

    def _process_received_message(self, message, sender, silent):
        with st.chat_message(sender.name):
            expander = st.expander("See Thought + Action generate from"+sender.name)
            expander.markdown(message)
        return super()._process_received_message(message, sender, silent)


class TrackableUserProxyAgent(UserProxyAgent):
    """
    A custom UserProxyAgent that tracks the messages it receives.

    This is done by overriding the `_process_received_message` method.
    """

    def _process_received_message(self, message, sender, silent):
        with st.chat_message(sender.name):
            expander = st.expander("See selected function from "+sender.name)
            expander.markdown(message)
            
        return super()._process_received_message(message, sender, silent)
    
class MarketAnalysis:
    def __init__(self):
        #self.api_key = "LS5RN88HLIZU7NOH"
        self.api_key="J6K11U31IPD4B4EX"
        self.config_list1 = [
            # {
            #     'model': 'llama3-8b-8192',
            #     'api_key': 'api',
            #     'base_url': "https://api.groq.com/openai/v1",
            # }

             {
                'model': 'llama3',
                'api_key': 'notrequired',
                'base_url': "http://localhost:6000",
            }
        ]
        self.config_list2=[
            #  {
            #     'model': 'llama3-8b-8192',
            #     'api_key': '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',
            #     'base_url': "https://api.groq.com/openai/v1",
            # }

                   {
                'model': 'llama3',
                'api_key': 'notrequired',
                'base_url': "http://localhost:6000",
            }


        ]

        self.finetune_list=[{
            'model': 'example',
            'api_key': 'ollama',
            'base_url': "http://localhost:4000",

        }]
        self.llm_config1 = {
            "config_list": self.config_list1,
            "timeout": 120,
            "temperature": 0.0,
        }
        self.llm_config2={
             "config_list": self.config_list2,
            "timeout": 120,
            "temperature": 0.0,

        }
        self.llm_fine_tune_config2={
            "config_list": self.finetune_list,
            "temperature": 0.0,

        }
        self.finetune=self.create_agent("Finetune",(
        "You are a seasoned stock market analyst. Your task is to list the positive developments and potential concerns for companies based on relevant news and basic financials from the past weeks, "
        "then provide an analysis and prediction for the companies' stock price movement for the upcoming week. \n\n"
        "Your answer format should be as follows:\n\n[Positive Developments]:\n1. ...\n\n[Potential Concerns]:\n1. ...\n\n[Prediction & Analysis]:\n..."
        "Reply TERMINATE when the task is done."
    ),self.llm_fine_tune_config2)
        self.data_provider = self.create_agent("Data Provider", "You are a Data Provider. Your task is to provide charts and necessary market information and send the data back to agent who need it.For coding tasks, only use the functions you have been provided with. Don't create code on your own. Reply TERMINATE when the task is done.",self.llm_config1)
        self.market_an = self.create_agent("Market Analyst", "You are Market Analyst, please based on the stock price of the company, analayze the stock trend with serveral technical indicator and also make the suggestion. The analysis should follow this framework '[Stock price treand & Technical Indicator (with stock price graph)],[Recommendation & Prediction based on the trend and technical indicator], [Trading Strategy : target buy price and target sell price]'.Reply TERMINATE when the task is done.",self.llm_config1)
        self.fundemental_an = self.create_agent("Fundemental Analyst", "You are Fundemental Analyst, please make the detail analysis based on the company fundemental information and list the top 2 competitors (stock ticker name) of this company, then make comparison with the competitor. The analysis should follow this framework '[Company Overview],[Company Fundemental Analysis & Valuation],[State the Competitor and make comparison with Competitors (list table and data for comparison)],[Recommendation based on the company fundemental  (Good side and possible risk)], [Investment Strategy based on the Fundementals]'Reply TERMINATE when the task is done.",self.llm_config2)
        self.macro_en = self.create_agent("Macro Analyst", "You are Macro Analyst, please make the detail analysis based on the macro industry and macro economy, then make conclusion whether the macro situation for industry and economy would influnece the company and how. The analysis should follow this framework '[Current Industry macro situation],[Current macro country economy situation],[Affect for the company],[Recommendation & investment strategy based on the macro situation perspective]'Reply TERMINATE when the task is done.",self.llm_config2)
        self.writer = self.create_agent("Writer", "You are a writer, Your task is to write a report based on the analysis provided by the market analyst, fundemental analyst and macro analyst. The report should totally copy from the previous analyst's work and then rewrite it based on the format. Also if receiving feedback from your boss, you should be able to revise the report based on the feedback. The output should always follow the format: [Introduction of company]/n.../n/n[Company Financial performance & Valuation & Comparison with Competitors (with table and detailed data comparison)]/n.../n/n [Recent market news analysis & Relationship between news and stock price]/n.../n/n[How the recent macro industry and economy view would affect company]/n/n.../n/n[Recent stock price trend & Technical Indicator (add stock price graph with markdown format :'![](stock_price.png)')]/n/n.../n/n[Risk]/n/n.../n/n[Forecast]/n/n.../n/n[Recommendation & Trading or Investment Strategy]/n/n.../n. Reply TERMINATE when the task is done.",self.llm_config1)
        self.boss = self.create_agent("Boss", "You are a boss, Your task is to review the report written by your writer and provide feedback on the report. Your feedback should include detail suggestions for improvement, additional information that should be included, and any corrections that need to be made. all the suggestions should be made based on current data and content, don't ask for extra content. Your feedback should be written in English and be at least 100 words long.",self.llm_config2)
        self.saver = self.create_agent("Saver", "You are a file saver, Your task is save the analysis to markdown file. Only use the functions you have been provided with. Don't create code on your own. Reply TERMINATE when the task is done.",self.llm_config1)
        self.user_proxy = TrackableUserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "") is not None and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={
                "executor": LocalCommandLineCodeExecutor(work_dir="coding"),
            },
        )
        self.register_functions()

    def create_agent(self, name, system_message,llm_config):
        return TrackableAssistantAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
        )
    
    def rag_retrival(self,question: Annotated[str,"The query that ask for RAG retrieval system"])->str:
        url = 'http://localhost:5000/api/ask' 
        payload = {'question': question}
        response = requests.post(url, json=payload)
        print("please wait")
        format_json=response.json()
    
        return format_json





    def save_markdown_report(self, report: Annotated[str, "The report content. The content should include detail explaination of the analysis based on the previous function output."], file_path: Annotated[str, "The file path where the report should be saved (e.g., 'report.md')"]) -> str:
        with open(file_path, "w") as f:
            f.write(report)
        return f"Report saved to {file_path}"

    def get_news_alpha_vintage(self, ticker_symbol: Annotated[str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"]) -> str:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker_symbol}&apikey={self.api_key}"
        response = requests.request("GET", url)
        result = response.json()['feed']
        if len(result) > 0:
            text = ""
            titles = [item['title'] for item in result]
            summaries = [item['summary'] for item in result]
            for i in range(len(result)):
                text += f"[News Title]:{titles[i]}[News Content]:{summaries[i]}"
            return text
        else:
            return "no news found for the company"

    def get_company_news(self, ticker_symbol: Annotated[str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"]) -> str:
        apac_api_key = "PK7YXQROBU7QJQ9RWH9X"
        apac_secret_key = "ucwKckj0mwJsYNsGZNeqkXgX9P87nHfZuKpMzxcm"
        params = {
            "symbols": ticker_symbol,
            "limit": 10,
            "include_content": False,
        }
        headers = {
            'Apca-Api-Key-Id': apac_api_key,
            'Apca-Api-Secret-Key': apac_secret_key,
        }
        url = "https://data.alpaca.markets/v1beta1/news"
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()['news']
            save_dict = [{"headline": i['headline'], "time": i['created_at'], 'symbol': i['symbols']} for i in result]
            return save_dict
        else:
            return "no news found for the company"

    def get_macro_info(self, topic: Annotated[str, "The topic of the industry macro information (e.g., 'technology', 'retail_wholesale', 'manufacturing','life_sciences')"]) -> str:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topic={topic}&apikey={self.api_key}"
        response = requests.request("GET", url)
        result = response.json()['feed']
        if len(result) > 0:
            text = ""
            titles = [item['title'] for item in result]
            summaries = [item['summary'] for item in result]
            count=0
            for i in range(len(result)):
                count=count+1
                if count>10:
                    break
                text += f"[News Title]:{titles[i]}[News Content]:{summaries[i]}"
            return text
        else:
            return "no macro news found"

    def get_fundemental_info(self, ticker_symbol: Annotated[str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"]) -> str:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_symbol}&apikey={self.api_key}"
        response = requests.request("GET", url)
        result = response.json()
        if result:
            return result
        # {
        #         "Symbol": result['Symbol'],
        #         "Description": result['Description'],
        #         "Sector": result['Sector'],
        #         "PERatio": result['PERatio'],
        #         "PEGRatio": result['PEGRatio'],
        #         "DividendYield": result['DividendYield'],
        #         "Earning Per Share": result['EPS'],
        #         "ProfitMargin": result['ProfitMargin'],
        #         "OperatingMarginTTM": result['OperatingMarginTTM'],
        #         "ReturnOnAssetsTTM": result['ReturnOnAssetsTTM'],
        #         "ReturnOnEquityTTM": result['ReturnOnEquityTTM'],
        #         "QuarterlyEarningsGrowthYOY": result['QuarterlyEarningsGrowthYOY'],
        #         "QuarterlyRevenueGrowthYOY": result['QuarterlyRevenueGrowthYOY'],
        #         "AnalystTargetPrice": result['AnalystTargetPrice'],
        #         "TrailingPE": result['TrailingPE'],
        #         "ForwardPE": result['ForwardPE'],
        #         "PriceToSalesRatioTTM": result['PriceToSalesRatioTTM'],
        #         "PriceToBookRatio": result['PriceToBookRatio'],
        #         "EVToRevenue": result['EVToRevenue'],
        #         "EVToEBITDA": result['EVToEBITDA'],
        #         "Beta": result['Beta'],
        #     }
        else:
            return "no data found for the company"

    def plot_stock_price_chart(self, ticker_symbol: Annotated[str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"], save_path: Annotated[str, "File path where the plot should be saved"]) -> str:
        stock_data = ak.stock_us_daily(symbol=ticker_symbol, adjust="").tail(10)
        stock_data['date'].astype(str)
        stock_data['date'].dt.strftime('%Y-%m-%d')
        if stock_data.empty:
            print("No data found for the given date range.")
            return
        plt.figure(figsize=(10, 6))
        plt.plot(stock_data['date'], stock_data['close'], label=ticker_symbol + ' Stock Price')
        plt.title('Stock Price Movement')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.legend()
        plt.grid(True)
        plt.savefig(save_path)
        return f"{ticker_symbol} chart saved to <img {save_path}>"

    def get_price(self, ticker_symbol: Annotated[str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"]) -> str:
        df = ak.stock_us_daily(symbol=ticker_symbol, adjust="")
        df['date'].astype(str)
        df['date'].dt.strftime('%Y-%m-%d')
        df.set_index('date', inplace=True)
        df['MACD'] = ta.trend.macd(df['close'])
        df['MACD_Signal'] = ta.trend.macd_signal(df['close'])
        df['MACD_Diff'] = ta.trend.macd_diff(df['close'])
        df['RSI'] = ta.momentum.rsi(df['close'])
        df['EMA'] = ta.trend.ema_indicator(df['close'])
        df['ADI'] = ta.volume.AccDistIndexIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume']).acc_dist_index()
        df['FI'] = ta.volume.ForceIndexIndicator(df['close'], df['volume']).force_index()
        indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
        df['BB_High'] = indicator_bb.bollinger_hband()
        df['BB_Low'] = indicator_bb.bollinger_lband()
        df['BB_Middle'] = indicator_bb.bollinger_mavg()
        return df.tail(14).to_json()
    
    def test_price(self,ticker,start_date,end_date):
        df=ak.stock_us_daily(symbol=ticker, adjust="")
        df.set_index('date', inplace=True)
        return df.loc[start_date:end_date]
    
    def get_finetune_prompt(self,ticker):
        today=datetime.today().strftime('%Y-%m-%d')
        one_week_later = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        fundem_info=self.get_fundemental_info(ticker)
        #print(type(fundem_info))
        # fundem_info=json.loads(get_fundemental_info(ticker))
        company_profile="[Company Introduction]:\n\n "+fundem_info['Name']+" is a "+fundem_info['Sector']+" company. As of today, "+fundem_info['Name']+" has market capitalization of $"+fundem_info['MarketCapitalization']+" USD with "+ fundem_info['SharesOutstanding']+" shares outstanding."+ fundem_info['Name']+ "trades under the ticker "+ticker +"\n\n"
        financial="[Basic Financials]:\n\nReporting Period"+ fundem_info['LatestQuarter']+"\nQuarterly Revenue Growth YOY: "+str(float(fundem_info['QuarterlyRevenueGrowthYOY'])*100)+"%\nQuarterly Earnings Growth YOY: "+str(float(fundem_info['QuarterlyEarningsGrowthYOY'])*100)+"%\nProfit Margin: "+fundem_info['ProfitMargin']+"\n\n"

        ending="Based on all the information before "+today+", let's first analyze the positive developments and potential concerns for "+ticker+". Come up with 2-4 most important factors respectively and keep them concise. Most factors should be inferred from company related news. Then make your prediction of the "+ ticker+" stock price movement for next week ("+today+" - "+one_week_later+" ). Provide a summary analysis to support your prediction."
        two_week_ago=(datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
        one_week_ago=(datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        first_stock=self.test_price(ticker,two_week_ago,one_week_ago)
        first_fluctuate=(first_stock['close'].iloc[-1]-first_stock['close'].iloc[0])/first_stock['close'].iloc[0]
        second_stock=self.test_price(ticker,one_week_ago,today)
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

    
    def register_functions(self):
        def stringify_output(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                return str(result)

            return wrapper
    

        autogen.agentchat.register_function(
            stringify_output(self.get_price),
            caller=self.data_provider,
            executor=self.user_proxy,
            description="get the stock price data for a company and a series of technical indicator including MACD, RSI, EMA, ADI, FI, Bollinger Bands. The data will be returned as a JSON string.",
            name="get_stock_price",
        )
        autogen.agentchat.register_function(
            stringify_output(self.get_company_news),
            caller=self.data_provider,
            executor=self.user_proxy,
            description="get the latest news for a company",
            name="get_company_news"
        )
        autogen.agentchat.register_function(
            stringify_output(self.plot_stock_price_chart),
            caller=self.data_provider,
            executor=self.user_proxy,
            description="plot the stock price chart and save it to a file",
            name="plot_stock_price"
        )
        autogen.agentchat.register_function(
            stringify_output(self.get_macro_info),
            caller=self.data_provider,
            executor=self.user_proxy,
            description="get the macro information for a specific industry",
            name="get_macro_info"
        )
        autogen.agentchat.register_function(
            stringify_output(self.save_markdown_report),
            caller=self.saver,
            executor=self.user_proxy,
            description="Save the analysis to a markdown file",
            name="save_markdown_report"
        )
        autogen.agentchat.register_function(
            stringify_output(self.get_fundemental_info),
            caller=self.data_provider,
            executor=self.user_proxy,
            description="get the fundemental information of the company,it includes company overview, PE ratio, P/E ratio, Profit margin, Return on equity TTM, Quarterly earnings growth YOY, Quarterly revenue growth YOY, Analyst target price, Trailing PE, Beta",
            name="get_fundemental_info"
        )
        autogen.agentchat.register_function(
            stringify_output(self.rag_retrival),
            caller=self.data_provider,
            executor=self.user_proxy,
            description="get the related information from the existing internal research material from RAG retrieval system.",
            name="RAG_retrieval"



        )
   
    def run_analysis(self,ticker):
        self.ticker=ticker
        with Cache.disk(cache_seed=31) as cache:
            # user_input = self.user_proxy.get_human_input(self.get_finetune_prompt(self.ticker))
            # print(user_input)
            first_opinion = self.finetune.generate_reply(
                messages=[{"role": "user", "content": self.get_finetune_prompt(self.ticker)}]
            )

            print(first_opinion)
            if len(first_opinion)>0:
                self.user_proxy.send(message=first_opinion,recipient=self.writer,request_reply=False,silent=True)
            time.sleep(10)


            result = autogen.initiate_chats(
                [
                    {
                        "sender": self.user_proxy,
                        "recipient": self.data_provider,
                        "message": f"Gather information for {self.ticker}, including plot the stock price trend, news stock price. Save the graph in stock_price.png. Reply TERMINATE when the task is done. ",
                        "clear_history": False,
                        "silent": False,
                        "summary_method": "last_msg",
                    },
                ]
            )
            if len(result[0].chat_history) > 0:
                for i in result[0].chat_history:
                    if i['content']:
                        self.user_proxy.send(message=i['content'], recipient=self.market_an, request_reply=False, silent=True)
                        # self.user_proxy.send(message=i['content'], recipient=self.planner, request_reply=False, silent=True)
            time.sleep(60)
            market_content = autogen.initiate_chats(
                [{
                    "sender": self.user_proxy,
                    "recipient": self.market_an,
                    "message": "With the stock price chart provided, along with recent market news of the company, analyze the recent fluctuations of the stock and the potential relationship with market news. and write the report based on the framework provide from the planner, all the information should be based on the data provided in the history chat.",
                    "max_turns": 1,
                    "summary_method": "last_msg",
                    "clear_history": False,
                }]
            )
            if len(market_content[0].chat_history) > 0:
                self.user_proxy.send(message=market_content[0].chat_history[-1]['content'], recipient=self.writer, request_reply=False, silent=True)
                self.user_proxy.send(message=market_content[0].chat_history[-1]['content'], recipient=self.boss, request_reply=False, silent=True)
            time.sleep(10)
            fun_data1 = autogen.initiate_chats(
                [
                    {
                        "sender": self.user_proxy,
                        "recipient": self.data_provider,
                        "message": f"Gather fundemental info for {self.ticker} and its top 1 competitor.",
                        "clear_history": True,
                        "silent": False,
                        "summary_method": "last_msg",
                    },
                ]
            )
            if len(fun_data1[0].chat_history) > 0:
                for i in fun_data1[0].chat_history:
                    if i['content']:
                        self.user_proxy.send(message=i['content'], recipient=self.fundemental_an, request_reply=False, silent=True)
            time.sleep(30)
            fundemental_content = autogen.initiate_chats(
                [{
                    "sender": self.user_proxy,
                    "recipient": self.fundemental_an,
                    "message": f"The company is {self.ticker}, analyzing the company's fundemental and make comparison with the competitor. All the information should be based on the data provided in the history chat. Reply TERMINATE when the task is done.",
                    "max_turns": 1,
                    "summary_method": "last_msg",
                    "clear_history": False,
                }]
            )
            if len(fundemental_content[0].chat_history) > 0:
                self.user_proxy.send(message=fundemental_content[0].chat_history[-1]['content'], recipient=self.writer, request_reply=False, silent=True)
                self.user_proxy.send(message=fundemental_content[0].chat_history[-1]['content'], recipient=self.boss, request_reply=False, silent=True)
            time.sleep(120)
            macro_data = autogen.initiate_chats(
                [
                    {
                        "sender": self.user_proxy,
                        "recipient": self.data_provider,
                        "message": f"Gather macro info for {self.ticker}'s industry and macro info from rag system",
                        "clear_history": False,
                        "silent": False,
                        "summary_method": "last_msg",
                    },
                ]
            )
            if len(macro_data[0].chat_history) > 0:
                for i in macro_data[0].chat_history:
                    if i['content']:
                        self.user_proxy.send(message=i['content'], recipient=self.macro_en, request_reply=False, silent=True)
            time.sleep(120)
            macro_content = autogen.initiate_chats(
                [{
                    "sender": self.user_proxy,
                    "recipient": self.macro_en,
                    "message": f"Our company is {self.ticker},Based on the macro industry info, analyze the how the current macro industry situation would influence the company. All uld influence the company. All the information should be based on the data provided in the history chat. Reply TERMINATE when the task is done.",
                    "max_turns": 1,
                    "summary_method": "last_msg",
                    "clear_history": False,
                }]
            )
            if len(macro_content[0].chat_history) > 0:
                self.user_proxy.send(message=macro_content[0].chat_history[-1]['content'], recipient=self.writer, request_reply=False, silent=True)
                self.user_proxy.send(message=macro_content[0].chat_history[-1]['content'], recipient=self.boss, request_reply=False, silent=True)
            time.sleep(10)
            report_content = autogen.initiate_chats(
                [{
                    "sender": self.user_proxy,
                    "recipient": self.writer,
                    "message": "Write a report based on the analysis provided by the market analyst, fundamental analyst, and macro analyst. The report should follow the format provided. Reply TERMINATE when the task is done.",
                    "max_turns": 1,
                    "summary_method": "last_msg",
                    "clear_history": False,
                }]
            )
            if len(report_content[0].chat_history) > 0:
                self.user_proxy.send(message=report_content[0].chat_history[-1]['content'], recipient=self.boss, request_reply=False, silent=True)
            time.sleep(10)
            feedback_content = autogen.initiate_chats(
                [{
                    "sender": self.user_proxy,
                    "recipient": self.boss,
                    "message": "Review the report and provide feedback. Reply TERMINATE when the task is done.",
                    "max_turns": 1,
                    "summary_method": "last_msg",
                    "clear_history": False,
                }]
            )
            if len(feedback_content[0].chat_history) > 0:
                self.user_proxy.send(message=feedback_content[0].chat_history[-1]['content'], recipient=self.writer, request_reply=False, silent=True)
            time.sleep(30)
            final_report_content = autogen.initiate_chats(
                [{
                    "sender": self.user_proxy,
                    "recipient": self.writer,
                    "message": "Revise the report based on the feedback provided by the boss. Reply TERMINATE when the task is done.",
                    "max_turns": 1,
                    "summary_method": "last_msg",
                    "clear_history": False,
                }]
            )
            if len(final_report_content[0].chat_history) > 0:
                self.user_proxy.send(message=final_report_content[0].chat_history[-1]['content'], recipient=self.saver, request_reply=False, silent=True)
            time.sleep(60)
            save_report_content = autogen.initiate_chats(
                [{
                    "sender": self.user_proxy,
                    "recipient": self.saver,
                    "message": "Save the final report to a markdown file. Reply TERMINATE when the task is done.",
                    "summary_method": "last_msg",
                    "clear_history": False,
                }]
            )
            # if len(save_report_content[0].chat_history) > 0:
            #     print(save_report_content[0].chat_history[-1]['content'])

if __name__ == "__main__":
    analysis = MarketAnalysis()
    analysis.run_analysis("NVDA")