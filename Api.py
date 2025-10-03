from dotenv import load_dotenv
import os

# Load .env into environment
load_dotenv()

# Test print (masking most of the key for safety)
api_key = os.getenv("GROQ_API_KEY")
if api_key:
    print("Groq API Key loaded ✅ :", api_key[:6] + "..." + api_key[-4:])
else:
    print("❌ No Groq API Key found. Please check your .env file.")
