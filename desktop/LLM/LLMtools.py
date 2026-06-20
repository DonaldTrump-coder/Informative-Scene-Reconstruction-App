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
                
    def send_with_tools(self, messages, tools):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            stream=True,
        )
        tool_buf = {}
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                yield ("text", delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_buf:
                        tool_buf[idx] = {"id": tc.id or "", "name": "", "arguments": ""}
                    buf = tool_buf[idx]
                    if tc.id:
                        buf["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            buf["name"] += tc.function.name
                        if tc.function.arguments:
                            buf["arguments"] += tc.function.arguments
        for buf in tool_buf.values():
            if buf["name"]:
                yield ("tool_call", {
                    "id": buf["id"],
                    "type": "function",
                    "function": {
                        "name": buf["name"],
                        "arguments": buf["arguments"],
                    }
                })
        
if __name__ == "__main__":
    llm = LLM()
    message = [
        {
            "role": "user",
            "content": "请告诉我什么是橘子洲。"
        }
    ]
    llm.send_message(message)