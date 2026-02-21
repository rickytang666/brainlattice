# brainlattice frontend

single-page app built with react, vite, and tailwind.

## how to run

```bash
npm install
npm run dev # local dev on :5173
```

## codebase structure

- `App.tsx`: main react root
- `Dashboard.tsx`: core layout bridging graph and sidebar
- `ForceGraph2D.tsx`: interaction wrapper for webgl canvas (hydrated from `/api/projects/{id}/graph`)
- `NoteSidebar.tsx`: sliding panel rendering ai synthesis for active nodes
- `UploadModal.tsx`: handles local pdf drops & backend progress polling
