import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = "https://ae-ai-coding-agent-workshop.cognitiveservices.azure.com/openai/v1/"

model_name = "gpt-4o"

deployment_name = "gpt-4o"


api_key = os.environ.get("AZURE_OPENAI_API_KEY")

# 1. Define the Tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_secret",
            "description": "Gets the magical secret value"
        }
    }
]


client = OpenAI(
    base_url=f"{endpoint}",
    api_key=api_key
)

# Load system prompt from file
def load_system_prompt():
    """Load the system prompt from system-prompt.md file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(script_dir, "system-prompt.md")
    with open(prompt_path, "r") as f:
        return f.read().strip()


def execute_tool(tool_name, tool_arguments):
    """Execute the requested tool and return the result."""
    if tool_name == "get_secret":
        # Return the hardcoded secret value
        return "42"
    else:
        return f"Unknown tool: {tool_name}"


def send_to_llm(conversation):
    """Send the entire conversation history to the LLM and return the response."""
    # 2. Include Tools in API Call
    completion = client.chat.completions.create(
        model=deployment_name,
        messages=conversation,
        tools=tools
    )
    return completion.choices[0].message


def main():
    print("Chat with the LLM. Type 'exit' to quit.\n")
    
    # Load system prompt and initialize conversation with it
    system_prompt = load_system_prompt()
    conversation = [{"role": "system", "content": system_prompt}]
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        # Add user message to conversation history
        conversation.append({"role": "user", "content": user_input})
        
        # 6. Handle the Loop - Keep calling LLM until we get a final response
        while True:
            # Send entire conversation to LLM
            response_message = send_to_llm(conversation)
            
            # 3. Detect Tool Call Requests
            if response_message.tool_calls:
                # Add the assistant's tool call message to conversation
                conversation.append(response_message.model_dump())
                
                # 4. Execute the Tool
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = tool_call.function.arguments
                    
                    print(f"[Tool Call] Executing: {function_name}")
                    
                    # Execute the tool
                    result = execute_tool(function_name, function_args)
                    
                    # Add tool result to conversation
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
                # 5. Continue the Conversation - Loop will call LLM again
            else:
                # No more tool calls, we have the final response
                final_response = response_message.content
                conversation.append({"role": "assistant", "content": final_response})
                print(f"Assistant: {final_response}\n")
                break


if __name__ == "__main__":
    main()