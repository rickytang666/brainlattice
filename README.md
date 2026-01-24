<div align="center">

<img src="frontend/public/brainlattice.png" alt="BrainLattice Logo" width="350">

_Textbook becomes mind map, **before** you even finish reading._

**BrainLattice** maps the lattice structure of knowledge onto your brain's neural network. Learning designed for how the mind actually works.

</div>

<div align="center">

[![Next.js 14](https://img.shields.io/badge/Next.js-black?logo=nextdotjs)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-%23009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Fish Audio](https://img.shields.io/badge/Fish%20Audio-Blue)](https://fish.audio/)
[![Firebase](https://img.shields.io/badge/Firebase-ffca28?logo=firebase&logoColor=black)](https://firebase.google.com/)

</div>

---

## Overview

Traditional learning forces linear consumption of non-linear information. **BrainLattice** flips this paradigm by transforming static PDF textbooks into interactive, explorable knowledge graphs. It uses advanced LLMs to extract core concepts, identify relationships, and generate high-fidelity study materials, allowing users to understand the "system" of a subject before memorizing the details.

## Key Features

- **Interactive Knowledge Graphs**: Visualize concepts in 3D space. Zoom, pan, and explore connections dynamically.
- **Deep Concept Analysis**: Click any node to retrieve AI-generated insights, including key formulas, theorems, and prerequisites.
- **Automated content generation**: Instantly create study guides, cheatsheets, and summaries from raw PDF text.
- **High-Fidelity Audio**: Listen to customized audio study guides generated via **Fish Audio** (replacing legacy ElevenLabs implementation).
- **Flexible Ingestion**: Drag-and-drop support for textbooks, research papers, and lecture notes.

## Tech Stack

### AI & Core Services

- **Google Gemini 2.5 Flash Lite**: Deep concept extraction and relationship mapping.
- **OpenRouter (Grok 4 Fast)**: Speed-optimized text summarization and study material generation.
- **Fish Audio**: Cost-effective, high-quality text-to-speech engine.
- **PyPDF**: Raw text extraction from documents.

### Architecture

- **Frontend**: Next.js, React Force Graph, TailwindCSS, Shadcn UI.
- **Backend**: FastAPI (Python).
- **Database**: Firebase Firestore.
- **Infrastructure**: Docker, Google Cloud Run, Vercel.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Fish Audio API Key](https://fish.audio/)
- [Google Gemini API Key](https://ai.google.dev/)
- [OpenRouter API Key](https://openrouter.ai/keys)
- [Firebase Service Account](https://firebase.google.com/docs/admin/setup)

### Installation

1. **Backend Setup**

   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

   _Server runs at `http://localhost:8000`_

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   _App runs at `http://localhost:3000`_

### Configuration (`backend/.env`)

```bash
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
FISH_AUDIO_API_KEY=your_fish_audio_key
FIREBASE_SERVICE_ACCOUNT_PATH=secrets/firebase_private.json
```

## How It Works

1.  **Ingestion**: PyPDF extracts raw text from uploaded documents.
2.  **Synthesis**: Grok 4 (via OpenRouter) identifies sequential concepts.
3.  **Mapping**: Gemini 2.5 constructs the hierarchical knowledge graph.
4.  **Generation**: The system produces study guides and audio scripts.
5.  **Audio**: Scripts are streamed to **Fish Audio** for TTS generation.

---

[View on Devpost](https://devpost.com/software/brainlattice)
