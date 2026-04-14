# Conversational Podcast

An AI-powered interactive podcast application. Provide sources, get a generated conversational podcast, and interject with questions during playback.

## Features

- 📄 **Multi-source ingestion** – plain text, URLs, or PDF/TXT file uploads
- 🤖 **AI script generation** – GPT-4o-mini turns your sources into a natural 2-host podcast conversation
- 🔊 **Text-to-speech audio** – each script segment is voiced by OpenAI TTS (two distinct voices)
- ▶️ **Segment player** – play the podcast sequentially, track progress, pause, resume, restart
- 💬 **Live interjection** – pause at any point, ask a text question (or use your microphone), and get a contextual answer backed by RAG over your source material
- 🎤 **Voice input** – record questions with your microphone; Whisper transcribes them automatically

## Architecture

```
.
├── backend/          # Python FastAPI API
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, static audio mount
│   │   ├── database.py       # SQLite schema (talks, sources, segments, interactions)
│   │   ├── models.py         # Pydantic request/response models
│   │   ├── routes/
│   │   │   ├── talks.py      # CRUD + generation trigger
│   │   │   └── interact.py   # Text + voice Q&A endpoint
│   │   └── services/
│   │       ├── source_processor.py  # Text/PDF/URL extraction + OpenAI embeddings
│   │       ├── script_generator.py  # GPT-4o-mini script generation
│   │       ├── audio_generator.py   # OpenAI TTS per segment
│   │       └── rag_service.py       # Cosine-similarity RAG + GPT answer
│   ├── requirements.txt
│   └── .env.example
└── frontend/         # React + Vite SPA
    └── src/
        ├── pages/
        │   ├── HomePage.jsx    # List talks
        │   ├── NewTalkPage.jsx # Create talk with sources
        │   └── TalkPage.jsx    # Podcast player + interaction panel
        └── components/
            ├── PodcastPlayer.jsx    # Audio player with segment tracking
            └── InteractionPanel.jsx # Q&A + voice recording
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and fill in your API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

python run.py
# API available at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

### Environment Variables (backend)

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `DATABASE_PATH` | `./data/podcast.db` | SQLite database file path |
| `AUDIO_DIR` | `./data/audio` | Directory where generated MP3 files are stored |
| `PORT` | `8000` | Server port |

## Usage

1. Open **http://localhost:5173**
2. Click **New Talk** and paste text, a URL, or upload a PDF
3. Wait for the script and audio to be generated (shown with a spinner)
4. Click **▶ Play** to start the podcast
5. At any time, click **💬 Interject** to pause and ask a question
6. Your question is answered using the original source material (RAG)
7. Click **▶ Resume** to continue where you left off

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/talks/` | List all talks |
| `POST` | `/api/talks/` | Create talk from text/URL sources |
| `POST` | `/api/talks/upload` | Create talk from file upload |
| `GET` | `/api/talks/{id}` | Get talk details + segments + interactions |
| `DELETE` | `/api/talks/{id}` | Delete a talk |
| `POST` | `/api/talks/{id}/interact` | Ask a text question |
| `POST` | `/api/talks/{id}/interact/voice` | Ask a voice question (audio upload) |
| `GET` | `/audio/{filename}` | Serve generated audio files |
