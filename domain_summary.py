import pandas as pd
import os
import analysis_modules

path = os.getenv('FILE_PATH')
os.chdir(path)

results = []
#Load Data
file_name = 'priority_domain_summary.csv'
df = analysis_modules.domain_summary_load(file_name)

for _, row in df.iterrows():
    domain = row["Domain"]
    data = row["Alignment"]
    # First Iteration
    prompt = f""" 
    write a summary for the following analysis: {data} 
     """
    domain_recommendation = analysis_modules.summarize_paragraph(domain, data, prompt)
    domain_recommendation = analysis_modules.clean_and_normalize_text(domain_recommendation)
    domain_recommendation = analysis_modules.to_sentence_case(domain_recommendation)

    # Updating variables for the second iteration
    data = domain_recommendation
    prompt = f"""Based on a comprehensive review of various capabilities within the {domain} domain, results labeled as {data} have revealed both strengths in areas like data virtualization and metadata management, and notable gaps in data governance and disaster recovery planning. Construct a concise, one-paragraph summary that reflects the overall state of these capabilities. Highlight the principal areas of strength and those requiring significant improvement. Conclude with five broad recommendations for enhancing the domain's overall effectiveness and preparing it for future challenges. Focus on delivering practical advice that can be universally understood and is not based on any specific evaluative criteria. Ensure that the summary is actionable and aimed at boosting operational efficacy without referencing structured analysis language or specific alignment criteria."""

    # Second iteration
    dom_final = analysis_modules.summarize_paragraph(domain, data, prompt)

    dom_parts = [f"{domain}|{data}"]
    dom_data = [item.split('|') for item in dom_parts]
    results.append(dom_data[0])
df_dom = pd.DataFrame(results, columns=['Domain', 'Assessment'])
df_dom.to_csv('domain_assessments.csv', index=False)