<div align="center">

<img src="assets/logo.png" alt="BrainLattice Logo" width="250">

<br>

**PDFs → Living Knowledge Networks**

![Obsidian Support](https://img.shields.io/badge/Obsidian-Support-101010?logo=obsidian&logoColor=7C3AED&labelColor=101010)

**BrainLattice** is an AI-powered extraction engine that turns dense PDFs (textbooks, research papers, course notes) into interactive, explorable WebGL knowledge networks.

</div>

---

## The Problem

Human knowledge is a high-dimensional network, but PDFs are linear streams of characters. When you read a 200-page textbook, you lose the "map" of how concepts actually connect. Mentally mapping these relationships is the hardest part of learning.

## The Solution

BrainLattice automates the learning process. It parses the document, discovers the core conceptual nodes, and plots their relationships on an interactive canvas.

- **Graph-First Synthesis**: Automatically identifies entities, theorems, and definitions using LLM-driven entity extraction.
- **Deep Contextual Retrieval**: Click any node to instantly pull up an AI-synthesized summary sourced directly from the original text chunks.
- **Native Obsidian Export**: One-click export to a full Obsidian Vault. Includes all markdown notes and a pre-configured Canvas file.
- **High-Performance WebGL**: Real-time force-directed graphs that stay snappy even with thousands of conceptual links.

## Tech Stack

- **Frontend**: React + Vite + Force Graph (WebGL)
- **Backend**: FastAPI
- **Database**: Neon PostgreSQL
- **Infra**: AWS Lambda, Cloudflare R2, Upstash Redis, Upstash QStash

## Quick Start

_For full setup details, see the specific READMEs in `/frontend` and `/backend`._

### 1. Configure Keys

Create a `.env` in `backend/` with your Gemini API key and DB URL (either local SQLite or Neon PostgreSQL):

```bash
GEMINI_API_KEY=your_key_here
DATABASE_URL=your_db_url_here
```

### 2. Start Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be live at `http://localhost:5173`.

## More Info on Local Development/Self-Hosting

Consult the `README.md` files inside the `frontend/` and `backend/` folders for detailed instructions.
