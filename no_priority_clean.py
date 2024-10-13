import os
import analysis_modules
import re
import pandas as pd

path = os.getenv('FILE_PATH')
os.chdir(path)

results = []
# Load Data
file_name = 'non_priority.xlsx'
df = analysis_modules.non_priority_load(file_name)

for _, row in df.iterrows():
    domain = row['Domain']
    capability = row["Capability"]
    response = row['Response']

    if str(response).lower() in ['nan', 'none', '']:
        continue

    response = re.sub('(?<=[^,])/(?=[^,])', '', response)
    response = response.replace('//', ' ')
    response = response.lstrip('/')
    response = response.rstrip('/')


    criteria = row['Criteria3']
    criteria = re.sub('<.*?>|[\n\r\]]', '', criteria)
    criteria = ' '.join(criteria.split())


    cleaned = analysis_modules.clean_and_normalize_text(response)
    cleaned = analysis_modules.to_sentence_case(cleaned)

    results.append((domain, capability, cleaned, criteria))
df_results = pd.DataFrame(results, columns=['Domain', 'Capability', 'Cleaned_Response', 'Criteria'])
df_results.to_csv('non_priority_cleaned.csv', index=False)


