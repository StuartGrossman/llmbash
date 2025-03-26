from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
from llm_handlers import (
    LLMHandlerFactory,
    AnalysisHandler
)
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

# Initialize Firebase
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://test-db.firebaseio.com'
})

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
    user_id: str
    message_id: str
    content: str
    llm_types: List[str]

class AnalysisRequest(BaseModel):
    user_id: str
    message_id: str
    responses: Dict[str, str]

@app.post("/api/send_message")
async def send_message(message: Message):
    """
    Send a message to be processed by multiple LLM handlers.
    """
    try:
        # Store message in Firebase
        ref = db.reference(f'messages/{message.user_id}/{message.message_id}')
        await ref.set({
            'content': message.content,
            'timestamp': {'serverValue': 'timestamp'}
        })

        # Initialize LLM handlers
        factory = LLMHandlerFactory()
        handlers = []
        for llm_type in message.llm_types:
            try:
                handler = factory.get_handler(llm_type, "test_api_key")  # Replace with actual API key
                handlers.append(handler)
            except ValueError as e:
                logger.error(f"Error creating handler for {llm_type}: {str(e)}")

        # Get responses from all handlers concurrently
        async def get_response(handler):
            try:
                return await handler.generate_response(message.content)
            except Exception as e:
                logger.error(f"Error getting response from {handler.__class__.__name__}: {str(e)}")
                return f"Error: {str(e)}"

        responses = await asyncio.gather(*[get_response(handler) for handler in handlers])

        # Store responses in Firebase
        response_data = {}
        for handler, response in zip(handlers, responses):
            response_data[handler.__class__.__name__.lower().replace('handler', '')] = response

        await ref.child('responses').set(response_data)

        return {
            "message": "Message sent successfully",
            "message_id": message.message_id
        }

    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze_responses")
async def analyze_responses(request: AnalysisRequest):
    """
    Analyze responses from multiple LLM handlers.
    """
    try:
        # Get responses from Firebase
        ref = db.reference(f'messages/{request.user_id}/{request.message_id}/responses')
        responses = await ref.get()

        if not responses:
            raise HTTPException(status_code=404, detail="No responses found")

        # Analyze responses
        analyzer = AnalysisHandler()
        analysis = await analyzer.analyze_responses(responses)

        # Store analysis in Firebase
        await ref.parent.child('analysis').set({
            'content': analysis,
            'timestamp': {'serverValue': 'timestamp'}
        })

        return {
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error in analyze_responses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 