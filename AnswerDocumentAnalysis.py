import openai
import os
import db_config
import csv
import time
import pandas as pd

# Define constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    print("Environment variable OPENAI_API_KEY is not set")
    sys.exit(1)
SQL_QUERY = """
SELECT C.capability_id as capability_id,
       CD.level as level,
       CONCAT(COALESCE(CD.capability_at_level, ''), ' ', COALESCE(CD.features, ''), ' ', COALESCE(CD.scoring_criteria_at_level, '')) AS Criteria,
       Q.uid AS question_id,  -- Return the specific question_id for the capability_id and level
       GROUP_CONCAT(Q.`binary`) AS 'binary',
       GROUP_CONCAT(Q.open_ended) AS 'open_ended'
FROM e2caf.Capabilities C
JOIN e2caf.CapabilityDetails CD ON C.capability_id = CD.capability_id
JOIN e2caf.Questions Q ON CD.capability_id = Q.capability_id AND CD.level = Q.level
WHERE CD.level < 2
  AND CD.capability_id IN (723)
GROUP BY C.capability_id, CD.level, CD.capability_at_level, CD.features, CD.scoring_criteria_at_level, Q.uid
ORDER BY C.capability_id, CD.level;
"""
OPENAI_ENGINE = "text-davinci-002"
MODEL_NAME = "gpt-4"
MAX_TOKENS = 10000

# AND CD.capability_id IN (723, 726, 727, 746, 749, 760, 765, 766, 767, 775, 797, 803, 826, 848, 850, 890, 919)

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY


def read_document(file_path):
    with open(file_path, 'r', errors='ignore') as file:
        content = file.read()
        return content


def query_criteria_from_db():
    return db_config.execute_query(SQL_QUERY)


def summarize_criteria(criteria):
    prompt = f"Summarize the following criteria into a concise paragraph:\n\n{criteria}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Updated to use gpt-3.5-turbo chat model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.2
        )
        summary = response['choices'][0]['message']['content'].strip()
        print(summary)
        return summary
    except Exception as e:
        print(f"Error generating summary: {e}")
        return criteria_sum


def get_analysis_result(document, criterion, question, question_type):
    system_message = "You are a very good business analyst" if question_type == 'binary' else \
        "You are a CIO with detailed experiences in analysing IT systems from a business perspective"
    user_message = (
        f"Please analyze the document:\n\n{document}\n\n"
        f"Question type: '{question_type.capitalize()}'\n"
        f"Question: '{question}'\n"
        f"Criterion: '{criterion}'\n"
    )

    if question_type == 'binary':
        user_message += "The response should be strictly 'Yes' or 'No'. based on the document."
    else:
        user_message += "Provide a fact-based justification of 50 words or less, grounded in the information provided in the document."

    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system",
             "content": system_message},
            {"role": "user",
             "content": user_message}
        ]
    )
    ai_response = response['choices'][0]['message']['content'].strip()
    answer = ai_response if ai_response else \
        'Justification not extracted' if question_type == 'openended' else 'Answer not extracted'
    # print(answer)
    return answer


def transform_criteria_data(rows):
    criteria = {}
    binary_questions = {}
    openended_questions = {}
    for row in rows:
        key = row['Criteria']  # also serves as the capability_id
        criteria[key] = {
            'capability_id': row['capability_id'],
            'level': row['level'],
            'question_id': row['question_id']
        }
        binary_questions[key] = row['binary']
        openended_questions[key] = row['open_ended']
    return criteria, binary_questions, openended_questions


def analyze_document(document, criteria, binary_questions, openended_questions):
    results = {}
    for criterion in criteria:
        capability_id = criteria[criterion]['capability_id']
        level = criteria[criterion]['level']
        question_id = criteria[criterion]['question_id']

        binary_ans = get_analysis_result(document, criterion, binary_questions[criterion], 'binary')
        justification_ans = get_analysis_result(document, criterion, openended_questions[criterion], 'openended')

        time.sleep(20)

        results[criterion] = {'capability_id': capability_id,
                              'level': level,
                              'question_id': question_id,
                              'binary_ans': binary_ans,
                              'justification_ans': justification_ans}
    return results


def main(document_path):
    # Fetch and transform criteria data
    criteria_data = query_criteria_from_db()
    criteria_dic, binary_questions, openended_questions = transform_criteria_data(criteria_data)

    # Read document text
    document_text = read_document(document_path)

    # Analyze document
    results = analyze_document(document_text, criteria_dic, binary_questions, openended_questions)

    # Prepare data

    # Sample data to populate DataFrame
    data = []
    for criterion, result in results.items():
        row = [result['question_id'], result['justification_ans'], result['capability_id']]
        data.append(row)

    # Create the DataFrame
    df = pd.DataFrame(data, columns=["question_id", "openended_answer", "capability_id"])

    # Add additional columns
    df["project_id"] = 2
    df["binary_answer"] = "Yes"

    # Display settings for DataFrame
    pd.set_option('display.max_rows', 3)
    pd.set_option('display.max_columns', 6)
    print(df)

    # SQL insert query template for the Answers table
#    insert_query = """
#        INSERT INTO Answers (question_id, openended_answer, capability_id, project_id, binary_answer)
#        VALUES (%s, %s, %s, %s, %s)
#    """

    # Insert each row into the database
#    for index, row in df.iterrows():
#        values = (
#        row["question_id"], row["openended_answer"], row["capability_id"], row["project_id"], row["binary_answer"])
#        try:
#            db_config.execute_query_commit(insert_query, values)
#            print(f"Inserted row {index} successfully")
#        except Exception as e:
#            print(f"Error inserting row {index}: {e}")


#def main(document_path):
#    # Fetch and transform criteria data
#    criteria_data = query_criteria_from_db()
#    criteria_dic, binary_questions, openended_questions = transform_criteria_data(criteria_data)

    # Read document text
#    document_text = read_document(document_path)

    # Analyze document
#    results = analyze_document(document_text, criteria_dic, binary_questions, openended_questions)

#    with open('output/DocumentAnalysisResults.csv', 'w', newline='') as file:
#        writer = csv.writer(file)
#        writer.writerow(["Capability ID", "Level", "Question ID", "Criteria", "Binary Answer", "Justification"])

#        for criterion, result in results.items():
#            writer.writerow([result['capability_id'], result['level'],
#                             result['question_id'], criterion,
#                             result['binary_ans'], result['justification_ans']])

main('input/document_analysis.txt')
