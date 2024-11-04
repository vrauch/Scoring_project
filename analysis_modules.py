import mysql.connector
from db_config import *
import logging
from transformers import BertTokenizer, BertModel
import torch
from scipy.spatial.distance import cosine
import re
import unicodedata
import contractions
from mysql.connector import Error


def load_from_db_project(project_id):
    try:
        # Setup MySQL connection
        connection = get_db_connection()

        # Check if the connection is established
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)

            # SQL query to retrieve data
            select_query = """
                SELECT
                    D.domain_name AS Domain,
                    C.capability_name AS Capability,
                    C.capability_id,
                    Q.Level as Level,
                    AP.project_name,
                    MAX(CASE WHEN Q.Level = 1 THEN A.openended_answer END) AS Assessment,
                    MAX(CASE WHEN CD.level = 1 THEN CD.capability_at_level END) AS Criteria1,
                    MAX(CASE WHEN CD.level = 2 THEN CD.capability_at_level END) AS Criteria2
                FROM
                    Questions Q
                INNER JOIN
                    Capabilities C ON Q.capability_id = C.capability_id
                INNER JOIN
                    Domain D ON C.domain_id = D.domain_id
                LEFT JOIN
                    Answers A ON A.question_id = Q.uid
                LEFT JOIN
                    CapabilityDetails CD ON C.capability_id = CD.capability_id
                JOIN AssessmentProject AP ON A.project_id = AP.project_id
                WHERE
                    Q.Level IN (1, 2) AND A.project_id = %s
                GROUP BY
                    D.domain_name, C.capability_name, C.capability_id, Q.Level, AP.project_name;
            """

            # Log the query and the parameters being used
            logging.info(f"Executing query: {select_query} with project_id: {project_id}")

            # Execute the query with project_id as a tuple
            cursor.execute(select_query, (project_id,))
            rows = cursor.fetchall()

            if not rows:
                logging.info(f"No rows returned for project ID {project_id}")
            return rows

    except mysql.connector.Error as err:
        logging.error(f"Error executing query: {err}")
        return None

    finally:
        if connection and connection.is_connected():
            connection.close()


def response_load(file_name):
    import pandas as pd
    df = pd.read_excel(file_name)
    df['Domain'] = df['Domain']
    df['Capability'] = df['Capability']
    df['Level'] = df['Level']
    # Normalize text data in specific columns
    df['Assessment'] = df['Assessment'].apply(clean_and_normalize_text)
    df['Criteria1'] = df['Criteria1']
    df['Criteria2'] = df['Criteria2']
    return df


def domain_summary_load(file_name):
    import pandas as pd
    df = pd.read_csv(file_name)
    df['Domain'] = df['Domain']
    df['Alignment'] = df['Alignment'].apply(clean_and_normalize_text)

    return df


def question_dev(file_name):
    import pandas as pd
    df = pd.read_excel(file_name)
    df['ID'] = df['ID']
    df['Domain'] = df['Domain']
    df['Level'] = df['Level']
    df['Capability'] = df['Capability']
    df['Cap_Level'] = df['Cap_Level']
    df['Feature'] = df['Feature']
    df['Objective'] = df['Objective']
    return df


def ia_analysis(criteria, assessment, prompt):
    try:
        import openai
        import os
        openai.api_key = os.getenv('OPENAI_API_KEY')
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": "You have your professional business consultant with and MBA and are an expert in Business Analysis"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0
        )
        # print(response.choices[0].message.content.strip().lower())
        ai_analysis_response = response.choices[0].message.content.strip().lower()
        return ai_analysis_response

    except ImportError as e:
        print(f"An import error occurred: {str(e)} ")
        print(
            "This might be because the OpenAI library is not installed or 'DefaultHttpxClient' cannot be found in the library's module.")
        print("Please ensure you have the latest version of OpenAI installed.")
    except Exception as e:
        print(f"An error occurred: {str(e)} ")
        print("Please check your OpenAI library installation and usage.")


def build_backlog(prompt, recommendation):
    try:
        import openai
        import os
        openai.api_key = os.getenv('OPENAI_API_KEY')
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You have your professional agile project manager and are an expert in developing agile backlogs"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0
        )
        # print(response.choices[0].message.content.strip().lower())
        backlog_response = response.choices[0].message.content.strip().lower()
        return backlog_response
    except ImportError as e:
        print(f"An import error occurred: {str(e)} ")
        print(
            "This might be because the OpenAI library is not installed or 'DefaultHttpxClient' cannot be found in the library's module.")
        print("Please ensure you have the latest version of OpenAI installed.")
    except Exception as e:
        print(f"An error occurred: {str(e)} ")
        print("Please check your OpenAI library installation and usage.")


def question_response(capability, level, cap_level, feature, objective, prompt):
    try:
        import openai
        import os
        openai.api_key = os.getenv('OPENAI_API_KEY')
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You have your professional survey writer and are an expert in Business Analysis"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0
        )
        question_dev_response = response.choices[0].message.content.strip().lower()
        return question_dev_response

    except ImportError as e:
        print(f"An import error occurred: {str(e)} ")
        print(
            "This might be because the OpenAI library is not installed or 'DefaultHttpxClient' cannot be found in the library's module.")
        print("Please ensure you have the latest version of OpenAI installed.")
    except Exception as e:
        print(f"An error occurred: {str(e)} ")
        print("Please check your OpenAI library installation and usage.")


def summarize_paragraph(domain, data, prompt):
    import openai
    import os
    openai.api_key = os.getenv('OPENAI_API_KEY')
    # Use the completion endpoint to summarize the paragraph
    response = openai.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=500,
        temperature=0,
        # top_p=0.5,
        # frequency_penalty=2,
        # presence_penalty=0
    )
    # Extract and return the summarized text from the response
    return response.choices[0].text.strip()


def get_embedding(text, tokenizer, model):
    # Tokenize and convert to input IDs
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

    # Generate embeddings
    with torch.no_grad():
        outputs = model(**inputs)

    # Use mean pooling to get a single vector representation
    embeddings = outputs.last_hidden_state
    attention_mask = inputs['attention_mask']
    mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    sum_embeddings = torch.sum(embeddings * mask_expanded, 1)
    sum_mask = mask_expanded.sum(1)
    sum_mask = torch.clamp(sum_mask, min=1e-9)
    mean_pooled = sum_embeddings / sum_mask
    return mean_pooled


def compute_cosine_similarity(criteria, text, tokenizer, model):
    # Get embeddings for both texts
    embedding1 = get_embedding(criteria, tokenizer, model).numpy().flatten()
    embedding2 = get_embedding(text, tokenizer, model).numpy().flatten()

    # Compute cosine similarity
    score = 1 - cosine(embedding1, embedding2)
    return score


def clean_and_normalize_text(text):
    if text is None:
        return None

    # Convert to string, strip whitespace, and convert to lowercase
    cleaned_text = str(text).strip().lower()
    # Expand contractions
    cleaned_text = contractions.fix(cleaned_text)
    # Remove leading -, =, and whitespace characters
    cleaned_text = re.sub(r'^[\-=\s]+', '', cleaned_text)
    # Remove newlines and carriage returns
    cleaned_text = re.sub(r'[\n\r]+', ' ', cleaned_text)
    # Remove HTML tags
    cleaned_text = re.sub(r'<.*?>', '', cleaned_text)
    # Remove URLs
    cleaned_text = re.sub(r'http\S+|www\S+|https\S+', '', cleaned_text, flags=re.MULTILINE)
    # Remove special characters and punctuation
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)
    # Remove numbers (if necessary)
    cleaned_text = re.sub(r'\d+', '', cleaned_text)
    # Normalize accented characters
    cleaned_text = unicodedata.normalize('NFKD', cleaned_text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    # Remove extra spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    return cleaned_text


def to_sentence_case(text):
    if not isinstance(text, str):
        raise TypeError("Expected a string")
    # Trim whitespace and split into sentences
    sentences = text.strip().split('. ')
    # Capitalize each sentence's first character
    sentences = [sentence.capitalize() for sentence in sentences if sentence]
    # Rejoin the sentences
    return '. '.join(sentences)


def get_maturity_score(text):
    # Dictionary to map keywords to scores
    scores = {"Strong": 1.0, "Moderate": 0.5, "Weak": 0.0}
    # Look for any keyword in the text, return the associated score, or 0.0 if not found
    return next((score for keyword, score in scores.items() if keyword in text), 0.0)


def save_analysis_result(project_id, capability_id, level, alignment, similarity_score, maturity_score,
                         recommendations):
    try:
        # Setup MySQL connection
        connection = get_db_connection()

        # Check if the project_id and capability_id combination already exists
        check_query = """
            SELECT COUNT(*) FROM AnalysisResults 
            WHERE project_id = %s AND capability_id = %s
        """
        result = execute_query(check_query, (project_id, capability_id))
        if result[0]['COUNT(*)'] > 0:
            print(
                f"Record already exists for project ID {project_id} and capability ID {capability_id}. Skipping insert.")
            return

        # Prepare the SQL insert query
        insert_query = """
            INSERT INTO e2caf.AnalysisResults (
                project_id,
                capability_id,
                level,
                alignment,
                similarity_score,
                maturity_score,
                recommendations,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """

        # Execute the query with the provided data
        execute_query_commit(insert_query, (
            project_id,
            capability_id,
            level,
            alignment,
            similarity_score,
            maturity_score,
            recommendations,
        ))

        print(f"Analysis result saved successfully for project ID {project_id} and capability ID {capability_id}.")

    except Error as e:
        print(f"Error while saving analysis results: {e}")
    finally:
        # Close the cursor and connection
        if connection.is_connected():
            connection.close()
