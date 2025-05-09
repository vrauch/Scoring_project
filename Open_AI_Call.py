from helper_functions import error, info
import os
from openai import OpenAI
#client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url="https://api.deepseek.com")
client = OpenAI()

# --- Configure OpenAI Client ---
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")

    client = OpenAI(api_key=api_key)
    # For alternate base_url (e.g. DeepSeek), uncomment:
    # client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

except Exception as e:
    error(f"Failed to initialize OpenAI client: {e}")
    raise

# import openai
# Call OpenAI API
#def ai_call(prompt, model, temperature, max_tokens):
#    response = openai.ChatCompletion.create(
##        model=model,
#        messages=[
#            {"role": "system",
#             "content": "You are an expert in generating maturity assessments for organizational capabilities."},
#            {"role": "user", "content": prompt}
#        ],
#        temperature=temperature,
#        max_tokens=max_tokens
#    )
#    info(f"API response: {response}")
#    return response

# --- API Call Function ---
def ai_call(prompt, model, temperature, max_tokens):
    info(f"Calling OpenAI with: model={model}, temp={temperature}, max_tokens={max_tokens}")
    info(f"Types: model={type(model)}, temp={type(temperature)}, max_tokens={type(max_tokens)}")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in generating maturity assessments for organizational capabilities."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        info("OpenAI API call succeeded.")
        return response
    except Exception as e:
        error(f"OpenAI API call failed: {e}")
        raise