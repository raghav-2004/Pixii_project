import requests
import os
from dotenv import load_dotenv

# Load .env from the same directory as this script
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

HF_API_KEY = os.getenv("HF_API_KEY")
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

def check(url):
    res = requests.post(url, headers=headers, json={"inputs": "test"})
    print(url, res.status_code, res.text[:200])

check("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0")
check("https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev")
check("https://api-inference.huggingface.co/models/briaai/RMBG-1.4")
check("https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base")
