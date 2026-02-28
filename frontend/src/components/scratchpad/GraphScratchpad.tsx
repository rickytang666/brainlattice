import { useState, useCallback, useRef } from 'react';
import KnowledgeGraph from '../graph/KnowledgeGraph';
import type { GraphData } from '../../types/graph';
import { AlertCircle, Code, Play, RefreshCw, Upload, FileJson, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function GraphScratchpad() {
  const [mode, setMode] = useState<'upload' | 'paste'>('upload');
  const [jsonInput, setJsonInput] = useState<string>('');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        const parsed = JSON.parse(content);
        if (!parsed.nodes || !Array.isArray(parsed.nodes)) {
          throw new Error('Invalid graph format: missing "nodes" array');
        }
        setGraphData(parsed);
        setError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        setGraphData(null);
      }
    };
    reader.readAsText(file);
  };

  const handleRender = useCallback(() => {
    try {
      const parsed = JSON.parse(jsonInput);
      
      // Basic validation
      if (!parsed.nodes || !Array.isArray(parsed.nodes)) {
        throw new Error('Invalid graph format: missing "nodes" array');
      }
      
      setGraphData(parsed);
      setError(null);
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Unknown error';
      setError(message);
      setGraphData(null);
    }
  }, [jsonInput]);

  const handleClear = () => {
    setJsonInput('');
    setGraphData(null);
    setError(null);
  };

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden pt-[60px]">
      {/* Sidebar: JSON Input */}
      <div className="w-1/3 flex flex-col border-r border-border bg-card">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link 
              to="/" 
              className="p-1 -ml-1 mr-1 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded transition-colors"
              title="Back to Landing Page"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <Code className="w-5 h-5 text-foreground" />
            <h2 className="font-semibold text-foreground text-base">JSON Scratchpad</h2>
          </div>
          <div className="flex gap-2 bg-muted rounded-lg p-1 border border-border">
            <button 
              onClick={() => setMode('upload')}
              className={`p-1.5 rounded transition-all ${mode === 'upload' ? 'bg-background text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
              title="Upload File"
            >
              <Upload className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setMode('paste')}
              className={`p-1.5 rounded transition-all ${mode === 'paste' ? 'bg-background text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
              title="Paste JSON"
            >
              <FileJson className="w-4 h-4" />
            </button>
            <div className="w-px bg-border mx-1" />
            <button 
              onClick={handleClear}
              className="p-1.5 hover:bg-destructive/20 hover:text-destructive rounded text-muted-foreground transition-colors"
              title="Clear"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 p-4 relative flex flex-col">
          {mode === 'upload' ? (
            <div className="flex-1 border-2 border-dashed border-border rounded-lg flex flex-col items-center justify-center p-8 hover:border-foreground/30 hover:bg-muted/50 transition-all group">
              <input 
                type="file" 
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".json"
                className="hidden" 
              />
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="flex flex-col items-center gap-4 w-full h-full justify-center"
              >
                <div className="p-4 bg-muted rounded-full group-hover:scale-110 transition-transform">
                  <Upload className="w-8 h-8 text-muted-foreground group-hover:text-foreground" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-foreground">Click to upload JSON</p>
                  <p className="text-xs text-muted-foreground mt-1">Supports any extracted graph file</p>
                </div>
              </button>
            </div>
          ) : (
            <textarea
              className="w-full h-full bg-background text-foreground font-mono text-xs p-4 rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground/50 resize-none border border-border"
              placeholder='Paste your graph JSON here...

Example:
{
  "nodes": [
    {"id": "A", "outbound_links": ["B"]},
    {"id": "B", "outbound_links": []}
  ]
}'
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
            />
          )}

          {error && (
            <div className="absolute bottom-6 left-6 right-6 p-3 bg-red-500/10 border border-red-500/50 rounded-md flex items-start gap-2 text-red-400 text-xs z-10">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {mode === 'paste' && (
          <div className="p-4 bg-background border-t border-border">
            <button
              onClick={handleRender}
              className="w-full bg-foreground hover:bg-foreground/80 text-background font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98]"
            >
              <Play className="w-4 h-4 fill-current" />
              VITALIZE GRAPH
            </button>
          </div>
        )}
      </div>

      {/* Main Area: Force Graph */}
      <div className="flex-1 relative">
        {graphData ? (
          <KnowledgeGraph data={graphData} />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-muted-foreground">
            <div className="mb-4 p-8 rounded-full border border-dashed border-border">
              <Code className="w-12 h-12 opacity-20" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Awaiting Influx of Knowledge</p>
          </div>
        )}
        
        {/* Overlay Info */}
        {graphData && (
          <div className="absolute bottom-6 right-6 flex items-center gap-4 text-xs font-medium text-muted-foreground bg-popover px-4 py-2 rounded-full border border-border shadow-sm">
            <span>{graphData.nodes.length} Concepts</span>
            <span className="w-1 h-1 bg-muted-foreground rounded-full" />
            <span>Interactive Node Focus Active</span>
          </div>
        )}
      </div>
    </div>
  );
}
