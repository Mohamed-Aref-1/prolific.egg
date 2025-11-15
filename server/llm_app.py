import os
import threading
from dotenv import load_dotenv
from openai import AzureOpenAI

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")

# Load environment variables from .env file in the same directory as the script
load_dotenv(env_path)

# LLM API Configuration from environment variables
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")

# Thread-local storage for the client
thread_local = threading.local()

def get_client():
    """Get thread-local Azure OpenAI client"""
    if not hasattr(thread_local, 'client'):
        if not AZURE_API_KEY or not AZURE_ENDPOINT:
            raise ValueError("Azure OpenAI API key and endpoint must be set in .env file")
        thread_local.client = AzureOpenAI(
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION,
            azure_endpoint=AZURE_ENDPOINT
        )
    return thread_local.client

def load_prompt_template():
    """Load the prompt template from prompt.txt file"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(script_dir, "prmopt_dir", "prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("Error: prompt.txt file not found!")
        return None
    except Exception as e:
        print(f"Error reading prompt.txt: {e}")
        return None

def get_llm_response(user_question, prompt_template):
    """Send the user question to the LLM API and get the response"""
    try:
        # Get the Azure OpenAI client
        client = get_client()
        
        # Append the user question to the prompt template
        full_prompt = prompt_template + f"\n\n<user_message>\n{user_question}\n</user_message>"
        
        # Send request to LLM API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7
        )
        
        # Extract and return the answer
        answer = response.choices[0].message.content
        return answer
        
    except Exception as e:
        return f"Error getting response from LLM: {e}"

def main():
    """Main function to run the app"""
    print("=" * 50)
    print("LLM Question Answering App")
    print("=" * 50)
    print()
    
    # Load the prompt template
    prompt_template = load_prompt_template()
    if prompt_template is None:
        return
    
    # Main loop
    while True:
        print("Enter your question (or 'quit' to exit):")
        user_question = input("> ").strip()
        
        if user_question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_question:
            print("Please enter a valid question.\n")
            continue
        
        print("\nProcessing your question...")
        
        # Get the answer from LLM
        answer = get_llm_response(user_question, prompt_template)
        
        print("\nAnswer:")
        print("-" * 50)
        print(answer)
        print("-" * 50)
        print()

if __name__ == "__main__":
    main()
