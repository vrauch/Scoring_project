import os

import pandas as pd
import openai
from openai import OpenAI
from os import environ


# Set your OpenAI API key (replace with your actual key)
openai.api_key = os.environ['OPENAI_API_KEY']

# Initialize the OpenAI client
client = OpenAI(api_key=openai.api_key)

def analyze_alignment(criteria, text):
    # Create a prompt for the model
    prompt = f"""You are trained to analyze and determine the alignment strength between the given criteria and text. If you are unsure of an answer, you can say "not sure" and recommend the user review manually. Analyze the following criteria and text pair and determine the alignment strength: Criteria: {criteria} Text: {text}"""

    # Call the OpenAI API to generate a response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use a powerful model for analysis
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1,  # Limit response to a single word
        temperature=0  # Keep response consistent
    )

    # Extract the alignment strength from the response
    alignment_strength = response.choices.message.content.strip().lower()

    return alignment_strength


# Load your spreadsheet data into a pandas DataFrame
df = pd.read_excel('response.xlsx')

# Iterate over each row in the DataFrame and perform analysis
results = []
for index, row in df.iterrows():
    capability = row['Capability']
    criteria = row['Criteria']
    text = row['Text']

    alignment_strength = analyze_alignment(criteria, text)

    # Generate justification based on alignment strength (you can customize this logic)
    if alignment_strength == 'fully aligned':
        justification = "The text aligns perfectly with the criteria."
    elif alignment_strength == 'partially aligned':
        justification = "There are some similarities between the text and criteria but not a complete match."
    else:
        justification = "There is no significant alignment between the text and criteria."

    results.append(f"{alignment_strength}, {justification}")

# Save results to a new CSV file
output_df = pd.DataFrame(results, columns=['Capability, Alignment Strength, Justification'])
output_df.to_csv('alignment_results.csv', index=False)