"""Debug script for chat API"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_chat():
    """Test the chat API directly"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    print(f"API Key first 10 chars: {api_key[:10] if api_key else 'None'}...")

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        messages = [{"role": "user", "content": "Hello"}]

        print("Sending request to DashScope...")
        response = await client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            stream=False
        )

        print(f"Response received!")
        print(f"Content: {response.choices[0].message.content}")
        print(f"Usage: {response.usage}")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())
