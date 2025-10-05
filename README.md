<div align="center">

<img src="frontend/public/brainlattice.png" alt="BrainLattice Logo" width="350">

_Textbook becomes mind map, **before** you even finish reading._

**BrainLattice** = your brain's neural network + the lattice structure of knowledge. Because learning should work the way your mind does.

</div>

<!-- Badges -->

[![Next.js 14](https://img.shields.io/badge/Next.js-14-black?logo=nextdotjs)](https://nextjs.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-%2306B6D4.svg?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Shadcn](https://img.shields.io/badge/Shadcn-UI-000000?logo=shadcn&logoColor=white)](https://ui.shadcn.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-%23009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Firebase](https://img.shields.io/badge/Firebase-ffca28?logo=firebase&logoColor=black)](https://firebase.google.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-111111)](https://openrouter.ai/)
[![Google Gemini](https://img.shields.io/badge/Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice-orange)](https://www.elevenlabs.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![GCP](https://img.shields.io/badge/Google%20Cloud-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?logo=vercel&logoColor=white)](https://vercel.com/)

---

## Why It Exists

Traditional learning is backwards. You read 200 pages sequentially, memorize isolated facts, and somehow expect to understand how everything connects. It's like trying to understand a city by walking down one street.

Your brain thinks in networks, not lines. When you truly understand something, you see how concept A influences concept B, which builds toward concept C. That's the difference between knowing facts and understanding systems.

BrainLattice flips this. Upload a textbook, get the entire landscape first. See connections, identify core concepts, dive deep into what matters. Perfect for course catchup, exam prep, or understanding complex subjects.

**Moral**: conceptual networks > "Unit 1, Unit 2, Lesson 3..." notes. Linear note-taking hides relationships; networks surface them so you learn faster and remember longer.

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

> [!WARNING] **⚠️ ElevenLabs Production Note:**  
> ElevenLabs Free Tier works for **localhost development only**. Cloud deployments (GCP, AWS, etc.) are blocked due to shared IP abuse prevention. For production audio generation, either:
>
> - Upgrade to [ElevenLabs Paid Plan](https://elevenlabs.io/pricing) ($5/month)
> - Switch to other TTS services

## Tech Stack

**Backend:**

- **FastAPI** - Python web framework
- **PyPDF** - PDF text extraction
- **OpenRouter (Grok 4 Fast)** - AI digest, cheatsheets, audio scripts
- **Google Gemini 2.5 Flash Lite** - Deep concept analysis, relationship mapping
- **Google Gemini 2.0 Flash Lite** - Overview of concepts when user Cmd+Shift+clicks on a node
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

## View more about BrainLattice 👇

[Devpost](https://devpost.com/software/brainlattice)

---

_Your brain thinks in networks. Your textbook should too._

_Studying with BrainLattice is just like navigating the earth on the atmosphere._
