<div align="center">

<img src="frontend/public/brainlattice.png" alt="BrainLattice Logo" width="200">

_Textbook becomes mind map, **before** you even finish reading._

**BrainLattice** = your brain's neural network + the lattice structure of knowledge. Because learning should work like your mind does.

</div>

---

## Why It Exists

Traditional learning is backwards. You read 200 pages sequentially, memorize isolated facts, and somehow expect to understand how everything connects. It's like trying to understand a city by walking down one street.

Your brain thinks in networks, not lines. When you truly get something, you see how concept A influences concept B, which builds toward concept C. That's the difference between knowing facts and understanding systems.

BrainLattice flips this. Upload a textbook, get the entire landscape first. See connections, identify core concepts, dive deep into what matters. Perfect for course catchup, exam prep, or just getting complex subjects.

## Features

- **Drag & drop PDFs** - Works with any textbook, lecture notes, research papers
- **Interactive knowledge graphs** - Click nodes, explore connections, zoom in/out
- **AI-generated study guides** - Overviews, summaries, key concepts
- **Audio study materials** - Listen to your content while commuting/gym
- **Smart concept mapping** - AI finds relationships you'd miss reading linearly
- **Dark/light themes** - Study at 3am without burning your eyes

## How It Works

1. **PDF → Text** → PyPDF2 extracts raw content
2. **Text → Concepts** → OpenRouter (Grok 4 Fast) identifies key ideas and relationships
3. **Concepts → Graph** → Gemini maps connections and hierarchy
4. **Graph → Materials** → Generate overviews, audio scripts, study guides
5. **Script → Audio** → ElevenLabs converts to speech for audio study guides

Result: Interactive concept map you can explore + AI-generated study materials

## Setup

**Backend:**

```bash
cd backend
pip install -r requirements.txt
cp secrets/env.yaml .env  # Add your API keys
python main.py
```

**Frontend:**

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
npm run dev
```

Go to `localhost:3000`, drop a PDF, watch it work.

## API Keys

```bash
# backend/.env
GEMINI_API_KEY=your_key          # Concept relationships
OPENROUTER_API_KEY=your_key      # Text processing
ELEVENLABS_API_KEY=your_key      # Audio generation
FIREBASE_SERVICE_ACCOUNT_PATH=secrets/firebase_private.json
```

## Stack

**Backend:** FastAPI + PyPDF2 + OpenRouter + Gemini + ElevenLabs + Firebase  
**Frontend:** Next.js + React Flow + TailwindCSS + TypeScript

## Deploy

Backend: `vercel --prod`  
Frontend: Connect repo to Vercel

---

_Your brain thinks in networks. Your textbook should too._
