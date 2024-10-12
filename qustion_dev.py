import pandas as pd
import os
import analysis_modules
import mysql.connector
from mysql.connector import Error

# Setup MySQL connection
try:
    connection = mysql.connector.connect(
        host='localhost',  # usually 'localhost' or an IP address
        database='e2caf',
        user='root',
        password='root')
    if connection.is_connected():
        cursor = connection.cursor()

    path = os.getenv('FILE_PATH')
    os.chdir(path)

    results = []
    #Load Data
    #file_name = 'input/question_dev.xlsx'
    #df = analysis_modules.question_dev(file_name)

#%%
    for _, row in df.iterrows():
        id = row['ID']
        domain = row['Domain']
        level = row['Level']
        capability = row['Capability']
        cap_level = row['Cap_Level']
        feature = row['Feature']
        objective = row['Objective']

        # SQL Select Statement
        select_query = """SELECT * FROM tb_question WHERE ID = %s"""
        cursor.execute(select_query, (id,))
        records = cursor.fetchall()

        # Check if any records with this ID exist
        if len(records) > 0:
            print(f"Data for ID {id} already exists, skipping this row")
            continue

        # First Iteration
        prompt = f""" 
        Looking at the capability, {capability}, the maturity level of the capability, {level}, the generalized objective at
         that level, {objective}, use the following expectations for Capability at Level, {cap_level} and general criteria
         for the capability at Level, {feature}, and return 1 binary question to test if an organisation meets the capability
         at level Only output the question, there is no need for a prelude..
         """
        binary_q = analysis_modules.question_response(capability,cap_level,feature,objective,prompt)
        binary_q = analysis_modules.to_sentence_case(binary_q)

        # Updating variables for the second iteration
        prompt = f""" 
            Looking at the capability, {capability}, the maturity level of the capability, {level}, the generalized objective at
             that level, {objective}, use the following expectations for Capability at Level, {cap_level} and general criteria
             for the capability at Level, {feature}, and return 3 open ended questions to test if an organisation meets the capability
             at level. Only output the questions there is no need for a prelude.
             """
        # Second iteration
        open_q = analysis_modules.question_response(capability,cap_level,feature,objective,prompt)
        open_q = analysis_modules.to_sentence_case(open_q)

        q_parts = [f"{id}|{domain}|{level}|{capability}|{binary_q}|{open_q}"]
        q_parts = [item.split('|') for item in q_parts]
        results.append(q_parts[0])

        # SQL Insert Statement
        query = """INSERT INTO tb_question (`ID`, `Domain`, `Level`, `Capability`, `Binary`, `OpenEnded`) VALUES (%s, %s, %s, %s, %s, %s)"""
        data = (id, domain, level, capability, binary_q, open_q)

        # Execute the query
        cursor.execute(query, data)
        connection.commit()  # Commit the transaction

        print(f"Capability {id} ata inserted successfully")

except Error as e:
    print("Error while connecting to MySQL", e)

finally:
# Closing database connection.
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")


    #%%
"""#print(results)
q_parts = pd.DataFrame(results, columns=['ID', 'Domain', 'Level', 'Capability', 'Binary Question', 'Open Ended Questions'])
q_parts.to_csv('output/question.csv', index=False)"""