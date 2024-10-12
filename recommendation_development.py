import pandas as pd
import os
import analysis_modules

path = os.getenv('FILE_PATH')
os.chdir(path)

#%%
df = pd.read_excel('response.xlsx')
df['Capability'] = df['Capability']
df['Assessment'] = df['Assessment']
df['Criteria'] = df['Criteria']
#print(df)

results = []
for _, row in df.iterrows():
    capability = row['Capability']
    assessment = row["Assessment"]
    criteria = row['Criteria']
    prompt = f"""PLEASE FOLLOW THESE INSTRUCTIONS CAREFULLY AND PRECISELY: Conduct an analysis based on the provided 
    Level 1 maturity assessment and the defined criteria for Level 2 maturity. Then, articulate a clear and concise 
    narrative in one or two sentences. This narrative should implicitly identify a key area where improvement is needed 
    without directly mentioning it as an 'opportunity for improvement' or using any similar labels. The response should 
    seamlessly integrate the identified area into the narrative, focusing solely on the description of the area needing 
    improvement without any explicit labeling or recommendations. Remember, do not use any form of the phrase 
    'opportunity for improvement' or include any additional formatting."
    "Level 1 maturity assessment: {assessment}"
    "Criteria for Level 2 maturity: {criteria}"
    """
    opportunity = analysis_modules.ia_analysis(criteria, assessment, prompt)
    opportunity = analysis_modules.clean_and_normalize_text(opportunity)
    opportunity = analysis_modules.to_sentence_case(opportunity)
    #print(opportunity)

    prompt = f"""Your task is to analyze a scenario involving the progression from a Level 1 to Level 2 maturity in a 
    business context. 
    Begin by considering a Level 1 Assessment {assessment}. 
    The criteria for achieving Level 2 maturity: {criteria}. 
    Given this context, provide an analysis that seamlessly transitions into 1 concise recommendation. 
    This recommendation should encapsulate a strategy for addressing the noted gaps and aligning with Level 2 maturity criteria. 
    The insight should be presented in a single paragraph without explicitly stating its purpose as a recommendation or including any form of conclusion.
    Key Instructions:
    -   Do not explicitly mention the insight is a recommendation.
    -	Avoid directly stating the analysis is for transitioning to Level 2 maturity. 
    -	Provide the insight in one concise paragraph without a concluding statement.
    """
    # Submit to analysis_modules.ia_analysis function to get a new set of recommendations
    recommendation = analysis_modules.ia_analysis(criteria, assessment, prompt)
    recommendation = analysis_modules.clean_and_normalize_text(recommendation)
    recommendation = analysis_modules.to_sentence_case(recommendation)
    #print(recommendation)

    parts = [f"{capability}|{opportunity}|{recommendation}\n"]
    data = [item.split('|') for item in parts]
    results.append(data[0])

    df = pd.DataFrame(results, columns=['Capability', 'Opportunity', 'Recommendation'])

print(df)

#%%
# Convert processed data to DataFrame
df.to_csv('recommendations.csv', index=False, quoting=1)