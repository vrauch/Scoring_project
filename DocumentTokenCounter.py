import tiktoken


def read_document(file_path):
    with open(file_path, 'r', errors='ignore') as file:
        return file.read()

# Initialize the encoding for the specific OpenAI model
encoding = tiktoken.get_encoding("cl100k_base")  # For GPT-3.5 and GPT-4

# Text document to analyze
document = read_document('input/document_analysis.txt')

# Encode the document to tokens
tokens = encoding.encode(document)

# Output the token count
print(len(tokens))