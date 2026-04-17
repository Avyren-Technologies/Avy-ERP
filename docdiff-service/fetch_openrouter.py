import requests
import json

response = requests.get("https://openrouter.ai/api/v1/models")
models = response.json().get("data", [])

free_models = []
for m in models:
    arch = m.get("architecture", {})
    pricing = m.get("pricing", {})
    
    # Check if free
    is_free = False
    if "prompt" in pricing and float(pricing["prompt"]) == 0.0:
        is_free = True
        
    if is_free:
        free_models.append(m["id"])
        
print("Free Models:")
for f in free_models:
    if "gemini" in f:
        print(f)
