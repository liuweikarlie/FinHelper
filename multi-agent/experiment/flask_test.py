import requests

def send_question(question):
    url = 'http://localhost:5000/api/ask'  # 远程服务器的地址和端口
    payload = {'question': question}
    response = requests.post(url, json=payload)
    return response.json()['answer']

# 使用函数
question = "你是谁？"
answer = send_question(question)
print(f"QA 系统的回答是: {answer}")