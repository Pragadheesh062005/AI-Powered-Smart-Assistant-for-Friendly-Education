import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
models = [m.name for m in genai.list_models()]
print(models)
