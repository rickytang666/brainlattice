# Frontend Setup Guide

## Environment Variables

Create a `.env.local` file in the frontend directory with:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Development

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Make sure your backend is running on `http://localhost:8000`

## Features Implemented

- ✅ PDF Upload with drag-and-drop
- ✅ Progress tracking during processing
- ✅ Interactive Knowledge Graph visualization (React Flow)
- ✅ Study Guide Overview generation
- ✅ Audio Study Material generation
- ✅ Download functionality for study materials
- ✅ Responsive design with dark/light theme
- ✅ Error handling and loading states

## Components

- `PDFUpload`: Handles file upload and processing pipeline
- `KnowledgeGraph`: Interactive graph visualization using React Flow
- `ProjectView`: Complete project view with all study materials
- `api.ts`: API service functions for backend communication

## Tech Stack

- Next.js 14 (App Router)
- React Flow for graph visualization
- TailwindCSS for styling
- TypeScript for type safety
- Tabler Icons for UI icons
