from openai import OpenAI

class LLM:
    def __init__(self):
        self.api_key = "sk-qgspupbsugmoknadoxohwuquyjfgtaljqspethzzywthvhgx"
        self.base_url = "https://api.siliconflow.cn/v1"
        self.model = "THUDM/glm-4-9b-chat"
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
        
        for chunk in response:
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content
            if token:
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