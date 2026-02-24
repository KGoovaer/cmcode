import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = "https://ae-ai-coding-agent-workshop.cognitiveservices.azure.com/openai/v1/"

model_name = "gpt-4o"

deployment_name = "gpt-4o"


api_key = os.environ.get("AZURE_OPENAI_API_KEY")


client = OpenAI(
    base_url=f"{endpoint}",
    api_key=api_key
)


def send_to_llm(conversation):
    """Send the entire conversation history to the LLM and return the response."""
    completion = client.chat.completions.create(
        model=deployment_name,
        messages=conversation,
    )
    return completion.choices[0].message.content


def main():
    print("Chat with the LLM. Type 'exit' to quit.\n")
    
    # Initialize conversation history list
    conversation = []
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        # Add user message to conversation history
        conversation.append({"role": "user", "content": user_input})
        
        # Send entire conversation to LLM
        response = send_to_llm(conversation)
        
        # Add assistant response to conversation history
        conversation.append({"role": "assistant", "content": response})
        
        print(f"Assistant: {response}\n")


if __name__ == "__main__":
    main()