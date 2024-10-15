# Must use openai .28 for this script. pip insta;; openai.28
import openai
import openai.error
import os
import db_config

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QUESTION_TABLE = "e2caf.Questions"
# MODEL_NAME = "gpt-3.5-turbo"
API_MAX_TOKEN = 50
API_TEMP = 0.3
QUERY_SELECT = """SELECT uid, `binary` FROM e2caf.Questions"""
QUERY_UPDATE = "UPDATE e2caf.Questions SET `binary` = %s WHERE uid = %s"

openai.api_key = OPENAI_API_KEY


def summarize_question(question):
    # Ensure question is valid
    if not question or not question.strip():
        return "Invalid question input."

    prompt = f"Rewrite the following question: {question} to be no more than 15 words."

    try:
        # Correct method to use ChatCompletion in openai>=1.0.0
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the latest chat model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,  # Limit to concise answers
            temperature=0.3  # Lower temperature for deterministic output
        )

        # Accessing the response from the chat model
        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return question  # Return the original question if there's an error
    except Exception as e:
        print(f"Unexpected error: {e}")
        return question


def update_question_in_database(database_connection, question_id, summarized_question):
    db_config.execute_query_commit(QUERY_UPDATE, (summarized_question, question_id))
    print(f"Question ID {question_id} will be updated to: {summarized_question}")


def process_table():
    try:
        database_connection = db_config.get_db_connection()
        rows = db_config.execute_query(QUERY_SELECT)
        for row in rows:
            original_question = row['binary']
            summarized_question = summarize_question(original_question)
            update_question_in_database(database_connection, row['uid'], summarized_question)
        database_connection.commit()
    except Exception as e:
        print(f"Error processing table: {e}")


if __name__ == "__main__":
    process_table()