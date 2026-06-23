"Simple Chat example using MCP Agent with built-in conversation memory"


import asyncio
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from mcp_use import MCPAgent, MCPClient

async def run_memory_chat():
    """Run a chat using MCP Agent with built-in conversation memory"""
    #Load Environment Variables
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model="openai/gpt-oss-20b")
    

    #Config file Path
    config_file = "browser_mcp.json"
    
    print("Initializing Chat...")
    
    #Create MCP Client and agent with memory enabled
    client = MCPClient.from_config_file(config_file)
    
    #Create agent with memory enabled=True
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=15,
        memory_enabled=True,
    )
    
    print("\n===== Interactive MCP Chat ======")
    print("Type 'exit' or 'quit' to end the chat")
    print("Type 'clear' to clear the conversation memory")
    print("=============================\n")
    
    try:
        #Main chat loop
        while True:
            #Get user input
            user_input = input("\nYou: ")
            
            #Check for exit commands
            if user_input.lower() in ["exit", "quit"]:
                print("Ending Conversation...")
                break
            
            #Check for clear History Command
            if user_input.lower() == "clear":
                agent.clear_conversation_history()
                print("Conversation history cleared.")
                continue
            
            #Get response from agent
            print("\nAssistant: ", end="", flush=True)
            
            try:
                #Run the Agent with the user input(memory handling is automatic)
                response = await agent.run(user_input)
                print(response)
                
            except Exception as e:
                print(f"\nError: {e}")
                
                
    finally:
        #Clean up
        if client and client.sessions:
            await client.close_all_sessions()
            
if __name__ == "__main__":
    asyncio.run(run_memory_chat())