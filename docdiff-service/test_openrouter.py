import requests
import json
from app.config import settings

# Test a list of models
models_to_test = [
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
]

for model in models_to_test:
    response = requests.post(
      url="https://openrouter.ai/api/v1/chat/completions",
      headers={
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
      },
      data=json.dumps({
        "model": model,
        "messages": [
          {
            "role": "user",
            "content": "Hi"
          }
        ]
      })
    )
    print(f"{model} Status: {response.status_code}")
