from fastapi import APIRouter, Depends, HTTPException
import requests
from chat.schemas import Query
from database import get_db

router = APIRouter(prefix="/generation", tags=["Generation"])

@router.post("/generate_chat_name")
async def generate_chat_name(query: Query):
    try:
        prompt = f"""You are a helpful assistant whose only job is to create concise chat titles. 
Given the very first user message, generate a title in exactly 3–5 words that captures its specific topic—nothing generic or off-topic.

Examples:
User message: "How to make pull ups?"
Title: "How to Do Pull-Ups"

User message: "Tips for installing Python packages on Windows"
Title: "Installing Python Packages on Windows"

User message: "What’s the best way to learn guitar chords?"
Title: "Learning Guitar Chords Effectively"

User message: "How can I improve my sleep schedule?"
Title: "Improving Your Sleep Schedule"

---
User message: "{query.prompt}"
Title:"""
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": query.model, "prompt": prompt, "stream": query.stream},
        )
        response.raise_for_status()
        return {"generated_text": response.json()["response"]}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

@router.post("/generate")
async def generate_text(query: Query):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": query.model, "prompt": query.prompt, "stream": query.stream},
        )
        response.raise_for_status()
        return {"generated_text": response.json()["response"]}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
