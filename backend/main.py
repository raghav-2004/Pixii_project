import os
import io
import base64
import requests
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load .env from the same directory as this script
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_API_KEY = os.getenv("HF_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

HF_HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}
GROQ_HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Switching back to direct inference API with stable models
HF_BASE_URL = "https://api-inference.huggingface.co/models"

def query_hf(model_id, data, is_json=False, max_retries=3):
    api_url = f"{HF_BASE_URL}/{model_id}"
    for attempt in range(max_retries):
        try:
            if is_json:
                response = requests.post(api_url, headers=HF_HEADERS, json=data, timeout=60)
            else:
                response = requests.post(api_url, headers=HF_HEADERS, data=data, timeout=60)
            
            if response.status_code == 200:
                return response.content
            elif response.status_code == 503:
                print(f"Model {model_id} loading (503), waiting 15s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(15)
            else:
                print(f"Error {response.status_code} from {model_id}: {response.text}")
                return None
        except Exception as e:
            print(f"Request failed for {model_id}: {e}")
            time.sleep(2)
    return None

def query_groq(payload):
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    # Using llama-3.1-8b-instant as it is very reliable
    payload["model"] = "llama-3.1-8b-instant"
    try:
        response = requests.post(api_url, headers=GROQ_HEADERS, json=payload, timeout=20)
        if response.status_code != 200:
            print(f"Error {response.status_code} from Groq: {response.text}")
            return None
        return response.json()
    except Exception as e:
        print(f"Groq request failed: {e}")
        return None

@app.post("/generate-marketing-image")
async def generate_marketing_image(file: UploadFile = File(...)):
    try:
        raw_image = await file.read()
        current_image = raw_image
        
        # 1. Background Removal
        print("Step 1: Running local rembg for background removal...")
        from rembg import remove
        try:
            bg_removed = remove(current_image)
            current_image = bg_removed
            print("Background removed successfully using rembg.")
        except Exception as e:
            print(f"rembg failed: {e}")
            
        # 2. Captioning
        print("Step 2: Running BLIP...")
        # Since API might be failing, we'll try it but default to "a product"
        caption_res = query_hf("Salesforce/blip-image-captioning-large", raw_image)
        caption = "a product"
        if caption_res:
            import json
            try:
                res_json = json.loads(caption_res)
                if isinstance(res_json, list) and 'generated_text' in res_json[0]:
                    caption = res_json[0]['generated_text']
            except:
                pass
        print(f"Caption: {caption}")

        # 3. Prompt Generation
        print("Step 3: Running Llama (Groq) for Prompt Engineering...")
        prompt_payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a world-class product photography prompt engineer. Create a prompt for an EMPTY background/podium for a marketing image. The background should be interesting and colorful, but perfectly balanced to complement the product's colors and design. IT MUST NOT CONTAIN ANY PRODUCT, ONLY THE EMPTY DISPLAY AREA/BACKGROUND. Include keywords like 'empty podium', 'color harmony', 'studio lighting', 'aesthetic background', '8k', and 'commercial photography'. Output ONLY the final prompt."
                },
                {
                    "role": "user",
                    "content": f"Create an empty background prompt for this product: {caption}"
                }
            ],
            "temperature": 0.8
        }
        
        marketing_prompt = f"empty product podium, colorful balanced aesthetic background, studio lighting, 8k, commercial ad, no product"
        groq_res = query_groq(prompt_payload)
        if groq_res:
            marketing_prompt = groq_res['choices'][0]['message']['content'].strip()
            
        print(f"Marketing Prompt: {marketing_prompt}")

        # 4. Final Image Generation
        print("Step 4: Running Image Generation for final marketing asset...")
        
        # Pollinations might fail with 429 if prompt is too long. Let's truncate and clean it.
        clean_prompt = marketing_prompt[:250].replace('\n', ' ').strip()
        import random
        seed = random.randint(1, 10000)
        
        # Using Pollinations API for reliable, fast, and free image generation based on our Llama3 prompt
        pollinations_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(clean_prompt)}?width=1024&height=1024&nologo=true&seed={seed}"
        
        try:
            image_res = requests.get(pollinations_url, timeout=30)
            if image_res.status_code == 200:
                bg_image_bytes = image_res.content
                
                # Overlay the transparent product on the generated background
                from PIL import Image
                
                bg_img = Image.open(io.BytesIO(bg_image_bytes)).convert("RGBA")
                product_img = Image.open(io.BytesIO(current_image)).convert("RGBA")
                
                # Resize product to fit nicely in the center (e.g. 60% of the background height)
                target_height = int(bg_img.height * 0.6)
                aspect_ratio = product_img.width / product_img.height
                target_width = int(target_height * aspect_ratio)
                product_img = product_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Calculate position (center bottom or center)
                x = (bg_img.width - target_width) // 2
                y = (bg_img.height - target_height) // 2 + int(bg_img.height * 0.05) # slightly lower than dead center
                
                # Paste product onto background using the product's alpha channel as mask
                bg_img.paste(product_img, (x, y), product_img)
                
                # Convert back to bytes
                output_buffer = io.BytesIO()
                bg_img.convert("RGB").save(output_buffer, format="JPEG", quality=95)
                final_image = output_buffer.getvalue()
                print("Image composition successful.")
            else:
                print(f"Pollinations API Error: {image_res.status_code}")
                # Fallback to white background if Pollinations fails
                from PIL import Image
                bg_img = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
                product_img = Image.open(io.BytesIO(current_image)).convert("RGBA")
                target_height = int(bg_img.height * 0.6)
                aspect_ratio = product_img.width / product_img.height
                target_width = int(target_height * aspect_ratio)
                product_img = product_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                x = (bg_img.width - target_width) // 2
                y = (bg_img.height - target_height) // 2
                bg_img.paste(product_img, (x, y), product_img)
                output_buffer = io.BytesIO()
                bg_img.convert("RGB").save(output_buffer, format="JPEG", quality=95)
                final_image = output_buffer.getvalue()
        except Exception as e:
            print(f"Pollinations generation/composition failed: {e}")
            final_image = current_image

        base64_image = base64.b64encode(final_image).decode('utf-8')
        
        return JSONResponse(content={
            "success": True,
            "caption": caption,
            "prompt": marketing_prompt,
            "image": f"data:image/jpeg;base64,{base64_image}"
        })

    except Exception as e:
        print(f"Pipeline Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


