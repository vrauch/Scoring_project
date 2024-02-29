import re
def remove_chinese(text):
    result = ''
    for char in text:
        if '\u4e00' <= char <= '\u9fa5':
            continue
        result += char
    return result
text = "Does your organization have a complete set of standardized tools and processes for infrastructure needs?您的組織是否擁有一套完整的標準化工具和流程來滿足基礎架構需求？"
print(re.sub(r"[^\w\s]", "", remove_chinese(text)))