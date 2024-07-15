import requests
import json
import pandas as pd
api_key="LS5RN88HLIZU7NOH"
def get_news_google(ticker_symbol: str):
    url = "https://google.serper.dev/news"

    payload = json.dumps({
    "q": ticker_symbol,
    "num": 30
    })
    headers = {
    'X-API-KEY': 'f6cb1d0f809bb567e76fcdb677415bbb903bdcac',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    result=response.text['news']
    text=""
    if result is not None:
        for i in result:
            if i['title'] is not None:
                text=text+"[News Title]:"+i['title']
            else:
                text=text+"[News Title]:None"
            if i['snippet'] is not None:
                text=text+"[News Content]:"+i['snippet']
            elif i['section'] is not None:
                text=text+"[News Content]:"+i['section']
            else:
                text=text+"[News Content]:None"
    return text

def get_news_alpha_vintage(ticker_symbol: str):
    url=f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker_symbol}&apikey={api_key}"
    print(url)
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
        return 



def get_news(ticker_symbol) -> str:
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
    


print(get_news("AAPL"))
