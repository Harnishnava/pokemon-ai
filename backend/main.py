from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import os
from typing import List, Optional
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS with more detailed settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"

# Initialize Groq LLM
try:
    api_key = os.getenv("OPENAI_API_KEY")  # Using the same env variable
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile"
    )
except Exception as e:
    logger.error(f"Error initializing Groq LLM: {str(e)}")
    raise

# Initialize embeddings model
try:
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"Error initializing SentenceTransformer: {str(e)}")
    raise

# Initialize vector store
vector_store = None

async def initialize_pokemon_database():
    global vector_store
    try:
        # Fetch first 151 Pokemon data
        pokemon_data = []
        for i in range(1, 152):
            try:
                response = requests.get(f"{POKEAPI_BASE_URL}pokemon/{i}")
                response.raise_for_status()
                data = response.json()
                pokemon_info = f"""
                Pokemon: {data['name']}
                ID: {data['id']}
                Types: {', '.join([t['type']['name'] for t in data['types']])}
                Abilities: {', '.join([a['ability']['name'] for a in data['abilities']])}
                Height: {data['height']}
                Weight: {data['weight']}
                Stats: {', '.join([f"{stat['stat']['name']}: {stat['base_stat']}" for stat in data['stats']])}
                """
                pokemon_data.append(pokemon_info)
            except Exception as e:
                logger.error(f"Error fetching Pokemon {i}: {str(e)}")
                continue
        
        if not pokemon_data:
            raise ValueError("No Pokemon data was fetched successfully")

        # Create embeddings
        embeddings = model.encode(pokemon_data)
        
        # Convert embeddings to numpy arrays for better computation
        embeddings = np.array([np.array(emb) for emb in embeddings])
        
        # Store embeddings
        vector_store = list(zip(pokemon_data, embeddings))
        logger.info(f"Successfully initialized database with {len(pokemon_data)} Pokemon")
    except Exception as e:
        logger.error(f"Error in initialize_pokemon_database: {str(e)}\n{traceback.format_exc()}")
        raise

class Query(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None

@app.on_event("startup")
async def startup_event():
    await initialize_pokemon_database()

@app.get("/")
async def root():
    return {"message": "Pokemon RAG AI API"}

@app.post("/chat")
async def chat(query: Query):
    try:
        if not vector_store:
            raise HTTPException(status_code=500, detail="Pokemon database not initialized")

        # Create query embedding
        query_embedding = model.encode([query.message])[0]
        
        # Find similar Pokemon (cosine similarity)
        similarities = []
        for text, embedding in vector_store:
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append((similarity, text))
        
        # Get top 3 most similar Pokemon
        similarities.sort(key=lambda x: x[0], reverse=True)
        context = "\n".join(text for _, text in similarities[:3])
        
        # Prepare messages for the chat
        messages = [
            SystemMessage(content=f"""You are a knowledgeable Pokemon AI assistant. Use the following Pokemon information to answer questions accurately:
            
            {context}
            
            Always be friendly and enthusiastic about Pokemon. If you're not sure about something, just say so."""),
            HumanMessage(content=query.message)
        ]
        
        # Get response from Groq
        ai_response = llm(messages)
        
        # Extract source Pokemon names from context
        sources = [line.split("Pokemon:")[1].strip() for line in context.split("\n") if "Pokemon:" in line]
        
        return ChatResponse(
            response=ai_response.content,
            sources=sources
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
