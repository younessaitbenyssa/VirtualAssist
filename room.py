import os
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()


class ClassifiyIntent:
    def __init__(self):
        self.url = "https://api.hyperbolic.xyz/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv("LLM_API_KEY")}"
        }
        self.model = "deepseek-ai/DeepSeek-V3"

    async def sendmessage(self, input_message):
        print("the user said" + input_message)
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify user inputs into specific intents:\n\n"
                        "1. For 'set the volume to 80%, or did you underatand that you need to adjust the volume' return {'intent':'volume_up', 'level':80} as json.\n"
                        "2. For 'set the brightness to 29% or you understand that you need to adjust the brightness' return {'intent':'light_up', 'level':29} as json.\n"
                        "3. For 'opening a software' (e.g., open x) return {'intent': 'open_soft', 'softname': 'x'} as json.\n"
                        "4. For 'closing a software,' return {'intent':'close_soft', 'softname':'x'} as json.\n"
                        "5. For sending messages (e.g., 'send X to Y'), return {'intent': 'send_message', 'contact': 'Y', 'message': 'X'} as json .\n"
                        "6. For browser search queries, detect specific keywords like 'look up,' 'search for,' 'google,' 'find out about,' or 'can you search.' "
                        "Return {'intent':'search_browser', 'query':'X'} as json.\n"
                        "   - Example: 'Search for the capital of France.' → {'intent':'search_browser', 'query':'the capital of France'}.\n"
                        "   - If these keywords are absent, classify the input as a general question.\n"
                        "7. For general questions unrelated to the above intents, just return None.\n\n"
                        "Respond strictly in the specified format without additional text or explanations."
                    ),
                },
                {
                    "role": "user",
                    "content": input_message,
                },
            ],
            "model": self.model,
            "max_tokens": 100,
            "temperature": 0.1,
            "top_p": 0.9
        }

        try:
            response = await asyncio.to_thread(
                requests.post, self.url, headers=self.headers, json=data
            )
            response.raise_for_status()
            response_data = response.json()

            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            print(content)

            if content.lower() == "none":
                return None
            return content
        except Exception as e:
            print(f"Error in ClassifiyIntent.sendmessage: {e}")
            return None
