from collections import defaultdict
from pyexpat.errors import messages
import pandas as pd
import time
from db_config import execute_query, execute_query_commit
import os

# Set OpenAI API key
import openai
from openai import OpenAI
client = OpenAI (api_key = os.getenv('OPENAI_API_KEY'))

# Function to get capability and level data with descriptions
def feature_analysis():

    query = """
    SELECT c.capability_id, c.capability_name, cd.level, cd.capability_at_level, MIN(l.description) AS level_description
    FROM e2caf.Capabilities AS c
    JOIN e2caf.CapabilityDetails AS cd ON c.capability_id = cd.capability_id
    LEFT JOIN e2caf.LevelDefinitions AS l ON cd.level = l.level
    group by c.capability_id, c.capability_name, cd.level, cd.capability_at_level
    """

    results = execute_query(query)
    # print(results)
    return pd.DataFrame(results)  # Convert query results to DataFrame

# Function to generate new quantitative features using AI
def generate_ai_features(capability_name, capbility_at_level, level, level_description):
    prompt = f"""
    Generate 3-5 new, qualitative, and measurable features for the following:
    Capability_Name: {capability_name}
    Capability_at_level: {capbility_at_level}
    Maturity Level: {level}
    Level Description: {level_description}

    The features should be:
    1. Specific and relevant to the capability at level and the level description
    2. Qualatativly measurable
    3. Indicative of the maturity level
    5. plain text only no bullets or numbering just plain text.

    Output the features as a comma-separated list.
    """

    try:
        # Use the latest ChatCompletion API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
            messages=[
                {"role": "system", "content": "You are a helpfull assistant that generates features basedon given infomration."},
                {"role":"user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        # print(messages)

        # Extract the response text
        reply_content = response.choices[0].message.content
        # print(reply_content)

        # Return the response as a list of features
        return reply_content.strip().split(', ')

    except Exception as e:
        print(f"Error generating AI features: {e}")
        return []

# Generate the features and save them in an output list
output = []

# Assuming feature_analysis() is defined and returns a DataFrame with the necessary data
data = feature_analysis()  # Get all necessary data from a single query

# Use a defaultdict to group features
grouped_features = defaultdict(list)

for _, row in data.iterrows():
    # time.sleep(1)  # Optional: Adjust delay based on your OpenAI usage limits
    features = generate_ai_features(
        row['capability_name'],
        row['capability_at_level'],
        row['level'],
        row['level_description']
    )

    # Create a key for grouping
    key = (row['capability_id'], row['capability_name'],
           row['capability_at_level'], row['level'])

    # Add features to the group
    grouped_features[key].extend(features)

    # Generate the features and save them in an output list
    output = []

    for key, features in grouped_features.items():
        capability_id, capability_name, capability_at_level, level = key
        output.append({
            'Capability_ID': capability_id,
            'Capability': capability_name,
            'Capability_at_Level': capability_at_level,
            'Level': level,
            'Features': '| '.join(features)  # Join all features with a semicolon
        })


    # Loop over each item in output and update the database based on capability_id and level
    for row in output:
        capability_id = row['Capability_ID']
        level = row['Level']
        features = row['Features'] if pd.notnull(row['Features']) else None  # Replace NaN with None

        # Construct the SQL UPDATE query
        update_query = """
        UPDATE e2caf.CapabilityDetails
        SET features = %s
        WHERE capability_id = %s AND level = %s
        """

        # Execute the update with parameters
        execute_query_commit(update_query, (features, capability_id, level))
    print(f"feature updated for capability:", capability_id, "at level:", level)

# Convert to DataFrame and save to CSV
"""
output_df = pd.DataFrame(output)
output_df.to_csv('output/AI_Generated_Capability_Features.csv', index=False)
"""
# Display the first few rows of the output
# print(output_df.head(10))
