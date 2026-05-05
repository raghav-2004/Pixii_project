---
title: Pixii Project
emoji: 🎨
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Pixii Project

An AI-powered image-to-image generation tool that creates professional marketing assets from raw product photos.

## Features
- **Background Removal**: Automatically removes backgrounds using `rembg`.
- **AI Captioning**: Generates descriptive captions for products.
- **Smart Prompt Engineering**: Uses Llama 3 (via Groq) to craft aesthetic background prompts.
- **AI Image Generation**: Uses Pollinations AI to generate high-quality marketing backgrounds.
- **Image Composition**: Merges products onto generated backgrounds for a studio-quality look.

## Project Structure
- `backend/`: FastAPI server handling the AI pipeline.
- `frontend/`: HTML/CSS/JS interface for uploading and viewing results.

## Setup

### Backend
1. Navigate to `backend/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (see `.env.example` if available) with:
   - `HF_API_KEY`: Hugging Face API key.
   - `GROQ_API_KEY`: Groq API key.
4. Run the server:
   ```bash
   python main.py
   ```

### Frontend
1. Open `frontend/index.html` in a browser or use a live server.

## Security
Note: The `.env` file is ignored by git to protect your API keys. Never commit your `.env` file!
