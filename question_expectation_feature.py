import openai
import pymysql
import pandas as pd
import logging
from packaging import version
import os
from tqdm import tqdm
import time

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

# ---------------------------
# Fetch Data Functions
# ---------------------------
def fetch_capabilities_data(domain_ids, levels, key_capability):
    query = """
    SELECT DISTINCT 
        D.domain_id, D.domain_name, c.capability_id, c.capability_name, cd.level, c.capability_description
    FROM e2caf.Domain D
    JOIN e2caf.Capabilities c ON D.domain_id = c.domain_id
    JOIN e2caf.CapabilityDetails cd ON c.capability_id = cd.capability_id
    JOIN e2caf.InitiativeCardsDetails id ON D.domain_id = id.domain_id AND c.capability_id = id.capability_id
    WHERE D.domain_id IN ({domain_placeholders}) 
      AND cd.level IN ({level_placeholders}) 
      AND cd.key_capability = %s
    ORDER BY RAND(), D.domain_name, c.capability_id, cd.level
    Limit 5;
    """
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
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
            return pd.DataFrame(rows)
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise
    finally:
        connection.close()

def fetch_maturity_levels(domain_id, level):
    query = """
    SELECT LevelDefinitions.level, LevelDefinitions.description
    FROM LevelDefinitions
    WHERE domain_id = %s AND level = %s;
    """
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            cursor.execute(query, (domain_id, level))
            return cursor.fetchone()
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise
    finally:
        connection.close()

def fetch_domain_description(domain_id):
    query = "SELECT domain_description FROM Domain WHERE domain_id = %s;"
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            cursor.execute(query, (domain_id,))
            return cursor.fetchone()
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise
    finally:
        connection.close()

def fetch_capability_description(capability_id):
    query = "SELECT capability_description FROM Capabilities WHERE capability_id = %s;"
    try:
        connection = connect_to_db()
        with connection.cursor() as cursor:
            cursor.execute(query, (capability_id,))
            return cursor.fetchone()
    except pymysql.MySQLError as err:
        logging.error(f"Error executing query: {err}")
        raise
    finally:
        connection.close()

# ---------------------------
# User Input Collection
# ---------------------------
def get_user_inputs(db_connection):
    print("Select input method:")
    print("1. Enter inputs manually")
    print("2. Select from the Digital Initiative Table")

    choice = input("Enter your choice (1 or 2): ").strip()
    if choice not in ["1", "2"]:
        raise ValueError("Invalid choice. Please select either 1 or 2.")

    if choice == "1":
        industry = input("Enter the industry: ").strip()
        country = input("Enter the country: ").strip()
        domain_ids = [int(x) for x in input("Enter domain IDs (comma-separated): ").split(",")]
        levels = [int(x) for x in input("Enter levels (comma-separated): ").split(",")]
        key_capability = input("Enter key capability (Yes/No): ").strip().capitalize() or "Yes"
        return industry, country, domain_ids, levels, key_capability


    elif choice == "2":
        with db_connection.cursor() as cursor:

            # Retrieve Digital Initiatives
            cursor.execute("SELECT id, di_name FROM DigitalImperatives")
            initiatives = cursor.fetchall()
            if not initiatives:
                raise ValueError("No digital initiatives found.")
            print("Available Digital Initiatives:")

            for idx, initiative in enumerate(initiatives, start=1):
                print(f"{idx}) {initiative['di_name']}")

            # User selects an initiative
            selection = int(input("Select a number: "))
            selected_initiative = initiatives[selection - 1]
            initiative_id = selected_initiative['id']

            # Retrieve domain_id and capability_id from DigitalImperativeDetails
            cursor.execute(
                """
                SELECT domain_id, capability_id
                FROM InitiativeCardsDetails
                WHERE i_card_id = %s
                """,
                (initiative_id,)
            )

            details = cursor.fetchall()
            if not details:
                raise ValueError("No details found for the selected initiative.")

            # Extract domain_ids, capability_ids, and levels
            domain_ids = [detail['domain_id'] for detail in details]
            capability_ids = [detail['capability_id'] for detail in details]
            levels = list(set(detail['assessment_level'] for detail in details))  # Get unique levels

            # Return the selected initiative name, and details
            return selected_initiative['di_name'], "Unknown Country", domain_ids, capability_ids, levels, "Yes"
# ---------------------------
# Prompt Generation
# ---------------------------
def generate_prompt(domain, capability_id, capability, level, description, domain_description, capability_description, industry, country):
    if not all([industry, country, domain, capability_id, capability, level, description, domain_description, capability_description]):
        raise ValueError("All input variables must be provided and non-empty.")

    prompt = f"""
You are an expert in organizational, IT, and cloud capability assessments. Your task is to generate a maturity assessment for a given capability and maturity level. Use the provided inputs and domain context to produce a structured output focusing solely on the specified capability and maturity level. Including sparingly industry- or country-specific references in the output.

Input Details:
    • Domain: {domain}
    • Capability ID: {capability_id}
    • Capability: {capability}
    • Maturity Level: {level}
    • Maturity Level Description: {description}
    • Domain Description: {domain_description}
    • Capability Description: {capability_description}
    • Industry: {industry}
    • Country: {country}

Task Requirements:
Generate a single-line output containing exactly 7 fields separated by a | delimiter. Each field must follow the order and formatting below:
    1. Domain: The name of the domain.
    2. Capability ID: The unique identifier for the capability.
    3. Capability: The description or name of the capability.
    4. Maturity Level: The specified maturity level.
    5. Question: A strategic question designed to explore strategies or initiatives related to this capability and maturity level.
    6. Expectation: What an organization at this maturity level is expected to demonstrate for the given capability.
    7. Features: Specific indicators or attributes that validate the organization’s adherence to this maturity level.

Output Format:
The output must use the following structure, with fields separated by a | delimiter. Do not include headers or extra text in the output:
Domain | Capability ID | Capability | Maturity Level | Question | Expectation | Features

Guidelines:
    • The Question must align with the provided {domain_description} and {capability_description} and be tailored to the context of {industry} and {country}, but not include them directly in the question.
    • The Expectation must reflect traits or actions expected at the given maturity level while incorporating nuances relevant to the industry and country.
    • The Features must include concise, specific indicators or attributes that demonstrate compliance with the stated expectation in the industry and country context.
    • Ensure the response adheres to the given input data and avoids unnecessary or generic outputs.

Example Input:
    • Domain: Cloud Operations
    • Domain Description: The management and optimization of cloud-based environments to ensure scalability, reliability, and efficiency.
    • Capability ID: CO-01
    • Capability: Incident Management
    • Capability Description: Cloud incidents are detected using monitoring tools and alerts are automatically sent and entered into an Incident Management tool. Basic communication is automated for team routing and management awareness. Escalation is automated based on category priority and documented resolution times. There is a formal "swarming" protocol established for high severity priorities when expected resolution times are not met.
    • Maturity Level: 3
    • Maturity Level Description: Proactive monitoring with root-cause analysis and automation.
    • Industry: Financial Services
    • Country: Germany

Example Output:
    Cloud Operations | CO-01 | Incident Management | 3 | How does the organization in Germany's financial services sector utilize proactive monitoring and automation to reduce incidents? | Organizations at this maturity level in the financial services sector in Germany should demonstrate automated root-cause analysis and resolution processes. | Proactive incident detection, automation frameworks, and root-cause analysis dashboards tailored for regulatory compliance in Germany.

If any input is missing or unclear, return:
"Insufficient information to generate output."
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
# Main Function
# ---------------------------
def main():
    setup_logging()
    response_access_method = setup_openai_api()

    db_connection = connect_to_db()
    try:
        # Collect inputs
        industry, country, domain_ids, levels, key_capability = get_user_inputs(db_connection)

        # Fetch data for both key_capability values ('Yes' and 'No')
        capabilities_df_yes = fetch_capabilities_data(domain_ids, levels, 'Yes')
        capabilities_df_no = fetch_capabilities_data(domain_ids, levels, 'No')

        # Combine both datasets
        capabilities_df = pd.concat([capabilities_df_yes, capabilities_df_no])

        # Process each capability-level combination
        output_rows = []
        for _, row in tqdm(capabilities_df.iterrows(), total=len(capabilities_df), desc="Processing rows"):
            domain_id = row['domain_id']
            domain = row['domain_name']
            capability_id = row['capability_id']
            capability = row['capability_name']
            level = row['level']
            capability_description = row['capability_description']
            description = fetch_maturity_levels(domain_id, level)
            domain_description = fetch_domain_description(domain_id)

            # Generate prompt
            prompt = generate_prompt(
                domain, capability_id, capability, level, description,
                domain_description, capability_description, industry, country
            )

            # Call OpenAI API
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert in generating maturity assessments for organizational capabilities."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=200
                )
                generated_text = response.choices[0].message.content.strip()
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
            except Exception as e:
                logging.error(f"Error processing Capability ID {capability_id}, Level {level}: {e}")
                continue

            # Add a short pause to avoid rate limiting
            time.sleep(1)

        # Write output to text file
        output_file = 'output/questions-expectations-features.txt'
        write_output_to_text(output_rows, output_file)
        print(f"Questions written to {output_file}")

    finally:
        db_connection.close()

if __name__ == "__main__":
    main()