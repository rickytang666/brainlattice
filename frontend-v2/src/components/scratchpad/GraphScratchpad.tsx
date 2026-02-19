import { useState, useCallback, useRef } from 'react';
import KnowledgeGraph from '../graph/KnowledgeGraph';
import type { GraphData } from '../../types/graph';
import { AlertCircle, Code, Play, RefreshCw, Upload, FileJson } from 'lucide-react';

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
    <div className="flex h-screen w-full bg-[#0a0a0a] overflow-hidden">
      {/* Sidebar: JSON Input */}
      <div className="w-1/3 flex flex-col border-r border-neutral-800 bg-[#0f0f0f]">
        <div className="p-4 border-b border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Code className="w-5 h-5 text-blue-500" />
            <h2 className="font-bold text-neutral-200 uppercase tracking-tighter">JSON Scratchpad</h2>
          </div>
          <div className="flex gap-2 bg-neutral-900 rounded-lg p-1 border border-neutral-800">
            <button 
              onClick={() => setMode('upload')}
              className={`p-1.5 rounded transition-all ${mode === 'upload' ? 'bg-neutral-800 text-blue-400 shadow-sm' : 'text-neutral-500 hover:text-neutral-300'}`}
              title="Upload File"
            >
              <Upload className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setMode('paste')}
              className={`p-1.5 rounded transition-all ${mode === 'paste' ? 'bg-neutral-800 text-blue-400 shadow-sm' : 'text-neutral-500 hover:text-neutral-300'}`}
              title="Paste JSON"
            >
              <FileJson className="w-4 h-4" />
            </button>
            <div className="w-px bg-neutral-800 mx-1" />
            <button 
              onClick={handleClear}
              className="p-1.5 hover:bg-red-900/20 hover:text-red-400 rounded text-neutral-500 transition-colors"
              title="Clear"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 p-4 relative flex flex-col">
          {mode === 'upload' ? (
            <div className="flex-1 border-2 border-dashed border-neutral-800 rounded-lg flex flex-col items-center justify-center p-8 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all group">
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
                <div className="p-4 bg-neutral-900 rounded-full group-hover:scale-110 transition-transform">
                  <Upload className="w-8 h-8 text-neutral-500 group-hover:text-blue-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-neutral-300">Click to upload JSON</p>
                  <p className="text-xs text-neutral-500 mt-1">Supports any extracted graph file</p>
                </div>
              </button>
            </div>
          ) : (
            <textarea
              className="w-full h-full bg-[#141414] text-emerald-400 font-mono text-xs p-4 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500/50 resize-none border border-neutral-800"
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
          <div className="p-4 bg-[#0a0a0a] border-t border-neutral-800">
            <button
              onClick={handleRender}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-900/20 active:scale-[0.98]"
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
          <div className="w-full h-full flex flex-col items-center justify-center text-neutral-600">
            <div className="mb-4 p-8 rounded-full border border-dashed border-neutral-800">
              <Code className="w-12 h-12 opacity-20" />
            </div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] opacity-40">Awaiting Influx of Knowledge</p>
          </div>
        )}
        
        {/* Overlay Info */}
        {graphData && (
          <div className="absolute bottom-6 right-6 flex items-center gap-4 text-[10px] text-neutral-500 uppercase tracking-widest bg-black/50 backdrop-blur-md px-4 py-2 rounded-full border border-neutral-800">
            <span>{graphData.nodes.length} Concepts</span>
            <span className="w-1 h-1 bg-neutral-700 rounded-full" />
            <span>Interactive Node Focus Active</span>
          </div>
        )}
      </div>
    </div>
  );
}
