import openai
from openai import OpenAI
import pandas as pd
import os
import logging
from packaging import version


# ---------------------------
# Configuration Setup
# ---------------------------

def setup_logging():
    logging.basicConfig(
        filename='maturity_assessment_errors.log',
        level=logging.ERROR,
        format='%(asctime)s:%(levelname)s:%(message)s'
    )
    # print("Logging setup complete.")


def setup_openai_api():
    openai.api_key = os.getenv('OPENAI_API_KEY')
    openai_version = openai.__version__
    response_access_method = "attribute" if version.parse(openai_version) >= version.parse("0.27.0") else "dictionary"
    # print(f"Using OpenAI library version: {openai_version}")
    return response_access_method


# ---------------------------
# Load Input Data
# ---------------------------

def load_input_data(input_csv_path, required_columns):
    try:
        capabilities_df = pd.read_csv(input_csv_path)
        # print(f"Columns in input CSV: {capabilities_df.columns.tolist()}")
    except FileNotFoundError:
        logging.error(f"CSV file not found at path: {input_csv_path}")
        raise FileNotFoundError("CSV file not found.")

    # Normalize column names
    capabilities_df.columns = capabilities_df.columns.str.strip().str.lower()
    required_columns = [col.lower() for col in required_columns]

    # Validate required columns
    missing_cols = [col for col in required_columns if col not in capabilities_df.columns]
    if missing_cols:
        logging.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    # print(f"Input data loaded successfully with {len(capabilities_df)} rows.")
    # print(f"Columns in input CSV: {capabilities_df.columns.tolist()}")
    # print(capabilities_df.head())
    return capabilities_df


# ---------------------------
# Maturity Levels
# ---------------------------

def define_maturity_levels():
    return {
        1: "Ad Hoc Processes: Processes are unstructured, reactive, and chaotic. Success depends on individual effort.",
        2: "Basic Processes: Processes are documented and repeatable but may not be standardized across the organization.",
        3: "Defined Processes: Processes are standardized, documented, and integrated across the organization.",
        4: "Quantitatively Managed: Processes are measured and controlled using quantitative performance metrics.",
        5: "Optimizing: Focus on continuous process improvement through innovation and proactive management."
    }


# ---------------------------
# Generate Prompt
# ---------------------------

def generate_prompt(domain, capability_id, capability, level, description):
    if not all([domain, capability_id, capability, level, description]):
        raise ValueError("All input variables must be provided and non-empty.")

        #print(f"Domain: {domain}")
        #print(f"Capability ID: {capability_id}")
        #print(f"Capability: {capability}")
        #print(f"Maturity Level: {level}")
        #print(f"Description: {description}")

    prompt = f"""
    You are an expert in organizational, IT, and Cloud capability. Please generate a detailed maturity assessment for:

    Input Details:
    Domain: {domain}
    Capability ID: {capability_id}
    Capability: {capability}
    Maturity Level {level}: {description}

    Assign Priority and Focus:
   - Determine the priority level (High, Medium, Low) based on the strategic importance of the capability within the given domain.
   - Assign the focus category (Strategic Focus, Functional Focus, Strategic Impact) that best aligns with how the capability contributes to organizational goals.

    Generate Maturity Framework
    For each maturity level from 1 to 5, provide the following separated by "|" delimiter:
    - Domain
    - Capability ID
    - Capability
    - Priority
    - Focus
    - Level
    - Question
    - Expectation
    - Features

    Output each response as a single line with exactly 9 fields separated by "|". Avoid empty lines or extraneous text.
    Example Output:
    Domain | Capability ID | Capability | Priority | Focus | Level | Question | Expectation | Features

    IMPORTANT: The output should be plain text only with no formatting including numbers, bullet points, bolding,
    italics or any other forms of formatting.
    IMPORTANT: Output each response as a single line with exactly 9 fields separated by "|". Each field must have content, and empty fields should use "N/A". Do not include headers, summaries, or extra lines.
    """

    return prompt

# ---------------------------
# Process AI Response
# ---------------------------

def process_ai_response(response, response_access_method):
    generated_text = response.choices[0].message.content if response_access_method == "attribute" else \
        response['choices'][0]['message']['content']
    lines = generated_text.strip().split('\n')
    parsed_rows = []
    for line in lines:
        parts = [part.strip() for part in line.split('|')]
        if len(parts) == 9:
            parsed_rows.append({
                'Domain': parts[0],
                'Capability ID': parts[1],
                'Capability': parts[2],
                'Priority': parts[3],
                'Focus': parts[4],
                'Level': parts[5],
                'Question': parts[6],
                'Expectation': parts[7],
                'Features': parts[8]
            })
        else:
            print(f"Unexpected line format: {line}. Expected 9 fields but got {len(parts)}. Skipping.")
    return parsed_rows


# ---------------------------
# Duplicate Check
# ---------------------------

def is_duplicate(output_rows, capability_id, level):
    return any(row for row in output_rows if row['Capability ID'] == capability_id and row['Level'] == str(level))


# ---------------------------
# Main Processing Loop
# ---------------------------

def main():
    setup_logging()
    response_access_method = setup_openai_api()

    input_csv_path = 'input/Capabilities_testData.csv'
    output_csv_path = 'output/maturity_assessment_results.csv'
    required_columns = ['domain', 'capability_id', 'capability', 'level']

    # Load data
    capabilities_df = load_input_data(input_csv_path, required_columns)
    # print(capabilities_df.values)

    # Define maturity levels
    maturity_levels = define_maturity_levels()

    # Process each capability-level combination
    output_rows = []
    for _, row in capabilities_df.iterrows():
        domain = row['domain']
        capability_id = row['capability_id']
        capability = row['capability']
        level = int(row['level'])  # Ensure Level is treated as an integer
        description = maturity_levels.get(level, "")  # Fetch description from the dictionary

        print(f"Processing: domain={domain}, capability ID={capability_id}, capability={capability}, level={level}, Description={description}")

        if is_duplicate(output_rows, capability_id, level):
            print(f"Duplicate entry detected for Capability ID {capability_id} at Level {level}, Skipping.")
            continue

        # Generate prompt using Level and its description
        print(domain, capability_id, capability, level, description)
        prompt = generate_prompt(domain, capability_id, capability, level, description)
        print(prompt)
        print(f"Sending request for Capability ID {capability_id}, Level {level}...")

        client = OpenAI()
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are ChatGPT."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            parsed_rows = process_ai_response(response, response_access_method)
            output_rows.extend(parsed_rows)
            print(f"response from AI: {output_rows}")
        except Exception as e:
            logging.error(f"Error processing Capability ID {capability_id} at Level {level}: {e}")
            print(f"Error processing Capability ID {capability_id} at Level {level}. Skipping.")

    # Write results to CSV
    write_output(output_rows, output_csv_path)


# ---------------------------
# Write Output
# ---------------------------

def write_output(output_rows, output_file):
    output_df = pd.DataFrame(output_rows)
    output_df.to_csv(output_file, index=False)
    print(f"Output written to {output_df.values}.")



if __name__ == "__main__":
    main()
