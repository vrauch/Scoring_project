# ---------------------------
# Script to define Questions , Expectations at level and Features at level based on
# Domain, Capability and Level definitions. Current output to txt file delimited by "|"
# ---------------------------
import pandas as pd
from pymysql import connect
from tqdm import tqdm
import time
import re
# import helper_functions
from helper_functions import error, openai, MySQLError, connect_to_db, info, warning, setup_logging, execute_query


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

    # Shared inputs collected once
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
                    'level': level
                })

        info(f"Generated DataFrame for manual input: {data}")
        user_data = pd.DataFrame(data)

        # Return consistent structure
        return int(choice), user_data, key_capability, industry, country

    elif choice == "2":  # Digital Initiative Selection
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

            info(f"Selected Digital Initiative: {selected_initiative['di_name']}")

            # Return consistent structure
            return int(choice), domain_ids, levels, industry, country

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
    WHERE D.domain_id IN ({}) 
      AND cd.level IN ({}) 
      AND cd.key_capability = %s
    ORDER BY RAND(), D.domain_name, c.capability_id, cd.level
    LIMIT 5;
    """.format(', '.join(['%s'] * len(domain_ids)), ', '.join(['%s'] * len(levels)))
    try:
        with connect_to_db() as cursor:
            info(f"Executing query: {query}")
            info(f"Parameters: {(*domain_ids, *levels, key_capability)}")
            rows = execute_query(query, (*domain_ids, *levels, key_capability))
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

#
# ---------------------------
# Prompt Generation
# ---------------------------
def generate_prompt(domain, capability_id, capability, level, description, domain_description, capability_description, industry, country):
    if not all([industry, country, domain, capability_id, capability, level, description, domain_description, capability_description]):
        raise ValueError("All input variables must be provided and non-empty.")

    prompt = f"""
You are an expert in organizational, IT, and cloud capability assessments. Your task is to generate survey questions for a maturity assessment of a given capability and maturity level. Use the provided inputs and domain context to produce clear and actionable questions designed for organizational maturity evaluations. Each question must specify an appropriate response format to ensure structured and measurable feedback.
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
Generate a single structured survey question for the given capability and maturity level. For each question, include:
	1.	Question: A clearly written, actionable survey question designed to assess the organization’s performance or alignment with the specified maturity level.
	2.	Response Format: Specify an appropriate format for collecting responses (e.g., Likert scale, multiple-choice, open-ended, or checkbox).
Guidelines:
    •	Generate exactly one set of structured survey questions for the given inputs. The output must not contain multiple sets or additional explanatory text.
    •	The question must align with the provided {domain_description} and {capability_description}.
    •	Relevance: Tailor questions to the {domain_description}, {capability_description}, ensuring they reflect the context of the {industry} and {country} sparingly without being overly specific.
	•	Questions must be tailored to the {industry} and {country} context sparingly, without overly specific references.
	•	Clarity and Simplicity: Avoid jargon, technical terms, or overly complex phrasing. Each question must be easily understandable without requiring additional context.
	•	Focus on a Single Topic: Each question should address one specific aspect of the capability or maturity level to prevent confusion. Avoid combining multiple concepts in one question.
	•	Neutrality: Questions must avoid leading language or assumptions that could bias the respondent’s answer.
	•	Measurability: Frame questions to elicit measurable responses, ensuring clear alignment with the response format (e.g., Likert scale, multiple-choice).
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
Output Format:
Ensure that the response contains exactly 8 fields separated by "|".
The output must use the following structure, with fields separated by a | delimiter. Do not include headers or extra text in the output:
Domain | Capability ID | Capability | Maturity Level | Question | Response Format | Expectation | Features
For each question, provide:
	1.	Question: (e.g., How effectively does your organization implement proactive monitoring and root-cause analysis to reduce cloud incidents?)
	2.	Response Format: (e.g., Likert scale: Not Effective, Slightly Effective, Moderately Effective, Very Effective, Extremely Effective)
Example Output:
    Cloud Operations | CO-01 | Incident Management | 3 | How effectively does your organization implement proactive monitoring and root-cause analysis to reduce cloud incidents? | Likert scale: Not Effective, Slightly Effective, Moderately Effective, Very Effective, Extremely Effective | Organizations at this maturity level in the financial services sector in Germany should demonstrate automated root-cause analysis and resolution processes. | Proactive incident detection, automation frameworks, and root-cause analysis dashboards tailored for regulatory compliance in Germany.
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
            file.write("Domain|Capability ID|Capability|Level|Question|Response Format|Expectation|Features\n")

            # Write each row to the file
            for row in output_rows:
                line = f"{row['Domain']}|{row['Capability ID']}|{row['Capability']}|{row['Level']}|{row['Question']}|{row['Response_Format']}|{row['Expectation']}|{row['Features']}\n"
                file.write(line)

        info(f"Output written to {output_file}")
    except Exception as e:
        error(f"Failed to write output file: {e}")

# ---------------------------
# Main Function
# ---------------------------
def main():
    setup_logging()

    try:
        # Collect inputs
        choice, user_data, key_capability_or_levels, industry, country = get_user_inputs(connect_to_db())

        # Initialize variables
        capabilities_df = None

        if choice == 1:  # Manual Input
            # Extract domain IDs and levels from the user-provided DataFrame
            domain_ids = user_data['domain_id'].unique()
            levels = user_data['level'].unique()

            # Fetch capabilities data for the specific key_capability value
            capabilities_df = fetch_capabilities_data(domain_ids, levels, key_capability_or_levels)

        elif choice == 2:  # Digital Initiative Selection
            # Use returned domain IDs and levels
            domain_ids = user_data
            levels = key_capability_or_levels

            # Fetch capabilities data for both 'Yes' and 'No' key_capability values
            capabilities_df_yes = fetch_capabilities_data(domain_ids, levels, 'Yes')
            capabilities_df_no = fetch_capabilities_data(domain_ids, levels, 'No')

            # Combine results into a single DataFrame
            capabilities_df = pd.concat([capabilities_df_yes, capabilities_df_no], ignore_index=True)

        # Add Industry and Country to the combined DataFrame
        capabilities_df['Industry'] = industry
        capabilities_df['Country'] = country

        # Debugging: Log the final capabilities DataFrame structure
        info(f"Capabilities DataFrame columns: {capabilities_df.columns}")
        info(f"Capabilities DataFrame head: \n{capabilities_df.values.tolist()}")

        # Ensure required columns are present
        required_columns = ['domain_id', 'domain_name', 'capability_id', 'capability_name', 'level', 'Industry', 'Country']
        missing_columns = [col for col in required_columns if col not in capabilities_df.columns]
        if missing_columns:
            error(f"Missing required columns in capabilities_df: {missing_columns}")
            raise ValueError(f"Missing required columns in capabilities_df: {missing_columns}")

        # Pre-fetch maturity levels and domain descriptions
        maturity_levels = fetch_all_maturity_levels()
        domain_descriptions = fetch_all_domain_descriptions()
        capability_descriptions = fetch_capability_description()

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
                         "content": "You are an expert in generating surveys for maturity assessments for organizational capabilities."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                info(f"API response: {response}")

                # Process API response
                generated_text = response.choices[0].message.content.strip()
                generated_text = re.sub(r'\s*\|\s*', '|', generated_text)  # Normalize spaces around delimiters
                responses = generated_text.strip().split("\n\n")  # Split into individual responses

                for response in responses:
                    parts = [part.strip() for part in generated_text.split('|')]  # Split and trim parts
                    # Debugging: Log split parts and their count
                    info(f"Generated Text: {generated_text}")
                    info(f"Split Parts: {parts}")
                    info(f"Number of Parts: {len(parts)}")

                    if len(parts) == 8:
                        output_rows.append({
                            'Domain': parts[0],
                            'Capability ID': parts[1],
                            'Capability': parts[2],
                            'Level': parts[3],
                            'Question': parts[4],
                            'Response_Format': parts[5],
                            'Expectation': parts[6],
                            'Features': parts[7]
                        })
                    else:
                        warning(
                            f"Unexpected response format: Expected 8 parts, got {len(parts)}.\nResponse: {generated_text}")
            except Exception as e:
                error(f"Error processing row: {row.to_dict()}. Exception: {e}")
                continue

        # Log output_rows
        if not output_rows:
            warning("No rows added to output_rows.")
        else:
            info(f"Number of rows added to output_rows: {len(output_rows)}")

        # Write output to text file
        output_file = 'output/survey_questions-expectations-features.txt'
        write_output_to_text(output_rows, output_file)
        print(f"Questions written to {output_file}")

        time.sleep(1)

    finally:
        connect_to_db().close()

if __name__ == "__main__":
    main()