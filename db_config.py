import pymysql
import logging
import pandas as pd

db_config = {
    "hostname": "localhost",
    "user" : "root",
    "password" : "root",
    "database" : "e2caf"
}
#%%
def get_db_connection():
    connection = None
    try:
        # Database connection
        connection = pymysql.connect(
            host=db_config['hostname'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            cursorclass=pymysql.cursors.DictCursor
        )
        if connection.open:
            print("Successfully connected to the database")
    except Exception as e:
        print("An error occurred while connecting to the database:", str(e))

    return connection

#%%
def execute_query(query, values=None, commit=False, fetch_id=False):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values if values else ())
            if commit:
                connection.commit()
                if fetch_id:
                    return cursor.lastrowid
                return None
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Database error during execute_query: {e}")
        if commit:
            connection.rollback()  # Rollback if there was an error during a commit operation
        raise
    finally:
        if connection:
            connection.close()  # Close the connection after query execution

def execute_query_lid(query, values=None, commit=False, fetch_id=True):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
            last_id = cursor.lastrowid  # Capture last inserted ID immediately
            if commit:
                connection.commit()
            return last_id if last_id else cursor.fetchall()  # Return last_id if available, otherwise fetch results
    except Exception as e:
        logging.error(f"Database error during execute_query_lid: {e}")
        if commit:
            connection.rollback()  # Rollback if there was an error during a commit operation
        raise
    finally:
        if connection:
            connection.close()  # Close the connection after query execution
#%%

query = "SELECT r.project_id AS Project_id, r.domain AS domain_id, r.capability AS Capability, r.level AS Level, r.response_text AS Response, c1.Criteria AS Criteria_Level, c2.Criteria AS Criteria_Level_Plus_One FROM tb_response AS r INNER JOIN tb_capabilities AS c1 ON r.capability = c1.Capability AND r.level = c1.Level LEFT JOIN tb_capabilities AS c2 ON r.capability = c2.Capability AND r.level + 1 = c2.Level"
result = execute_query(query)
df = pd.DataFrame(result)
df.to_csv('~/test.csv', index=False)