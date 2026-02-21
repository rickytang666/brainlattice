import { useState, useMemo, useEffect, useRef } from "react";
import Fuse from "fuse.js";
import { Search, X } from "lucide-react";
import type { GraphData } from "../../types/graph";

interface SearchBarProps {
  data: GraphData | null;
  onSelectNode: (nodeId: string) => void;
}

export default function SearchBar({ data, onSelectNode }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // init Fuse.js with node data
  const fuse = useMemo(() => {
    if (!data?.nodes) return null;
    return new Fuse(data.nodes, {
      keys: ["id", "aliases"],
      threshold: 0.3, // fuzzy matching threshold
      distance: 100,
    });
  }, [data]);

  // perform search
  const results = useMemo(() => {
    if (!fuse || !query) return [];
    return fuse.search(query).slice(0, 8); // limit to top 8 results
  }, [fuse, query]);

  // handle outside click to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!data?.nodes || data.nodes.length === 0) return null;

  return (
    <div
      ref={wrapperRef}
      className="absolute top-6 right-8 w-72 z-10 font-mono"
    >
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-emerald-500/50" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-10 py-2 bg-black/60 border border-emerald-500/30 rounded-lg text-emerald-50 placeholder-emerald-500/50 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 backdrop-blur-sm transition-all"
          placeholder="Search graph..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            if (query) setIsOpen(true);
          }}
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              setIsOpen(false);
            }}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-emerald-500/50 hover:text-emerald-400"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* dropdown results */}
      {isOpen && query && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-black/90 border border-emerald-500/30 rounded-lg shadow-xl shadow-black overflow-hidden backdrop-blur-md max-h-96 overflow-y-auto">
          {results.map((result) => (
            <button
              key={result.item.id}
              onClick={() => {
                onSelectNode(result.item.id);
                setIsOpen(false);
                setQuery(result.item.id);
              }}
              className="w-full text-left px-4 py-3 border-b border-emerald-500/10 hover:bg-emerald-500/10 transition-colors last:border-0 flex flex-col gap-1"
            >
              <span className="text-emerald-50 font-bold text-sm truncate">
                {result.item.id}
              </span>
              {result.item.aliases && result.item.aliases.length > 0 && (
                <span className="text-emerald-500/60 text-[10px] truncate">
                  also: {result.item.aliases.join(", ")}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {isOpen && query && results.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-black/90 border border-red-500/30 rounded-lg p-4 text-center backdrop-blur-md">
          <span className="text-red-400 text-xs">no concepts found</span>
        </div>
      )}
    </div>
  );
}
