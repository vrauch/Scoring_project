# ---------------------------
# Script to define Questions , Expectations at level and Features at level based on
# Domain, Capability and Level definitions. Current output to txt file delimited by "|"
# ---------------------------
import pandas as pd
from pymysql import connect
from tqdm import tqdm
import time
# import helper_functions
from helper_functions import error, openai, MySQLError, connect_to_db, info, warning, setup_logging, execute_query

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
    JOIN e2caf.DigitalImperativesDetails id ON D.domain_id = id.domain_id AND c.capability_id = id.capability_id
    WHERE D.domain_id IN ({domain_placeholders}) 
      AND cd.level IN ({level_placeholders}) 
      AND cd.key_capability = %s
    ORDER BY RAND(), D.domain_name, c.capability_id, cd.level
    limit 3;
    """
    try:
        with connect_to_db() as cursor:

            # Dynamically create placeholders for the WHERE clause
            domain_placeholders = ', '.join(['%s'] * len(domain_ids))
            level_placeholders = ', '.join(['%s'] * len(levels))
            query = query.format(
                domain_placeholders=domain_placeholders,
                level_placeholders=level_placeholders
            )

            # Execute query with parameters
            rows = execute_query(query, (*domain_ids, *levels, key_capability))

            # Convert to DataFrame
            return pd.DataFrame(rows)
    except MySQLError as err:
        error(f"Error executing query: {err}")
        raise
    finally:
        connect.close(connect_to_db())

def fetch_all_maturity_levels():
    query = """
    SELECT domain_id, level, description
    FROM LevelDefinitions;
    """
    try:
        with connect.cursor(connect_to_db()) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            # Create a dictionary for quick lookup
            return {(row['domain_id'], row['level']): row['description'] for row in results}
    except MySQLError as err:
        error(f"Error executing query: {err}")
        raise
    finally:
        connect.close(connect_to_db())

def fetch_all_domain_descriptions():
    query = "SELECT domain_id, domain_description FROM Domain;"
    try:
        with connect.cursor(connect_to_db()) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            # Create a dictionary for quick lookup
            return {row['domain_id']: row['domain_description'] for row in results}
    except MySQLError as err:
        error(f"Error executing query: {err}")
        raise
    finally:
        connect.close(connect_to_db())

def fetch_capability_description():
    query = "SELECT capability_description FROM Capabilities"
    try:
        with connect.cursor(connect_to_db()) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

            if not result:  # Check if the query returned no rows
                warning(f"No capability descriptions found")
                return {"capability_description": "No description available"}  # Return a default value

            return result  # Return the fetched row
    except MySQLError as err:
        error(f"Error executing query for capability: {err}")
        raise
    finally:
        connect.close(connect_to_db())

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

    # Shared inputs
    industry = input("Enter the industry: ").strip()
    country = input("Enter the country: ").strip()
    levels = [int(x) for x in input("Enter levels (comma-separated): ").split(",")]

    if choice == "1":  # Manual Input
        domain_ids = [int(x) for x in input("Enter domain IDs (comma-separated): ").split(",")]
        key_capability = input("Enter key capability (Yes/No): ").strip().capitalize() or "Yes"

        # Create combinations of domain_id and levels
        data = []
        for domain_id in domain_ids:
            for level in levels:
                data.append({
                    'domain_id': domain_id,
                    'level': level,
                    'key_capability': key_capability,
                    'Industry': industry,
                    'Country': country
                })

        info(f"Generated DataFrame for manual input: {data}")
        return pd.DataFrame(data)

    elif choice == "2":  # Database Selection
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT id, di_name FROM DigitalImperatives")
            initiatives = cursor.fetchall()
            if not initiatives:
                raise ValueError("No digital initiatives found.")

            print("Available Digital Initiatives:")
            for idx, initiative in enumerate(initiatives, start=1):
                print(f"{idx}) {initiative['di_name']}")

            selection = int(input("Select a number: "))
            if selection < 1 or selection > len(initiatives):
                raise ValueError("Invalid selection.")

            selected_initiative = initiatives[selection - 1]
            initiative_id = selected_initiative['id']

            cursor.execute(
                """
                SELECT domain_id, capability_id
                FROM DigitalImperativesDetails
                WHERE di_id = %s
                """,
                (initiative_id,)
            )
            details = cursor.fetchall()
            if not details:
                raise ValueError("No details found for the selected initiative.")

            domain_ids = [detail['domain_id'] for detail in details]

            capabilities_df = fetch_capabilities_data(domain_ids, levels, 'Yes')
            capabilities_df['Industry'] = [industry] * len(capabilities_df)
            capabilities_df['Country'] = [country] * len(capabilities_df)

            info(f"Generated DataFrame for database selection: {capabilities_df}")
            return capabilities_df

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
        warning("No output rows to write.")
        return

    try:
        with open(output_file, 'w') as file:
            # Write a header line with pipe delimiter
            file.write("Domain|Capability ID|Capability|Level|Question|Expectation|Features\n")

            # Write each row to the file
            for row in output_rows:
                line = f"{row['Domain']}|{row['Capability ID']}|{row['Capability']}|{row['Level']}|{row['Question']}|{row['Expectation']}|{row['Features']}\n"
                file.write(line)

        info(f"Output written to {output_file}")
    except Exception as e:
        error(f"Failed to write output file: {e}")

# ---------------------------
# Main Function
# ---------------------------
def main():
    setup_logging()
    # response_access_method = helper_functions.setup_openai_api()

    try:
        # Collect inputs
        capabilities_df = get_user_inputs(connect_to_db())

        # Debugging: Log capabilities_df structure
        info(f"Capabilities DataFrame columns: {capabilities_df.columns}")
        info(f"Capabilities DataFrame head: \n{capabilities_df.values.tolist()}")

        # Ensure domain_id exists
        if 'domain_id' not in capabilities_df.columns or 'level' not in capabilities_df.columns:
            raise ValueError("Missing 'domain_id' or 'level' column in capabilities_df.")

        # Extract inputs
        domain_ids = list(capabilities_df['domain_id'].unique())  # Ensure domain_ids is always a list
        levels = list(capabilities_df['level'].unique())  # Ensure levels is always a list
        industry = capabilities_df['Industry'].iloc[0]
        country = capabilities_df['Country'].iloc[0]

        # Fetch data for both key_capability values ('Yes' and 'No')
        capabilities_df_yes = fetch_capabilities_data(domain_ids, levels, 'Yes')
        capabilities_df_no = fetch_capabilities_data(domain_ids, levels, 'No')

        # Combine both datasets
        capabilities_df = pd.concat([capabilities_df_yes, capabilities_df_no])

        # Add Industry and Country to the combined DataFrame
        capabilities_df['Industry'] = industry
        capabilities_df['Country'] = country

        # Pre-fetch maturity levels and domain descriptions
        maturity_levels = fetch_all_maturity_levels()
        domain_descriptions = fetch_all_domain_descriptions()
        capability_descriptions = fetch_capability_description()

        # Validate required columns
        required_columns = ['domain_id', 'domain_name', 'capability_id', 'capability_name', 'level', 'Industry', 'Country']
        missing_columns = [col for col in required_columns if col not in capabilities_df.columns]
        if missing_columns:
            error(f"Missing required columns in capabilities_df: {missing_columns}")
            raise ValueError(f"Missing required columns in capabilities_df: {missing_columns}")

        info(f"capabilities_df columns: {capabilities_df.columns}")
        info(f"capabilities_df head: {capabilities_df.head()}")

        # Process each capability-level combination
        output_rows = []
        for _, row in tqdm(capabilities_df.iterrows(), total=len(capabilities_df), desc="Processing rows"):
            try:
                info(f"Processing row: {row.to_dict()}")

                # Fetch or look up capability description
                capability_description = capability_descriptions.get(row['capability_id'], "No description available")

                # Generate the prompt
                prompt = generate_prompt(
                    domain=row['domain_name'],
                    capability_id=row['capability_id'],
                    capability=row['capability_name'],
                    level=row['level'],
                    description=maturity_levels.get((row['domain_id'], row['level']), "No description available"),
                    domain_description=domain_descriptions.get(row['domain_id'], "No description available"),
                    capability_description=capability_description,
                    industry=row['Industry'],
                    country=row['Country']
                )
                info(f"Generated prompt: {prompt}")

                # Call OpenAI API
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": "You are an expert in generating maturity assessments for organizational capabilities."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=200
                )
                info(f"API response: {response}")

                # Process API response
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
                else:
                    warning(f"Unexpected response format for prompt: {prompt}")

            except Exception as e:
                error(f"Error processing row: {row.to_dict()}. Exception: {e}")
                continue

        # Log output_rows
        if not output_rows:
            warning("No rows added to output_rows.")
        else:
            info(f"Number of rows added to output_rows: {len(output_rows)}")

        # Write output to text file
        output_file = 'output/questions-expectations-features.txt'
        write_output_to_text(output_rows, output_file)
        print(f"Questions written to {output_file}")


        time.sleep (1)

    finally:
        connect_to_db().close()

if __name__ == "__main__":
    main()