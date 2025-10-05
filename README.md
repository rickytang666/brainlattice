<div align="center">

<img src="frontend/public/brainlattice.png" alt="BrainLattice Logo" width="350">

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
- **Deep concept exploration** - Cmd+Shift+click any node for detailed insights: overview, important formulas, theorems, related concepts
- **AI-generated study guides** - Overviews, summaries, key concepts
- **Audio study materials** - Listen to your content while commuting/gym
- **Smart concept mapping** - AI finds relationships you'd miss reading linearly
- **Dark/light themes** - Study at 3am without burning your eyes

## How It Works

1. **PDF → Text** → PyPDF extracts raw content
2. **Text → Concepts** → OpenRouter (Grok 4 Fast) identifies key ideas and relationships
3. **Concepts → Graph** → Gemini maps connections and hierarchy
4. **Graph → Materials** → Generate overviews, audio scripts, study guides
5. **Script → Audio** → ElevenLabs converts to speech for audio study guides

Result: Interactive concept map you can explore + AI-generated study materials

## Setup

**Prerequisites:**

- Python 3.8+
- Node.js 18+
- API keys (see below)

**Backend:**

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Server runs on `http://localhost:8000`

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

App runs on `http://localhost:3000`

**Test it:**

1. Go to `localhost:3000`
2. Drop a PDF (textbook, lecture notes, etc.)
3. Watch it process and generate your knowledge graph

## API Keys

```bash
# backend/.env
GEMINI_API_KEY=your_key          # Deep concept analysis & relationships
OPENROUTER_API_KEY=your_key      # AI digest, cheatsheets, audio scripts
ELEVENLABS_API_KEY=your_key      # Text-to-speech audio generation
FIREBASE_SERVICE_ACCOUNT_PATH=secrets/firebase_private.json
```

## Tech Stack

**Backend:**

- **FastAPI** - Python web framework
- **PyPDF** - PDF text extraction
- **OpenRouter (Grok 4 Fast)** - AI digest, cheatsheets, audio scripts
- **Google Gemini 2.5 Flash Lite** - Deep concept analysis, relationship mapping
- **Google Gemini 2.0 Flash Lite** - Overview of concepts when the user cmd + shift + clicks on a node
- **ElevenLabs** - Text-to-speech audio generation
- **Firebase Firestore** - NoSQL database
- **Docker** - Containerization

**Frontend:**

- **Next.js 14** - React framework with App Router
- **React Force Graph** - Interactive 3D graph visualization
- **TailwindCSS** - CSS framework with dark/light themes
- **Shadcn UI** - Component library
- **TypeScript** - Type-safe development
- **Vercel** - Frontend hosting

**Cloud & Deployment:**

- **Google Cloud Platform** - Backend hosting
- **Firebase** - Authentication, database, cloud functions
- **Vercel** - Frontend deployment

---

_Your brain thinks in networks. Your textbook should too._

_Studying with BrainLattice is navigating the earth on the atmosphere._
