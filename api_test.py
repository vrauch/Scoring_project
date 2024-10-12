import os
from openai import OpenAI
import openai


# Replace 'your_api_key_here' with your actual OpenAI API key
openai.api_key = os.environ['OPENAI_API_KEY']
print(openai.api_key)
def test_openai_key():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            prompt="This is a test of the OpenAI API.",
            max_tokens=5
        )
        print("API key is valid. Here's a sample response:")
        print(response.choices[0].text.strip())
    except Exception as e:
        print("Failed to validate API key:", str(e))

test_openai_key()
