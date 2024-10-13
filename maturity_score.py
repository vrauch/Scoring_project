import re

import pymysql
import logging

db_config = {
    "hostname": "127.0.0.1",
    "user" : "root",
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
import re
query = "SELECT capability, alignment FROM tb_analysis"
text = execute_query(query)
for item in text:
     if re.search("strong", item['alignment']):
        print("strong")
     elif re.search("moderate", item['alignment']):
         print("moderate")
     elif re.search("weak", item['alignment']):
         print("weak")
     else:
         print("No alignment defined")


