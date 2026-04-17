import os
from google import genai
from app.config import settings

client = genai.Client(api_key=settings.google_api_key)
for model in client.models.list():
    if "gemini" in model.name.lower():
        print(model.name)
