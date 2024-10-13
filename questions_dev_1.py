import os
import analysis_modules
import mysql.connector
from mysql.connector import Error

# Setup MySQL connection
try:
    connection = mysql.connector.connect(
        host='localhost',
        database='e2caf',
        user='root',
        password='root'
    )
    if connection.is_connected():
        cursor = connection.cursor()

        path = os.getenv('FILE_PATH')
        if path:  # Only change directory if the path is not None
            os.chdir(path)

        # Query to fetch all records from CapabilityDetails and join with Capabilities
        select_query = """
        SELECT cd.*, c.capability_name
        FROM CapabilityDetails cd
        INNER JOIN Capabilities c ON cd.capability_id = c.capability_id
        """
        cursor.execute(select_query)
        rows = cursor.fetchall()

        # Get column names using cursor.description
        column_names = [desc[0] for desc in cursor.description]

        results = []

        # Loop through each row to process it
        for row in rows:
            # Create a dictionary mapping column names to values
            row_dict = dict(zip(column_names, row))

            # Extract necessary fields using column names
            capability_id = row_dict['capability_id']
            capability_at_level = row_dict['capability_at_level']
            features = row_dict['features']
            scoring_criteria_at_level = row_dict['scoring_criteria_at_level']
            capability_name = row_dict['capability_name']
            level = row_dict['cap_level']  # Assuming 'cap_level' corresponds to 'Level' in tb_question

            # Check if there is already a binary and open-ended question for this `capability_id` and `level`
            check_query = """
                       SELECT 1 FROM tb_question WHERE capability_id = %s AND Level = %s
                       """
            cursor.execute(check_query, (capability_id, level))
            existing_record = cursor.fetchone()

            # If a record exists, skip this iteration
            if existing_record:
                print(f"Skipping Capability ID {capability_id} at Level {level} as it already has questions.")
                continue

            # First iteration: Generate the binary question
            prompt = f"""
            Looking at the capability, {capability_name}, the maturity level of the capability, {level}, the generalized objective at
            that level, {scoring_criteria_at_level}, use the following expectations for Capability at Level, {capability_at_level} and general criteria
            for the capability at Level, {features}, and return 1 binary question to test if an organisation meets the capability
            at level. Only output the question, there is no need for a prelude.
            """
            binary_q = analysis_modules.question_response(capability_name, level, capability_at_level, features, scoring_criteria_at_level, prompt)
            binary_q = analysis_modules.to_sentence_case(binary_q)

            # Second iteration: Generate the open-ended questions
            prompt = f"""
            Looking at the capability, {capability_name}, the maturity level of the capability, {level}, the generalized objective at
            that level, {capability_at_level}, use the following expectations for Capability at Level, {capability_at_level} and general criteria
            for the capability at Level, {features}, and return 3 open-ended questions to test if an organisation meets the capability
            at level. Only output the questions, there is no need for a prelude.
            """
            open_q = analysis_modules.question_response(capability_name, level, capability_at_level, features, scoring_criteria_at_level, prompt)
            open_q = analysis_modules.to_sentence_case(open_q)

            # Prepare the data for insertion
            data = (capability_id, level, binary_q, open_q)

            # Insert the processed data into the tb_question table
            insert_query = """
            INSERT INTO tb_question (capability_id, Level, `Binary`, OpenEnded) 
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, data)
            connection.commit()  # Commit the transaction for each row

            results.append((capability_id, level, binary_q, open_q))
            print(f"Data for Capability ID {capability_id} inserted successfully.")

except Error as e:
    print(f"Error while processing records: {e}")

finally:
    # Closing database connection
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
