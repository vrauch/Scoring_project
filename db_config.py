import logging
import pymysql
from pymysql.cursors import DictCursor

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "e2caf"
}


# Function to establish a database connection
"""def get_db_connection():
    connection = None
    try:
        # Database connection using mysql.connector
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            logging.info("Successfully connected to the database")
        return connection
    except mysql.connector.Error as e:
        logging.error(f"Error connecting to the database: {e}")
        raise
    finally:
        if connection is None or not connection.is_connected():
            logging.error("Failed to establish database connection.")"""

def get_db_connection():
    config = db_config
    connection = pymysql.connect(
        host=config['host'],
        database=config['database'],
        user=config['user'],
        password=config['password'],
        cursorclass=DictCursor # Use DictCursor to get dictionary results
    )
    return connection

# Function to execute a query (for SELECT statements or others without commit)
def execute_query(query, values=None):
    connection = get_db_connection()
    results = None
    cursor = connection.cursor()
    cursor.execute(query, values if values else ())
    results = cursor.fetchall()
    return results


# Function to execute a query with commit (for INSERT, UPDATE, DELETE, etc.)
def execute_query_commit(query, values=None, fetch_id=False):
    global cursor
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(query, values if values else ())

        if fetch_id:
            last_id = cursor.lastrowid  # Fetch last inserted ID if required
            connection.commit()
            return last_id

        connection.commit()  # Commit changes if no errors
    except pymysql.connect.Error as e:
        logging.error(f"Error during query execution with commit: {e}")
        connection.rollback()  # Rollback transaction if there's an error
        raise
    finally:
        if connection and connection:
            cursor.close()
            connection.close()

