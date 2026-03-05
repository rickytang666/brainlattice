<div align="center">

<a href="https://brainlattice.rickytang.dev"><img src="assets/logo.png" alt="BrainLattice Logo" width="250"></a>

<br>

**PDFs → Living Knowledge Networks**

![Obsidian Support](https://img.shields.io/badge/Obsidian-Support-101010?logo=obsidian&logoColor=7C3AED&labelColor=101010)

<!-- [![NPM Version](https://img.shields.io/npm/v/brainlattice?color=339933&logo=npm)](https://www.npmjs.com/package/brainlattice) -->

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

Before using you need to get your API keys from [Google AI](https://aistudio.google.com/), [OpenRouter](https://openrouter.ai/settings/keys), and optionally, [OpenAI](https://openai.com/index/openai-api-platform/).

### BrainLattice Web App

1. Open [BrainLattice web app](https://brainlattice.rickytang.dev).
2. Fill in your API keys by clicking the settings icon in the top navigation bar.
3. (Optional) You can sign up for an account to sync your projects across devices; otherwise it's local-only.
4. Upload a PDF.
5. Wait for the graph generation to complete.
6. Click on any node to view the LLM-generated notes.
7. If you want a Obsidian vault with full notes, click "export" to export the graph, and click "download" to download the prepared zip file. Then unzip the file and open it in Obsidian (File > Open Vault > Open Folder as Vault).

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

Optionally login (if you want projects to sync across devices).

```bash
login
```

Configure your vault & keys.

```bash
config
```

Generate a vault from a local pdf.

```bash
gen path/to/pdf
```

_For more details, see the [CLI Documentation](cli/README.md) or enter `help` in the interactive session._

## Architecture

![Architecture](assets/arch.svg)

## Local dev

_For full setup details, see the specific READMEs in `/frontend` and `/backend`._

### 1. Configure Keys

Create a `.env` in `backend/` with your API keys and DB URL (Neon PostgreSQL required for pgvector):

```bash
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
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

## Contributions

Please open an issue or submit a pull request!

## License

MIT
