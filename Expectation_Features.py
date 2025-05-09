import pandas as pd
import os
import analysis_modules

path = os.getenv('FILE_PATH')
os.chdir(path)

#%%
file_path = 'input/Result_8.csv'

df = pd.read_csv(file_path)

print("Column Details")
print(df.dtypes)

# ---------------------------
# Prompt Generation
# ---------------------------
def generate_prompt(domain_name, capability_id, capability, level, description, domain_description, capability_description, industry, country):
    if not all([industry, country, domain, capability_id, capability, level, description, domain_description, capability_description]):
        raise ValueError("All input variables must be provided and non-empty.")

results = []
for _, row in df.iterrows():
    domain_name = row['domain_name']
    subdomain_name = row['subdomain_name']
    level = row['level']
    description = row['description']
    capability_id = row['capability_id']
    capability_name = row['capability_name']
    capability_description = row['capability_description']

    prompt = f"""You are a strategic maturity analyst for organizational operations, responsible for assessing maturity levels and crafting actionable recommendations. Using the provided input data table, analyze the “level,” “description,” and “capability description” columns for each row. Based on this analysis:
	1.	Develop clear expectations that define where the organization should ideally be at each maturity level.
	2.	Suggest a set of features or initiatives that would align the organization with the expectations for that level.

The output must be in the following structured format:
	•	Domain: {domain_name}
	•	Sub Domain: {subdomain_name}
	•	Capability ID: {capability_id}
	•	Capability Name: {capability_name}
	•	Level: {level}
	•	Expectation: [Derived expectation for the maturity level]
	•	Features: [Specific features or initiatives needed to meet the expectation]

Use the example provided below to guide your response formatting:

Example Output:
	•	Domain: Strategy & Governance
	•	Sub Domain: Communication
	•	Capability ID: 749
	•	Capability Name: Standards
	•	Level: 2
	•	Expectation: At this maturity level, the organization should transition from siloed initiatives to a standardized approach, improving cloud transformation and governance.
	•	Features: Evidence of standardized processes, enhanced understanding of cloud economics, and active steps toward comprehensive governance.

Ensure that the generated expectations and features are precise, actionable, and aligned with the given maturity descriptions."
    """

    opportunity = analysis_modules.ia_analysis(prompt)
    #print(opportunity)


    parts = [f"{domain_name}|{capability_id}|{capability_name}|{level}|{Expectation}|{Feature}\n"]
    data = [item.split('|') for item in parts]
    results.append(data[0])

    df = pd.DataFrame(results, columns=['Capability', 'Opportunity', 'Recommendation'])

print(df)

#%%
# Convert processed data to DataFrame
df.to_csv('recommendations.csv', index=False, quoting=1)