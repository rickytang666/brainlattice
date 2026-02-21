import { useState, useEffect, useMemo } from "react";

function decodeConceptId(id: string | null): string | null {
  if (!id) return null;
  try {
    return decodeURIComponent(id);
  } catch {
    return id;
  }
}
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Loader2, X, BookOpen, Hash, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import "katex/dist/katex.min.css";
import { API_BASE } from "../../config";

interface NoteSidebarProps {
  projectId: string;
  conceptId: string | null;
  aliases?: string[];
  validNodeIds?: Set<string>;
  onClose: () => void;
  onNodeSelect?: (id: string) => void;
}

export default function NoteSidebar({
  projectId,
  conceptId,
  aliases = [],
  validNodeIds,
  onClose,
  onNodeSelect,
}: NoteSidebarProps) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // process content to handle [[obsidian-links]] -> markdown links
  // use angle brackets <href> so concepts with spaces (e.g. "scalar field") parse correctly
  const processedContent = useMemo(() => {
    if (!content) return null;
    return content.replace(
      /\[\[([^\]]+)\]\]/g,
      (_, concept) => `[${concept}](<${concept}>)`,
    );
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

    const enc = encodeURIComponent(conceptId);
    const url = regenerate
      ? `${API_BASE}/project/${projectId}/node/${enc}/note?regenerate=true`
      : `${API_BASE}/project/${projectId}/node/${enc}/note`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error("failed to load note");
        return res.json();
      })
      .then((data) => {
        setContent(data.content);
        setLoading(false);
      })
      .catch((err) => {
        console.error(`[Interaction] fetch_note_failed: ${conceptId}`, err);
        setError("failed to generate note.");
        setLoading(false);
      });
  };

  useEffect(() => {
    if (!conceptId || !projectId) return;
    console.log(`[Interaction] fetch_note: ${conceptId}`);
    let ignore = false;

    fetch(
      `${API_BASE}/project/${projectId}/node/${encodeURIComponent(conceptId)}/note`,
    )
      .then((res) => {
        if (!res.ok) throw new Error("failed to load note");
        return res.json();
      })
      .then((data) => {
        if (!ignore) {
          console.log(`[Interaction] fetch_note_success: ${conceptId}`);
          setContent(data.content);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          console.error(`[Interaction] fetch_note_failed: ${conceptId}`, err);
          setError("failed to generate note.");
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [conceptId, projectId]);

  return (
    <div className="w-full min-w-0 border-l border-neutral-800 bg-[#0f0f0f] flex flex-col h-full shadow-2xl relative z-20 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-neutral-800 bg-[#141414] flex items-center justify-between">
        <div className="flex items-center gap-2 text-emerald-400">
          <BookOpen className="w-4 h-4 flex-shrink-0" />
          <h3 className="text-sm font-bold tracking-widest truncate max-w-[250px]">
            {decodeConceptId(conceptId) || "Note"}
          </h3>
        </div>
        <div className="flex items-center gap-1">
          {conceptId && (
            <button
              onClick={() => fetchNote(true)}
              disabled={loading}
              title="Regenerate note"
              className="p-1.5 text-neutral-500 hover:text-emerald-400 hover:bg-neutral-800 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1 text-neutral-500 hover:text-neutral-200 hover:bg-neutral-800 rounded transition-colors"
            title="Clear selection"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-neutral-800">
        {!conceptId ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <BookOpen className="w-10 h-10 text-neutral-700 mb-4" />
            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
              Select a node
            </p>
            <p className="text-[11px] text-neutral-600 leading-relaxed">
              Click a node in the graph or cmd+click a concept link to view and
              focus.
            </p>
          </div>
        ) : loading ? (
          <div className="h-full flex flex-col p-2 space-y-6">
            <div className="space-y-3">
              <motion.div
                initial={{ opacity: 0.3 }}
                animate={{ opacity: 1 }}
                transition={{
                  repeat: Infinity,
                  duration: 1.2,
                  repeatType: "reverse",
                }}
                className="h-6 bg-neutral-800/50 rounded w-3/4"
              />
              <motion.div
                initial={{ opacity: 0.3 }}
                animate={{ opacity: 1 }}
                transition={{
                  repeat: Infinity,
                  duration: 1.2,
                  delay: 0.2,
                  repeatType: "reverse",
                }}
                className="h-4 bg-neutral-800/30 rounded w-1/2"
              />
            </div>

            <div className="space-y-2 pt-4">
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0.2 }}
                  animate={{ opacity: 0.7 }}
                  transition={{
                    repeat: Infinity,
                    duration: 1.5,
                    delay: i * 0.1,
                    repeatType: "reverse",
                  }}
                  className="h-3 bg-neutral-800/40 rounded w-full"
                  style={{ width: `${100 - (i % 3) * 10}%` }}
                />
              ))}
            </div>

            <div className="space-y-2 pt-6">
              {[...Array(4)].map((_, i) => (
                <motion.div
                  key={`block2-${i}`}
                  initial={{ opacity: 0.2 }}
                  animate={{ opacity: 0.7 }}
                  transition={{
                    repeat: Infinity,
                    duration: 1.5,
                    delay: 0.5 + i * 0.1,
                    repeatType: "reverse",
                  }}
                  className="h-3 bg-neutral-800/40 rounded w-full"
                  style={{ width: `${95 - (i % 2) * 15}%` }}
                />
              ))}
            </div>

            <div className="flex-1 flex flex-col justify-end pb-8">
              <div className="flex items-center gap-2 text-emerald-500/60">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-[10px] uppercase tracking-[0.2em] font-medium">
                  synthesizing notes...
                </span>
              </div>
            </div>
          </div>
        ) : error ? (
          <div className="text-red-400 text-xs p-4 bg-red-400/5 border border-red-400/20 rounded-lg">
            {error}
          </div>
        ) : content ? (
          <div className="prose prose-invert prose-sm max-w-none">
            <div className="text-neutral-300 leading-relaxed text-sm">
              <ReactMarkdown
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold text-neutral-100 mt-6 mb-4">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-semibold text-neutral-200 mt-5 mb-3">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-medium text-neutral-300 mt-4 mb-2">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="mb-4 text-neutral-400 leading-relaxed">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-outside ml-4 mb-4 space-y-1.5 text-neutral-400">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-outside ml-4 mb-4 space-y-1.5 text-neutral-400">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => <li>{children}</li>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-2 border-emerald-500/50 pl-4 py-0.5 my-4 text-neutral-500 italic bg-emerald-500/5 rounded-r">
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto mb-4 border border-neutral-800 rounded-lg">
                      <table className="w-full text-sm text-left text-neutral-400">
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="px-4 py-2.5 bg-neutral-800/50 font-medium text-neutral-300 border-b border-neutral-800">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="px-4 py-2 border-b border-neutral-800/50 last:border-0">
                      {children}
                    </td>
                  ),
                  pre: ({ children }) => (
                    <pre className="bg-[#111] p-3 rounded-lg overflow-x-auto mb-4 border border-neutral-800/80">
                      {children}
                    </pre>
                  ),
                  code: ({ className, children }) => {
                    const isInline = !className;
                    return (
                      <code
                        className={`${isInline ? "bg-[#1a1a1a] px-1.5 py-0.5 rounded text-emerald-400 text-[11px] font-mono border border-neutral-800/50" : "text-emerald-400 text-[11px] font-mono"}`}
                      >
                        {children}
                      </code>
                    );
                  },
                  a: ({ href, children }) => {
                    const raw = (href || "").replace(/^<|>$/g, "").trim();
                    const targetId = decodeConceptId(raw) ?? raw;
                    const isLinked =
                      !validNodeIds || validNodeIds.has(targetId.toLowerCase());
                    if (!isLinked) {
                      return (
                        <span className="text-neutral-500">{children}</span>
                      );
                    }
                    return (
                      <button
                        onClick={() => onNodeSelect?.(targetId)}
                        className="text-emerald-400 hover:text-emerald-300 font-bold border-b border-emerald-500/30 hover:border-emerald-500 transition-all px-0.5"
                      >
                        {children}
                      </button>
                    );
                  },
                }}
              >
                {processedContent || ""}
              </ReactMarkdown>
            </div>

            {aliases.length > 0 && (
              <div className="mt-8 pt-6 border-t border-neutral-800">
                <div className="flex items-center gap-2 text-neutral-600 mb-3">
                  <Hash className="w-3 h-3" />
                  <span className="text-[10px] uppercase tracking-wider font-bold">
                    Aliases
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {aliases.map((a) => (
                    <span
                      key={a}
                      className="text-[11px] text-neutral-500 bg-neutral-800/80 px-2 py-0.5 rounded lowercase"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
