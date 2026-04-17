import requests
from app.config import settings
import json
import base64

with open("alembic.ini", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": f"Bearer {settings.openrouter_api_key}",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "qwen/qwen3-next-80b-a3b-instruct:free",
    "messages": [
      {
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": "What is this?"}
        ]
      }
    ]
  })
)
print("Status Code:", response.status_code)
print("Response:", response.text)
