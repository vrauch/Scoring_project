import openai
import pymysql
import pandas as pd
import logging
from packaging import version
import os
from tqdm import tqdm


# ---------------------------
# Configuration Setup
# ---------------------------
def setup_logging():
    logging.basicConfig(
        filename='maturity_assessment_errors.log',
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s:%(message)s'
    )

def setup_openai_api():
    openai.api_key = os.getenv('OPENAI_API_KEY')
    openai_version = openai.__version__
    response_access_method = "attribute" if version.parse(openai_version) >= version.parse("0.27.0") else "dictionary"
    return response_access_method


# ---------------------------
# Database Connection
# ---------------------------
def connect_to_db():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="root",
            database="e2caf",
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as err:
        logging.error(f"Error connecting to MySQL: {err}")
        raise


def get_all_domain_ids():
    query = "SELECT domain_id FROM Domain"
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def get_all_levels():
    query = "SELECT level FROM CapabilityDetails"
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def fetch_capabilities_data(domain_ids, levels, key_capability):
    query = """
    SELECT DISTINCT 
        D.domain_name, c.capability_id, c.capability_name, cd.level
    FROM Capabilities c
    JOIN e2caf.Domain D ON D.domain_id = c.domain_id
    JOIN e2caf.CapabilityDetails cd ON cd.capability_id = c.capability_id
    WHERE D.domain_id IN ({domain_placeholders}) 
      AND cd.level IN ({level_placeholders}) 
      AND cd.key_capability = %s
    ORDER BY RAND(), D.domain_name, c.capability_id, cd.level
    LIMIT 5;
    """
    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Dynamically create placeholders for the WHERE clause
        domain_placeholders = ', '.join(['%s'] * len(domain_ids))
        level_placeholders = ', '.join(['%s'] * len(levels))
        query = query.format(
            domain_placeholders=domain_placeholders,
            level_placeholders=level_placeholders
        )

        # Execute query with parameters
        cursor.execute(query, (*domain_ids, *levels, key_capability))
        rows = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(rows)
        cursor.close()
        connection.close()

        return df
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise

def fetch_maturity_levels (domain_id, level):
    query = """
    select LevelDefinitions.level, LevelDefinitions.description
        from LevelDefinitions
        WHERE domain_id = %s AND level = %s;
    """
    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Execute query with parameters
        cursor.execute(query, (domain_id, level))
        result = cursor.fetchone()

        return result
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise

def fetch_doman_description (domain_id):
    query = """
    Select domain_description
        From Domain
        WHERE domain_id = %s;
    """
    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Execute query with parameters
        cursor.execute(query, (domain_id))
        result = cursor.fetchone()


        return result
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise

def fetch_capability_description (capability_id):
    query = """
    Select capability_description
        From Capabilities
        WHERE capability_id = %s;
    """
    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Execute query with parameters
        cursor.execute(query, (capability_id))
        result = cursor.fetchone()

        return result
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise
# ---------------------------
# User Input Collection
# ---------------------------
def get_user_inputs():
    """
    Collects user inputs for domain IDs, levels, key capability, industry, and country.
    Returns:
        domain_ids (list of int): List of domain IDs.
        levels (list of int): List of levels.
        key_capability (str): 'Yes' or 'No'.
        industry (str): The specified industry.
        country (str): The specified country.
    """
    # Get industry
    industry = input("Enter the industry (e.g., financial services): ").strip()
    if not industry:
        raise ValueError("Industry cannot be empty.")

    # Get country
    country = input("Enter the country (e.g., Taiwan): ").strip()
    if not country:
        raise ValueError("Country cannot be empty.")

    # Get domain IDs
    domain_input = input("Enter domain IDs (comma-separated, e.g., 9,10,11,12): ")
    domain_ids = [int(domain.strip()) for domain in domain_input.split(',') if domain.strip().isdigit()]

    # Get levels
    level_input = input("Enter levels (comma-separated, e.g., 1,2,3,4,5): ")
    levels = [int(level.strip()) for level in level_input.split(',') if level.strip().isdigit()]

    # Get key capability
    key_capability = input("Enter key capability (Yes/No) [Default: Yes]: ").strip().capitalize()
    if not key_capability:
        key_capability = "Yes"  # Default to 'Yes' if the input is empty
    elif key_capability not in ["Yes", "No"]:
        raise ValueError("Invalid input for key capability. Must be 'Yes' or 'No'.")
    return industry, country, domain_ids, levels, key_capability

# ---------------------------
# Prompt Generation
# ---------------------------
def generate_prompt( domain, capability_id, capability, level, description, industry, country ):
    if not all([industry, country, domain, capability_id, capability, level, description]):
        raise ValueError("All input variables must be provided and non-empty.")

    prompt = f"""
You are an expert in organizational, IT, and cloud capability assessments. Your task is to generate a maturity assessment for the given capability and maturity level.

Use the above context to guide your analysis, but do not include the industry or country in the output. 
The output must focus solely on the given capability and maturity level.

Input Details:
    - Domain: {domain}
    - Capability ID: {capability_id}
    - Capability: {capability}
    - Maturity Level: {level} 
    - Maturity Level Description: {description}

**IMPORTANT** For this capability and maturity level, generate a single-line response with ONLY the following fields, separated by a "|" delimiter:
    - Domain:
    - Capability ID:
    - Capability:
    - Maturity Level:
    - Question: A strategic question designed to explore current strategies and initiatives in the {industry} industry in {country} for this capability and maturity level.
    - Expectation: What an organization at this maturity level in the {industry} industry in {country }should exhibit regarding the capability.
    - Features: Specific indicators or attributes that demonstrate the organization meets the expectations for this level.

Output Requirements:
  - Include exactly 7 fields: Domain, Capability ID, Capability, Level, Question, Expectation, Features.
  - Use a "|" delimiter to separate fields.
  - **IMPORTANT** Avoid using column headers in output, extraneous text, explanations, or formatting (e.g., headers, summaries, numbers, bold, italics).

**Example Output**:
Domain | Capability ID | Capability | Level | Question | Expectation | Features
"""
    return prompt


# ---------------------------
# Write Output to a Pipe-Delimited Text File
# ---------------------------
def write_output_to_text(output_rows, output_file):
    if not output_rows:
        logging.warning("No output rows to write.")
        return

    try:
        with open(output_file, 'w') as file:
            # Write a header line with pipe delimiter
            file.write("Domain|Capability ID|Capability|Level|Question|Expectation|Features\n")

            # Write each row to the file
            for row in output_rows:
                line = f"{row['Domain']}|{row['Capability ID']}|{row['Capability']}|{row['Level']}|{row['Question']}|{row['Expectation']}|{row['Features']}\n"
                file.write(line)

        logging.info(f"Output written to {output_file}")
    except Exception as e:
        logging.error(f"Failed to write output file: {e}")

# ---------------------------
# Main Processing Loop
# ---------------------------
def main():
    setup_logging()
    response_access_method = setup_openai_api()

    # Collect user inputs
    industry, country, domain_ids, levels, key_capability  = get_user_inputs()

    # Fetch data from database
    capabilities_df = fetch_capabilities_data(domain_ids, levels, key_capability)
    #print("Fetched Capabilities Data:")
    #print(capabilities_df)

    # Define maturity levels
    maturity_levels = {
        1: "Ad Hoc Processes: Processes are unstructured, reactive, and chaotic. Success depends on individual effort.",
        2: "Basic Processes: Processes are documented and repeatable but may not be standardized across the organization.",
        3: "Defined Processes: Processes are standardized, documented, and integrated across the organization.",
        4: "Quantitatively Managed: Processes are measured and controlled using quantitative performance metrics.",
        5: "Optimizing: Focus on continuous process improvement through innovation and proactive management."
    }

    # Process each capability-level combination
    output_rows = []
    for _, row in tqdm(capabilities_df.iterrows(), total=len(capabilities_df), desc="Processing rows"):
        domain = row['domain_name']
        capability_id = row['capability_id']
        capability = row['capability_name']
        level = row['level']
        description = maturity_levels[level]

        # Generate prompt
        prompt = generate_prompt(domain, capability_id, capability, level, description, industry, country)
        # print(f"Prompt for level;\n {level}: {prompt}")

        # Call OpenAI API
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in generating maturity assessments for organizational capabilities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            # Process the response
            generated_text = response.choices[0].message.content.strip()
            # print(f"Generated Response:\n {generated_text}")

            # Append result to output
            parts = generated_text.split('|')
            if len(parts) == 7:
                output_rows.append({
                    'Domain': parts[0],
                    'Capability ID': parts[1],
                    'Capability': parts[2],
                    'Level': parts[3],
                    'Question': parts[4],
                    'Expectation': parts[5],
                    'Features': parts[6]
                })
                # print(f"Output row:\n {output_rows [-1]}")
        except Exception as e:
            logging.error(f"Error processing Capability ID {capability_id}, Level {level}: {e}")
            continue

    # Write output to txt
    output_file = 'output/maturity_assessment_results.txt'
    write_output_to_text(output_rows, output_file)
    print(f"Questions writen to {output_file}")

if __name__ == "__main__":
    main()