import openai

# Set your OpenAI API key
openai.api_key = '...'

# The analyze_sentence function sends a request to the OpenAI API with the given sentence and criteria, and returns the decision made by the model.
def analyze_sentence(sentence, criteria):
    response = openai.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=f"Sentence: {sentence}\nCriteria: {criteria}\nDecision:",
        temperature=0.9,
        max_tokens=100,
        stop=["\n"]
    )
    decision = response.choices[0].text.strip()
    return decision

# The main function prompts the user to input the sentence and criteria they want to analyze, calls analyze_sentence with these inputs, and prints out the decision.
def main():
    sentence = "TFS automatic deployment"
    #sentence = input("Enter the sentence you want to analyze: ")
    criteria = 'Standardized Toolset: Listen for comprehensive toolset,organization-wide standards,and unified processes.Tooling for Development and Deployment: Keywords like integrated tooling,support for application development,and deployment tool standardization are crucial.Infrastructure Templates: Terms such as standardized templates,consistent deployment, and infrastructure efficiency indicate a mature approach.'
    #criteria = input("Enter the criteria for analysis: ")
    criteria_b = "What percentage is the sentences meet the criteria: " + criteria
    decision = analyze_sentence(sentence, criteria_b)
    #print(f"The decision for the sentence '{sentence}' based on the criteria '{criteria}' is: {decision}")
    print(f'{decision}')
    

if __name__ == "__main__":
    main()
