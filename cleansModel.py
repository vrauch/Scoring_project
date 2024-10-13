import pandas as pd

# Load the Excel spreadsheet into a DataFrame
df = pd.read_excel('input/master.xlsx')

# Identify columns requiring cleansing
columns_to_clean = ['Capability at Level', 'Features', 'Scoring Criteria at Level',	'Questions']  # Specify column names

# Cleanse the data in the identified columns
for col in columns_to_clean:
    # Apply cleaning operations based on your requirements
    # Example: Remove leading and trailing whitespace
    # df[col] = df[col].str.strip()
    df[col] = df[col].str.replace('---', '°').str.replace('-', '•').str.replace('** ','').str.replace('_','')

# Write the cleaned data back to an Excel file
df.to_excel('output/cleaned_master.xlsx', index=False)
