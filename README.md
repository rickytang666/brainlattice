<div align="center">

<a href="https://brainlattice.rickytang.dev"><img src="assets/logo.png" alt="BrainLattice Logo" width="250"></a>

<br>

**PDFs → Living Knowledge Networks**

![Obsidian Support](https://img.shields.io/badge/Obsidian-Support-101010?logo=obsidian&logoColor=7C3AED&labelColor=101010)

**BrainLattice** is an AI-powered extraction engine that turns dense PDFs (textbooks, research papers, course notes) into interactive, explorable WebGL knowledge networks.

</div>

---

## The Problem

Human knowledge is a high-dimensional network, but PDFs are linear streams of characters. When you read a 200-page textbook, you lose the "map" of how concepts actually connect. Mentally mapping these relationships is the hardest part of learning.

## The Solution

BrainLattice turns linear documents into high-dimensional knowledge networks. It automatically parses PDFs, discovers core conceptual nodes, and plots their relationships on an interactive canvas.

- **Graph-First Synthesis**: Extracts theorems, definitions, and entities into interactive WebGL networks.
- **Contextual Synthesis**: Click any node to instantly pull up AI-summarized context from original source chunks.
- **Native Obsidian Export**: Generates a full Obsidian Vault complete with markdown notes and Canvas maps.
- **Semantic Intelligence**: Understands "ancestors" (dependencies) and "descendants" (what depends on it) for every concept.
- **Infinite Zoom**: Move from a 50,000-ft textbook overview to a specific theorem in seconds.
- **CLI Workflow**: Full-featured CLI for local vault generations.

## Tech Stack

- **Frontend**: React + Vite + Force Graph (WebGL)
- **Backend**: FastAPI
- **Database**: Neon PostgreSQL
- **Infra**: AWS Lambda, Cloudflare R2, Upstash Redis, Upstash QStash
- **CLI**: Node.js (Commander.js)

## How to use

### BrainLattice Web App

1. Open [BrainLattice web app](https://brainlattice.rickytang.dev).
2. Upload a PDF.
3. Wait for the graph generation to complete.
4. Click on any node to view the AI-generated notes.
5. If you want a Obsidian vault with full notes, click "export" to export the graph, and click "download" to download the prepared zip file.

### BrainLattice CLI

#### Installation

```bash
npm i -g brainlattice
```

#### Start

This will open an interactive session.

```bash
brainlattice
```

#### Core Usage

```bash
# optionally login (if you want projects to sync across devices)
login

# configure your vault & keys
config

# generate a vault from a local pdf
gen path/to/pdf
```

_For more details, see the [CLI Documentation](cli/README.md)._

## Pro-Tips

- **Large Documents**: For dense textbooks (>100MB), the extraction works best if you process it in sections or ensure you have high LLM rate limits.
- **Math Support**: BrainLattice has native KaTeX support in the scratchpad and exports clean LaTeX to Obsidian.
- **Knowledge Caching**: Your previous extractions are cached in your account; use the CLI `export` command to pull them down to new machines instantly.
- **Dark Mode**: The WebGL graph is optimized for high-contrast viewing. Toggle the sun/moon icon for a premium night-mode experience.

## Local dev

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
