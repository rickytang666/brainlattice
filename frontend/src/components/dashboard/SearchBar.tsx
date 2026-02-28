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
  const [selectedIndex, setSelectedIndex] = useState(-1);
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
      className="relative w-64 font-mono ml-2 mt-0.5"
    >
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-muted-foreground" />
        </div>
        <input
          type="text"
          className="block w-full pl-9 pr-9 py-1.5 bg-card border border-border/50 shadow-sm rounded-full text-xs text-foreground placeholder-muted-foreground focus:outline-none focus:border-foreground focus:ring-1 focus:ring-foreground transition-all"
          placeholder="search graph..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            setSelectedIndex(-1);
          }}
          onFocus={() => {
            if (query) setIsOpen(true);
          }}
          onKeyDown={(e) => {
            if (!isOpen || results.length === 0) return;
            
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setSelectedIndex((prev) => Math.max(prev - 1, -1));
            } else if (e.key === "Enter") {
              e.preventDefault();
              if (selectedIndex >= 0 && selectedIndex < results.length) {
                const selected = results[selectedIndex];
                onSelectNode(selected.item.id);
                setIsOpen(false);
                setQuery(selected.item.id);
              } else if (results.length > 0) {
                // Default to first if none explicitly selected
                const first = results[0];
                onSelectNode(first.item.id);
                setIsOpen(false);
                setQuery(first.item.id);
              }
            } else if (e.key === "Escape") {
              setIsOpen(false);
            }
          }}
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              setIsOpen(false);
            }}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* dropdown results */}
      {isOpen && query && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-popover border border-border rounded-lg shadow-sm overflow-hidden max-h-96 overflow-y-auto">
          {results.map((result, index) => (
            <button
              key={result.item.id}
              onClick={() => {
                onSelectNode(result.item.id);
                setIsOpen(false);
                setQuery(result.item.id);
              }}
              onMouseEnter={() => setSelectedIndex(index)}
              className={`w-full text-left px-4 py-3 border-b border-border/50 transition-colors last:border-0 flex flex-col gap-1 ${
                selectedIndex === index ? "bg-muted" : "hover:bg-muted/50"
              }`}
            >
              <span className="text-foreground font-bold text-sm truncate">
                {result.item.id}
              </span>
              {result.item.aliases && result.item.aliases.length > 0 && (
                <span className="text-muted-foreground text-[10px] truncate">
                  aka: {result.item.aliases.join(", ")}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {isOpen && query && results.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-popover border border-destructive/30 rounded-lg p-4 text-center shadow-sm">
          <span className="text-destructive text-xs">no concepts found</span>
        </div>
      )}
    </div>
  );
}
