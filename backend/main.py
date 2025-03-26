from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import logging
import time

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
    allow_origins=["http://localhost:3002"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    content: str
    id: str

@app.post("/api/message")
async def process_message(message: Message):
    try:
        logger.info(f"Received message with ID: {message.id}")
        # Save to Firebase
        ref = db.reference(f'/question/{message.id}')
        data = {
            'content': message.content,
            'timestamp': int(time.time() * 1000)  # Current time in milliseconds
        }
        logger.info(f"Attempting to save data to Firebase: {json.dumps(data, indent=2)}")
        ref.set(data)
        logger.info(f"Successfully saved message to Firebase at /question/{message.id}")
        
        return {"response": f"Message saved with ID: {message.id}"}
    except Exception as e:
        logger.error(f"Error saving message to Firebase: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 