"""
api.py — HTTP wrapper for the frontend.
Imports agent config from app.py (untouched).
app.py is never modified.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

load_dotenv(override=True)

# Force UTF-8 output on Windows (cp1252 can't encode emoji from mcp_use logs)
if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

def get_llms():
    primary = ChatMistralAI(
        model="mistral-large-latest",
        api_key=os.getenv("MISTRAL_API_KEY"),
        max_tokens=2048
    )
    backup = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_tokens=2048
    )
    return primary, backup

async def run_once(message: str) -> str:
    place_ids = {
        "goa": "ChIJQbc2YxC6vzsRkkDzYv-H-Oo",
        "mumbai": "ChIJwe1EZjDG5zsRaYxkjY_tpF0",
        "delhi": "ChIJLbZ-NFv9DDkRzk0gLkGdk10",
        "new york": "ChIJOwg_06VPwokRYv534QaPC8g",
        "london": "ChIJdd4hrwug2EcRmSrV3Vo6llI",
        "paris": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
        "bangalore": "ChIJ5VBo_cQOrjsR6KKnEOeB7n8",
        "dubai": "ChIJRcbZaklDXz4RYlEphFBu5r0",
    }
    msg_lower = message.lower()
    for city, pid in place_ids.items():
        if city in msg_lower and "airbnb" in msg_lower:
            message = f"{message} (use placeId='{pid}' for the airbnb_search call)"
            break

    primary, backup = get_llms()
    config_file = os.path.join(os.path.dirname(__file__), "browser_mcp.json")
    

    for llm, name in [(primary, "Mistral"), (backup, "Gemini")]:
        client = MCPClient.from_config_file(config_file)
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=10,
            memory_enabled=False,
            system_prompt=(
                "You are a helpful assistant. "
                "When using tavily_search, always set topic to one of: 'general', 'news', or 'finance'. "
                "Never use any other topic value. "
                "When using tavily_search with a time_range, use only: 'day', 'week', 'month', or 'year'. "
                "Never use 'last week', 'last month', or any other phrase — only the single word values above. "
                "When using airbnb_search, always use the placeId parameter instead of location string. "
                "Use these placeIds: Goa='ChIJQbc2YxC6vzsRkkDzYv-H-Oo', "
                "Mumbai='ChIJwe1EZjDG5zsRaYxkjY_tpF0', "
                "Delhi='ChIJLbZ-NFv9DDkRzk0gLkGdk10', "
                "New York='ChIJOwg_06VPwokRYv534QaPC8g', "
                "London='ChIJdd4hrwug2EcRmSrV3Vo6llI', "
                "Paris='ChIJD7fiBh9u5kcRYJSMaMOCCwQ'. "
                "For any other city, use the location string as fallback. "
                "Never use browser tools unless the user explicitly asks to browse a website. "
                "Do not use browser_navigate as a fallback when other tools fail."
            )
        )
        try:
            print(f"[{name}] Trying...", flush=True)
            response = await agent.run(message)
            return response
        except Exception as e:
            print(f"[{name}] Failed: {e}", flush=True)
        finally:
            if client and client.sessions:
                await client.close_all_sessions()

    return "Error: Both models failed."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python api.py <message>")
        sys.exit(1)
    result = asyncio.run(run_once(sys.argv[1]))
    print(result, flush=True)