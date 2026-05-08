from openai import OpenAI
from desktop.LLM.api_key import api_key

class LLM:
    def __init__(self):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1"
        self.model = "deepseek-ai/DeepSeek-V4-Flash"
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
    def send_message(self, message):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=message,
            stream=True
        )
        
        first_token = True
        for chunk in response:
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content
            if token:
                if first_token:
                    token = token.lstrip("\n")
                first_token = False
                yield token
        
if __name__ == "__main__":
    llm = LLM()
    message = [
        {
            "role": "user",
            "content": "请告诉我什么是橘子洲。"
        }
    ]
    llm.send_message(message)