import { useState, useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Loader2, X, BookOpen, ExternalLink, Hash, RefreshCw } from 'lucide-react';
import 'katex/dist/katex.min.css';
import { API_BASE } from '../../config';

interface NoteSidebarProps {
  projectId: string;
  conceptId: string | null;
  onClose: () => void;
  onNodeSelect?: (id: string) => void;
}

export default function NoteSidebar({ projectId, conceptId, onClose, onNodeSelect }: NoteSidebarProps) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // process content to handle [[obsidian-links]]
  const processedContent = useMemo(() => {
    if (!content) return null;
    // replace [[concept]] with [concept](concept) to make it clickable via markdown components
    // we use a special prefix or just use the link component override
    return content.replace(/\[\[(.*?)\]\]/g, '[$1]($1)');
  }, [content]);

  // sync state with props during render to avoid cascading effect renders
  const [prevProps, setPrevProps] = useState({ projectId, conceptId });
  if (prevProps.conceptId !== conceptId || prevProps.projectId !== projectId) {
    setPrevProps({ projectId, conceptId });
    setContent(null);
    setError(null);
    setLoading(!!conceptId && !!projectId);
  }

  const fetchNote = (regenerate = false) => {
    if (!conceptId || !projectId) return;
    setError(null);
    setLoading(true);

    const url = regenerate
      ? `${API_BASE}/project/${projectId}/node/${conceptId}/note?regenerate=true`
      : `${API_BASE}/project/${projectId}/node/${conceptId}/note`;

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error('failed to load note');
        return res.json();
      })
      .then(data => {
        setContent(data.content);
        setLoading(false);
      })
      .catch(err => {
        console.error(`[Interaction] fetch_note_failed: ${conceptId}`, err);
        setError('failed to generate note.');
        setLoading(false);
      });
  };

  useEffect(() => {
    if (!conceptId || !projectId) return;
    console.log(`[Interaction] fetch_note: ${conceptId}`);
    let ignore = false;

    setError(null);
    setLoading(true);

    fetch(`${API_BASE}/project/${projectId}/node/${conceptId}/note`)
      .then(res => {
        if (!res.ok) throw new Error('failed to load note');
        return res.json();
      })
      .then(data => {
        if (!ignore) {
          console.log(`[Interaction] fetch_note_success: ${conceptId}`);
          setContent(data.content);
          setLoading(false);
        }
      })
      .catch(err => {
        if (!ignore) {
          console.error(`[Interaction] fetch_note_failed: ${conceptId}`, err);
          setError('failed to generate note.');
          setLoading(false);
        }
      });

    return () => { ignore = true; };
  }, [conceptId, projectId]);

  if (!conceptId) return null;

  return (
    <div className="w-80 border-l border-neutral-800 bg-[#0f0f0f] flex flex-col h-full shadow-2xl relative z-20 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-neutral-800 bg-[#141414] flex items-center justify-between">
        <div className="flex items-center gap-2 text-emerald-400">
          <BookOpen className="w-4 h-4" />
          <h3 className="text-xs font-bold uppercase tracking-widest truncate max-w-[140px]">
            {conceptId}
          </h3>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => fetchNote(true)}
            disabled={loading}
            title="Regenerate note"
            className="p-1.5 text-neutral-500 hover:text-emerald-400 hover:bg-neutral-800 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button 
            onClick={onClose}
            className="p-1 text-neutral-500 hover:text-neutral-200 hover:bg-neutral-800 rounded transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-neutral-800">
        {loading ? (
          <div className="h-full flex flex-col items-center justify-center space-y-4">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-500/40" />
            <p className="text-[10px] text-neutral-500 uppercase tracking-[0.2em] animate-pulse">
              generating study note...
            </p>
          </div>
        ) : error ? (
          <div className="text-red-400 text-xs p-4 bg-red-400/5 border border-red-400/20 rounded-lg">
            {error}
          </div>
        ) : content ? (
          <div className="prose prose-invert prose-sm max-w-none">
            <div className="text-neutral-400 leading-relaxed text-sm lowercase">
              <ReactMarkdown 
                remarkPlugins={[remarkMath]} 
                rehypePlugins={[rehypeKatex]}
                components={{
                  p: ({ children }) => <p className="mb-4">{children}</p>,
                  code: ({ children }) => (
                    <code className="bg-neutral-800 px-1 py-0.5 rounded text-emerald-400 text-xs">
                      {children}
                    </code>
                  ),
                  a: ({ href, children }) => (
                    <button 
                      onClick={(e) => {
                          const isQuickFocus = e.metaKey || e.ctrlKey;
                          console.log(`[Interaction] backlink_click: target=${href}, quickFocus=${isQuickFocus}`);
                          onNodeSelect?.(href || '');
                      }}
                      className="text-emerald-400 hover:text-emerald-300 font-bold border-b border-emerald-500/30 hover:border-emerald-500 transition-all px-0.5"
                    >
                      {children}
                    </button>
                  )
                }}
              >
                {processedContent || ''}
              </ReactMarkdown>
            </div>
            
            <div className="mt-8 pt-6 border-t border-neutral-800">
                <div className="flex items-center gap-2 text-neutral-600 mb-3">
                    <Hash className="w-3 h-3" />
                    <span className="text-[10px] uppercase tracking-wider font-bold">Metadata</span>
                </div>
                <div className="bg-[#141414] p-3 rounded-lg border border-neutral-800/50">
                    <p className="text-[10px] text-neutral-500 mb-1">Concept ID</p>
                    <code className="text-[11px] text-neutral-400 break-all">{conceptId}</code>
                </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Footer */}
      <div className="p-4 bg-[#0a0a0a] border-t border-neutral-800/50">
        <button className="w-full flex items-center justify-center gap-2 text-[10px] uppercase tracking-[0.15em] font-bold py-2 text-neutral-500 border border-neutral-800 rounded hover:border-neutral-700 hover:text-neutral-300 transition-all">
          <ExternalLink className="w-3 h-3" />
          More Details
        </button>
      </div>
    </div>
  );
}
