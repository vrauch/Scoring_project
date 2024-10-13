
def load_from_db():
    import mysql.connector

    try:
        # Setup MySQL connection
        connection = mysql.connector.connect(
            host='localhost',
            database='e2caf',
            user='root',
            password='root'
        )

        # Check if the connection is established
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)  # Return results as dictionaries

            # SQL query to retrieve data
            select_query = """
                    SELECT
                        D.domain_name AS Domain,
                        C.capability_name AS Capability,
                        Q.Level as Level,
                        MAX(CASE WHEN Q.Level = 1 THEN A.openended_answer END) AS Assessment,
                        MAX(CASE WHEN CD.cap_level = 1 THEN CD.scoring_criteria_at_level END) AS Criteria1,
                        MAX(CASE WHEN CD.cap_level = 2 THEN CD.scoring_criteria_at_level END) AS Criteria2
                    FROM
                        tb_question Q
                    INNER JOIN
                        Capabilities C ON Q.capability_id = C.capability_id
                    INNER JOIN
                        Domain D ON C.domain_id = D.domain_id
                    LEFT JOIN
                        answers A ON A.question_id = Q.uid
                    LEFT JOIN
                        CapabilityDetails CD ON C.capability_id = CD.capability_id
                    WHERE
                        Q.Level IN (1, 2) AND A.openended_answer is not null
                    GROUP BY
                        D.domain_name, C.capability_name, Q.Level;
                """

            # Execute the query
            cursor.execute(select_query)
            rows = cursor.fetchall()  # Fetch all the rows returned by the query

            # Close the cursor and connection
            cursor.close()
            connection.close()

            return rows

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
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


def non_priority_load(file_name):
    import pandas as pd
    df = pd.read_excel(file_name)
    df['Domain'] = df['Domain']
    df['Capability'] = df['Capability']
    # Normalize text data in specific columns - also converting to string type
    df['Response'] = df['Response'].astype(str)
    df['Criteria3'] = df['Criteria3'].astype(str)
    return df


def ia_analysis(criteria, assessment, prompt):
    try:
        import openai
        from openai import OpenAI
        import os
        openai.api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
        from openai import OpenAI
        import os
        openai.api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
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
        from openai import OpenAI
        import os
        openai.api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
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


# %%
def summarize_paragraph(domain, data, prompt):
    import openai
    import os
    from openai import OpenAI
    openai.api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=openai.api_key)
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


# %%
def get_embedding(text, tokenizer, model):
    import torch
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


# %%
def compute_cosine_similarity(criteria, text, tokenizer, model):
    from scipy.spatial.distance import cosine
    # Get embeddings for both texts
    embedding1 = get_embedding(criteria, tokenizer, model).numpy().flatten()
    embedding2 = get_embedding(text, tokenizer, model).numpy().flatten()

    # Compute cosine similarity
    score = 1 - cosine(embedding1, embedding2)
    return score


# %%
def clean_and_normalize_text(text):
    import re
    if text is None:
        return None
    cleaned_text = str(text).strip()
    cleaned_text = cleaned_text.lower()
    #cleaned_text = re.sub(r'[\n\r]+', '', cleaned_text)
    return cleaned_text


def to_sentence_case(text):
    import re
    if not isinstance(text, str):
        raise TypeError("expected string or bytes-like object")
    # Split the text into sentences using a regex that captures some common sentence enders
    sentences = re.split('(?<=[.!?:]) +', text)
    # Convert each sentence to lowercase and then capitalize the first letter
    sentences = [sentence.capitalize() for sentence in sentences]
    # Join the sentences back together
    return ' '.join(sentences)


def get_maturity_score(text):
    if 'Alignment: Strong' in text:
        return 1.0
    elif 'Alignment: Moderate' in text:
        return 0.5
    elif 'Alignment: Weak' in text:
        return 0.0
    else:
        return 0.0
