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
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import { IconLoader2, IconX, IconBook, IconHash, IconRefresh } from "@tabler/icons-react";
import { useSafeAuth } from "../../hooks/useSafeAuth";
import "katex/dist/katex.min.css";
import { API_BASE, apiFetch } from "../../config";

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
  const { userId } = useSafeAuth();
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // process content to handle [[obsidian-links]] -> markdown links
  // use angle brackets <href> so concepts with spaces (e.g. "scalar field") parse correctly
  const processedContent = useMemo(() => {
    if (!content) return null;
    let md = content.replace(
      /\[\[([^\]]+)\]\]/g,
      (_, concept) => `[${concept}](<${concept}>)`,
    );

    // Normalize block math: ensure $$ starts on its own line and has padding
    // Use a function as replacement to avoid the JS '$$' string literal trap
    md = md.replace(/\s*\$\$\s*/g, () => "\n\n$$\n\n");
    // Also collapse unnecessary multiple newlines created by the above
    md = md.replace(/\n{3,}/g, "\n\n");

    return md;
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

    apiFetch(url, undefined, userId)
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

    apiFetch(
      `${API_BASE}/project/${projectId}/node/${encodeURIComponent(conceptId)}/note`,
      undefined,
      userId
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
  }, [conceptId, projectId, userId]);

  return (
    <div className="w-full min-w-0 border-l border-border bg-background flex flex-col h-full relative z-20 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card flex items-center justify-between">
        <div className="flex items-center gap-2 text-foreground">
          <IconBook className="w-4 h-4 flex-shrink-0" />
          <h3 className="text-sm font-bold truncate max-w-[300px]">
            {decodeConceptId(conceptId) || "note"}
          </h3>
        </div>
        <div className="flex items-center gap-1">
          {conceptId && (
            <button
              onClick={() => fetchNote(true)}
              disabled={loading}
              title="Regenerate note"
              className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <IconRefresh
                className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
            title="Clear selection"
          >
            <IconX className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-muted">
        {!conceptId ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <p className="text-sm font-medium text-foreground mb-1">
              select a concept
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              click a node in the graph to view its note.
            </p>
          </div>
        ) : loading ? (
          <div className="h-full flex flex-col p-6 space-y-4 animate-pulse">
            <div className="h-5 bg-muted/50 rounded w-1/3 mb-4" />
            <div className="h-3 bg-muted/40 rounded w-full" />
            <div className="h-3 bg-muted/30 rounded w-[95%]" />
            <div className="h-3 bg-muted/30 rounded w-[90%]" />
            <div className="h-3 bg-muted/30 rounded w-[85%]" />
            <div className="h-3 bg-muted/40 rounded w-full mt-6" />
            <div className="h-3 bg-muted/30 rounded w-[95%]" />
            <div className="h-3 bg-muted/30 rounded w-[80%]" />
            
            <div className="flex-1 flex flex-col justify-end pb-8">
              <div className="flex items-center gap-2 text-muted-foreground">
                <IconLoader2 className="w-4 h-4 animate-spin" />
                <span className="text-xs font-medium">
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
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <div className="text-foreground leading-relaxed text-sm">
              <ReactMarkdown
                remarkPlugins={[remarkMath, remarkGfm]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold text-foreground mt-6 mb-4">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-semibold text-foreground mt-5 mb-3">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-medium text-foreground mt-4 mb-2">
                      {children}
                    </h3>
                  ),
                  // Removed 'p' component to allow rehype-katex display blocks to render correctly without nesting issues
                  ul: ({ children }) => (
                    <ul className="list-disc list-outside ml-4 mb-4 space-y-1.5">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-outside ml-4 mb-4 space-y-1.5">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => <li>{children}</li>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-2 border-muted-foreground/30 pl-4 py-0.5 my-4 italic bg-muted/30 rounded-r">
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto mb-6 border border-border rounded-lg bg-card">
                      <table className="w-full text-[13px] text-left text-muted-foreground border-collapse">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-muted">
                      {children}
                    </thead>
                  ),
                  th: ({ children }) => (
                    <th className="px-4 py-3 font-semibold text-muted-foreground border-b border-border text-xs">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="px-4 py-2.5 border-b border-border/50 last:border-0">
                      {children}
                    </td>
                  ),
                  pre: ({ children }) => (
                    <pre className="bg-muted p-3 rounded-lg overflow-x-auto mb-4 border border-border/80">
                      {children}
                    </pre>
                  ),
                  code: ({ className, children }) => {
                    const isInline = !className;
                    return (
                      <code
                        className={`${isInline ? "bg-muted px-1.5 py-0.5 rounded text-foreground text-xs font-mono border border-border/50" : "text-foreground text-xs font-mono"}`}
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
                        <span className="text-muted-foreground">{children}</span>
                      );
                    }
                    return (
                      <button
                        onClick={() => onNodeSelect?.(targetId)}
                        className="text-foreground hover:text-primary font-bold border-b border-foreground/60 hover:border-primary transition-all px-0.5"
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
              <div className="mt-8 pt-6 border-t border-border">
                <div className="flex items-center gap-2 text-muted-foreground mb-3">
                  <IconHash className="w-3 h-3" />
                  <span className="text-xs font-medium">
                    aliases
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {aliases.map((a) => (
                    <span
                      key={a}
                      className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <style>{`
              .katex-display {
                margin: 1.5em 0 !important;
                display: block;
                text-align: center;
              }
              .katex {
                font-size: 1.1em;
              }
              .prose {
                line-height: 1.7;
              }
              .prose p {
                margin-bottom: 1.25em;
              }
              .prose li {
                margin-bottom: 0.25em;
              }
              .prose hr {
                border-color: var(--border);
                margin: 2em 0;
                opacity: 0.5;
              }
            `}</style>
          </div>
        ) : null}
      </div>
    </div>
  );
}
