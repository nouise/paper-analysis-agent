"""Debug script for chat API via FastAPI test client"""
import asyncio
import os
import sys

# Add project to path
sys.path.insert(0, r"D:\2026\个人简历\InterestingWork\paper-analysis-agent")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_chat_in_context():
    """Test the chat API in FastAPI context"""
    from main import chat_completion, ChatRequest, ChatMessage

    # Create a mock request
    request = ChatRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        stream=False
    )

    try:
        result = await chat_completion(request)
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_in_context())
