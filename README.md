<div align="center">

<img src="assets/logo.png" alt="BrainLattice Logo" width="250">

_Turn any PDF into an interactive conceptual network._

**BrainLattice** is an AI-powered extraction engine that reads entire textbooks or research papers and reconstructs them as an explorable WebGL knowledge graph. Stop reading linearly. Start exploring spatially.

</div>

---

## What it does

Knowledge isn't linear, but books are. **BrainLattice** breaks this limitation by parsing dense documents and using LLM to automatically discover core concepts, map their relationships, and plot them on an interactive 2D canvas. You get the 10,000-foot view of a subject instantly, with the ability to dive deep on command.

## Core Features

- **Spatial Discovery**: Navigate complex subjects visually. See how concepts, formulas, and theorems connect before you even start reading.
- **Instant Context**: Click any node on the graph to instantly pull up an AI-synthesized summary of that specific entity, sourced directly from the original text.
- **Universal Ingestion**: Feed it 200-page textbooks, messy lecture notes, or dense research papers.
- **Effortless Synthesis**: Skip the tedious note-taking. BrainLattice distills hours of reading into an explorable, high-yield conceptual network so you can focus entirely on understanding.

## Tech Stack

- **Frontend**: React + Vite + Force Graph (WebGL)
- **Backend**: FastAPI
- **Database**: Neon PostgreSQL
- **Infra**: AWS Lambda, Cloudflare R2, Upstash Redis, Upstash QStash

## Quick Run

_For full technical details, see the `README.md` files inside the `frontend/` and `backend/` folders._

1. **Clone the repo**
2. **Configure Backend API Key**
   Create a `.env` in the `backend/` directory with just your Gemini key.

   Only `GEMINI_API_KEY` is mandatory for the app (`OPEN_AI_API_KEY` is optional, but better for embedding).

   ```bash
   GEMINI_API_KEY=your_key_here
   ```

3. **Start Backend**

   ```bash
   cd backend && uv sync && uv run uvicorn main:app
   ```

4. **Start Frontend**

   ```bash
   cd frontend && npm install && npm run dev
   ```

The frontend will be available at `http://localhost:5173`.

## Local Development/Self-Hosting

Consult the `README.md` files inside the `frontend/` and `backend/` folders for detailed instructions.
