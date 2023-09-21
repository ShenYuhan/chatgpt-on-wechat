from typing import List
import numpy as np
import requests
import json
from ..config import config

class ErnieEncodeText:
    def __init__(
        self,
    ):
        self.token = ""

    def get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        if self.token != "":
            return self.token
        token = config.get("ernie_token", "")
        if token != "":
            self.token = token
            return self.token
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": config.get("ernie_bot", {}).get("ak", ""), "client_secret": config.get("ernie_bot", {}).get("sk", "")}
        token = str(requests.post(url, params=params).json().get("access_token"))
        config["ernie_token"] = token
        self.token = token
        return self.token

    def __call__(self, all_contents: List[str]):
        if not isinstance(all_contents, List):
            all_contents = [all_contents]
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embedding-v1?access_token=" + self.get_access_token()
        payload = json.dumps({
            "input": all_contents,
        })

        headers = {
            'Content-Type': 'application/json'
        }
    
        response = requests.request("POST", url, headers=headers, data=payload)
        datas = response.json().get("data", None)
        if not datas:
            return None

        embeddings = np.array([v["embedding"] for v in datas])

        return embeddings
    
    def chat_completions(self, prompt, history=None, **kwargs):
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token=" + self.get_access_token()
    
        if not history:
            history = []

        temperature = kwargs.get('temperature', 0.95)
        top_p = kwargs.get('top_p', 0.8)

        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": temperature,
            "top_p": top_p,
        })
    
        response = requests.request("POST", url, headers=headers, data=payload)
        
        return response.text

if __name__ == '__main__':
    eet = ErnieEncodeText()
    eet(["今天天气真好", "我爱中国"])