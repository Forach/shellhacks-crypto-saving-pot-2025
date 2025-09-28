import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # <-- key line

print("Using model:", MODEL)
print("API key loaded?", bool(os.getenv("GOOGLE_API_KEY")))

model = genai.GenerativeModel(MODEL)
resp = model.generate_content("Say hello in under 10 words.")
print("Response:", resp.text)
