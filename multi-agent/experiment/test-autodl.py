import openai 
# reference https://zhuanlan.zhihu.com/p/692686053
# reference https://blog.csdn.net/u011423880/article/details/138069616
# reference autodl ssh : 下载AutoDL SSH隧道工具, 输入ssh 号码和密码和port：4000
client = openai.OpenAI(api_key="anything",base_url="http://localhost:4000") # set proxy to base_url
response = client.chat.completions.create(model="anything", 
    messages = [
    {
        "role": "user",
        "content": "hi"
    }
])

print(response)


