from pymysql import cursors, connect, MySQLError
from logging import basicConfig, DEBUG, error, info, warning
import openai
import os
from packaging import version as version


# ---------------------------
# Logging Setup
# ---------------------------
def setup_logging():
    basicConfig(
        filename='maturity_assessment_errors.log',
        level=DEBUG,
        format='%(asctime)s:%(levelname)s:%(message)s'
    )

# -------------------------
# Connect to openai_API
# -------------------------
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
        connection = connect(
            host="localhost",
            user="root",
            password="root",
            database="e2caf",
            cursorclass=cursors.DictCursor
        )
        return connection
    except MySQLError as err:
        error(f"Error connecting to MySQL: {err}")
        raise

def execute_query(query, values=None):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(query, values if values else ())
    results = cursor.fetchall()
    return results