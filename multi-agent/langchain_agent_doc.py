from langchain_openai import ChatOpenAI
from langchain_experimental.plan_and_execute import PlanAndExecute,load_chat_planner,load_agent_executor
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents.tools import Tool
from langchain import LLMMathChain
from langchain.agents import AgentType
import akshare as ak
from langchain_experimental.utilities import PythonREPL

from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


import os
import yfinance as yf
from langchain.agents import initialize_agent, Tool

from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool

from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama


# os.environ["GROQ_API_KEY"] = "api"
os.environ['SERPER_API_KEY']='f6cb1d0f809bb567e76fcdb677415bbb903bdcac'

class qna:

    def __init__(self) -> None:
        self.search = GoogleSerperAPIWrapper(serper_api_key="f6cb1d0f809bb567e76fcdb677415bbb903bdcac")
        # if you don't want to install the llama3 model on local machine, you can use the groq model instead
        self.model=ChatOllama(base_url="http://localhost:6000",model="llama3")
        # self.model = ChatGroq(temperature=0, model_name="llama3-70b-8192")
        self.financial_tool=YahooFinanceNewsTool()
        self.llm_math_chain = LLMMathChain.from_llm(llm=self.model, verbose=True)
        self.search_wrap=DuckDuckGoSearchAPIWrapper(time="d",max_results=10)
        self.free_search=DuckDuckGoSearchResults(api_wrapper=self.search_wrap,backend="news")
        self.python_repl=PythonREPL()
        self.tools = [
    # Tool(
    #     name = "Search",
    #     func=self.search.run,
    #     description="useful for when you need to answer questions about current event"
    # ),
    # Tool(
    #     name="Calculator",
    #     func=self.llm_math_chain.run,
    #     description="useful for when you need to answer questions about math"
    # ),
    # Tool(
    #     name="Financial News",
    #     func=self.financial_tool.run,
    #     description="useful for when you need to answer questions about financial news, please input the company name, not stock ticker"
    # ),
    Tool(
        name="Python reply",
        func=self.python_repl.run,
        description="useful for when you need to use python to answwer a question (draw graph or do calculation or get stock price from yfinance). You should input python code, don't use it for other complex task. "
    ),
    Tool(
        name="DuckDuckGo Search",
        func=self.free_search.run,
        description="useful when you need to do a search on the internet to find information that another tool can't find. be specific with your input"
    )
    # Tool(
    #     name="Get stock price",
    #     func=self.get_stock_price,
    #     description="Getting stock price for a ticker within a period,input ticker, starting date and end date, the start/end date input format example '2024-01-01'"
    # )
    ]
    @tool
    def get_stock_price(self,ticker:str,start_date:str,end_date:str)->str:
        """Get stock price for the ticker, with start date and end date """
        df=yf.download(ticker, start=start_date, end=end_date)
        return df.to_json()

    def run(self, prompt,st_callback):
        self_ask_with_search = initialize_agent(
                self.tools, self.model, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True,
                )
        
        response=self_ask_with_search.run(
                prompt,
                callbacks=[st_callback]
                )
        return response

