import anthropic
import asyncio
from app.config import settings

async def main():
    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        # Test a simple chat request with Claude 3.5/3.7 Sonnet
        models = ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
        
        for model in models:
            print(f"Testing model: {model} ...")
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=100,
                    messages=[{"role": "user", "content": "What is the meaning of life? Return just one word."}]
                )
                text = response.content[0].text
                print(f"SUCCESS: {model} responded: {text}\n")
                break # We found a working one, no need to test next
            except Exception as e:
                print(f"FAILED on {model}: {e}\n")
    except Exception as e:
        print("Initialization Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
