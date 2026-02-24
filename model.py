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


def send_to_llm(user_input):
    completion = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {
                "role": "user",
                "content": user_input,
            }
        ],
    )
    return completion.choices[0].message.content


def main():
    print("Chat with the LLM. Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        response = send_to_llm(user_input)
        print(f"Assistant: {response}\n")


if __name__ == "__main__":
    main()