# Pokemon RAG AI Assistant

An interactive Pokemon assistant that uses RAG (Retrieval Augmented Generation) to provide accurate information about Pokemon by combining the PokeAPI database with AI capabilities.

## Features
- Chat-based interface for Pokemon queries
- Integration with PokeAPI for accurate Pokemon data
- RAG system for enhanced AI responses
- Modern Next.js frontend
- FastAPI backend

## Setup

### Backend
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend:
```bash
uvicorn backend.main:app --reload
```

### Frontend
1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

## Environment Variables
Create a `.env` file in the root directory with:
```
OPENAI_API_KEY=your_openai_api_key
```
