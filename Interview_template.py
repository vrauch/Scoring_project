import openai
import openai.error
import os
import db_config


# Setup for Answers Template
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QUESTION_TABLE = "e2caf.Questions"
