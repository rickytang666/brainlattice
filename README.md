# 🧠 BrainLattice

_Upload 200-page PDFs → Get Knowledge Graphs + AI Study Guide_

Transform massive course PDFs into interactive concept graphs with AI-powered study materials. Perfect for students who want to understand the big picture and see how concepts connect.

## ✨ Features

- **PDF Upload**: Drag-and-drop PDF upload with progress tracking
- **AI Processing**: Multi-model AI pipeline for text extraction and analysis
- **Interactive Knowledge Graph**: Visualize concept relationships using React Flow
- **Study Materials**: Generate overviews, audio scripts, and downloadable study guides
- **Responsive Design**: Works on desktop and mobile with dark/light theme support

## 🚀 Quick Start

### Backend Setup

1. Navigate to backend directory:

```bash
cd backend
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:

```bash
# AI Service API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=secrets/firebase_private.json
```

4. Start the backend server:

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Create `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

4. Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 🏗️ Architecture

### Backend (Python FastAPI)

- **PDF Processing**: PyPDF2 for text extraction
- **AI Pipeline**: Multi-model approach using OpenRouter (Grok 4 Fast) and Gemini 2.5 Flash Lite
- **Database**: Firebase Firestore for project storage
- **API**: RESTful endpoints for all operations

### Frontend (Next.js 14)

- **Upload**: Drag-and-drop PDF upload with progress tracking
- **Visualization**: React Flow for interactive knowledge graphs
- **Study Materials**: Overview generation and audio script creation
- **UI**: TailwindCSS with dark/light theme support

## 📊 AI Processing Pipeline

1. **PDF → Text**: Extract raw text using PyPDF2
2. **Text → AI Digest**: OpenRouter (Grok 4 Fast) creates structured concept outline
3. **Digest → Knowledge Graph**: Gemini 2.5 Flash Lite generates relationships and hierarchy
4. **Graph → Study Materials**: OpenRouter generates overviews and audio scripts
5. **Script → Audio**: ElevenLabs converts scripts to audio files

## 🎯 API Endpoints

- `POST /api/extract` - Extract text from PDF
- `POST /api/digest` - Create AI digest from text
- `POST /api/relationships` - Generate knowledge graph
- `POST /api/overview` - Generate study guide overview
- `POST /api/audio-script` - Generate audio script
- `POST /api/audio` - Generate audio from script
- `POST /api/project/save` - Save project to database
- `GET /api/project/{id}` - Retrieve project data

## 🛠️ Tech Stack

### Backend

- **FastAPI**: Modern Python web framework
- **PyPDF2**: PDF text extraction
- **Google Gemini**: AI model for relationship mapping
- **OpenRouter**: AI model for text processing
- **ElevenLabs**: Text-to-speech for audio generation
- **Firebase Firestore**: NoSQL database

### Frontend

- **Next.js 14**: React framework with App Router
- **React Flow**: Interactive graph visualization
- **TailwindCSS**: Utility-first CSS framework
- **TypeScript**: Type-safe JavaScript
- **Tabler Icons**: Icon library

## 📁 Project Structure

```
brainlattice/
├── backend/                     # Python FastAPI
│   ├── main.py                 # FastAPI application
│   ├── routers/                # API endpoints
│   ├── services/               # Business logic
│   ├── models/                 # Pydantic schemas
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Next.js App
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   ├── components/        # React components
│   │   └── lib/              # Utilities and API
│   └── package.json           # Node dependencies
└── README.md                  # This file
```

## 🎨 UI Components

- **PDFUpload**: Drag-and-drop file upload with progress tracking
- **KnowledgeGraph**: Interactive graph visualization with React Flow
- **ProjectView**: Complete project view with all study materials
- **ProjectList**: List of all user projects (future enhancement)

## 🔧 Development

### Backend Development

```bash
cd backend
python main.py  # Start development server
```

### Frontend Development

```bash
cd frontend
npm run dev     # Start development server
```

### Testing

Upload a PDF file through the frontend interface and watch the processing pipeline in action!

## 🚀 Deployment

### Backend (Vercel Serverless)

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `vercel --prod`

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Automatic deployment on push to main branch

## 📝 Environment Variables

### Backend (.env)

```bash
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
FIREBASE_SERVICE_ACCOUNT_PATH=secrets/firebase_private.json
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **OpenRouter** for fast, free AI text processing
- **Google Gemini** for relationship mapping
- **ElevenLabs** for high-quality text-to-speech
- **React Flow** for interactive graph visualization
- **Firebase** for scalable database storage

---

**BrainLattice** - See your entire course as an interactive graph. Know what to learn first.
