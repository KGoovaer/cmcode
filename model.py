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
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the contents of a file and returns it as a string",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file. Creates the file if it doesn't exist, overwrites if it does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path where the file should be written"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
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
    elif tool_name == "read_file":
        # Parse arguments from JSON
        arguments = json.loads(tool_arguments)
        file_path = arguments.get("file_path")
        
        if not file_path:
            return "Error: file_path parameter is required"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' not found"
        
        try:
            # Read the file contents
            with open(file_path, "r", encoding="utf-8") as f:
                contents = f.read()
            return contents
        except Exception as ex:
            return f"Error reading file: {str(ex)}"
    elif tool_name == "write_file":
        # Parse arguments from JSON
        arguments = json.loads(tool_arguments)
        file_path = arguments.get("file_path")
        content = arguments.get("content")
        
        if not file_path:
            return "Error: file_path parameter is required"
        if content is None:
            return "Error: content parameter is required"
        
        # Security: Size limit (1MB)
        MAX_FILE_SIZE = 1_000_000
        if len(content) > MAX_FILE_SIZE:
            return f"Error: Content exceeds {MAX_FILE_SIZE} byte limit"
        
        # Security: Directory sandboxing - restrict to workspace directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        allowed_directory = os.path.abspath(script_dir)
        full_path = os.path.abspath(file_path)
        
        if not full_path.startswith(allowed_directory):
            return f"Error: Can only write files within {allowed_directory}"
        
        # Security: Blocklist sensitive paths
        BLOCKED_PATTERNS = [".ssh", ".bashrc", ".zshrc", ".env", "id_rsa", "/etc/", "/usr/", ".git/"]
        if any(pattern in full_path for pattern in BLOCKED_PATTERNS):
            return "Error: Cannot write to sensitive locations"
        
        try:
            # Check if file exists and ask for confirmation
            if os.path.exists(file_path):
                confirm = input(f"File '{file_path}' already exists. Overwrite? [y/N]: ")
                if confirm.lower() != 'y':
                    return f"Write cancelled: File '{file_path}' was not overwritten"
            
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write the file contents
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {file_path}"
        except Exception as ex:
            return f"Error writing file: {str(ex)}"
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