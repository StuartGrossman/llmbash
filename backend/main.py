from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
from llm_handlers.openai_handler import OpenAIChatHandler
from llm_handlers.gemini_handler import GeminiHandler
from llm_handlers.grok_handler import GrokHandler
from llm_handlers.deepseek_handler import DeepseekHandler
from llm_handlers.analysis_handler import AnalysisHandler
from llm_handlers.base_handler import BaseChatHandler
import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
import logging
import time
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin
try:
    cred = credentials.Certificate('firebase-service-account.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://apper-cb3d6-default-rtdb.firebaseio.com'
    })
    logger.info("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
    raise

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    content: str
    id: str
    userId: str

class AnalysisRequest(BaseModel):
    messageId: str
    responses: Dict[str, Any]
    userId: str

# Initialize handlers
openai_handler = OpenAIChatHandler(os.getenv('OPENAI_API_KEY'))
gemini_handler = GeminiHandler(os.getenv('GEMINI_API_KEY'))
grok_handler = GrokHandler(os.getenv('GROK_API_KEY'))
deepseek_handler = DeepseekHandler(os.getenv('DEEPSEEK_API_KEY'))
analysis_handler = AnalysisHandler()

@app.post("/api/message")
async def send_message(message: Message):
    try:
        # Create initial user data structure if it doesn't exist
        user_ref = db.reference(f'/users/{message.userId}')
        user_data = user_ref.get()
        if not user_data:
            user_ref.set({
                'created_at': int(time.time() * 1000),
                'last_active': int(time.time() * 1000)
            })

        # Save message to Firebase
        message_ref = db.reference(f'/users/{message.userId}/question/{message.id}')
        message_ref.set({
            'content': message.content,
            'timestamp': int(time.time() * 1000)
        })

        # Process responses from different LLMs concurrently
        tasks = [
            process_llm_response(message.id, message.content, message.userId, 'deepseek', deepseek_handler),
            process_llm_response(message.id, message.content, message.userId, 'grok', grok_handler),
            process_llm_response(message.id, message.content, message.userId, 'gemini', gemini_handler),
            process_llm_response(message.id, message.content, message.userId, 'openai', openai_handler)
        ]
        
        await asyncio.gather(*tasks)
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_llm_response(message_id: str, content: str, user_id: str, model: str, handler: BaseChatHandler):
    try:
        response_text = await handler.get_response(content)
        response_data = {
            'answer': response_text,
            'timestamp': int(time.time() * 1000)
        }
        db.reference(f'/users/{user_id}/question/{message_id}/{model}').set(response_data)
    except Exception as e:
        logger.error(f"Error processing {model} response: {str(e)}")
        error_data = {
            'error': str(e),
            'timestamp': int(time.time() * 1000)
        }
        db.reference(f'/users/{user_id}/question/{message_id}/{model}').set(error_data)

@app.post("/api/analyze")
async def analyze_responses(request: AnalysisRequest):
    try:
        # Get the original question from Firebase
        question_ref = db.reference(f'/users/{request.userId}/question/{request.messageId}')
        question_data = question_ref.get()
        
        if not question_data:
            raise HTTPException(status_code=404, detail="Question not found")

        # Analyze responses
        analysis_result = await analysis_handler.analyze_responses(
            question_data['content'],
            request.responses
        )

        # Save analysis result to Firebase
        db.reference(f'/users/{request.userId}/question/{request.messageId}/analysis').set(analysis_result)

        return analysis_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 