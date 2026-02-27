import { useState, useEffect } from "react";
import { X, Key } from "lucide-react";
import { GEMINI_KEY_STORAGE, OPENAI_KEY_STORAGE } from "../../config";

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ConfigModal({ isOpen, onClose }: ConfigModalProps) {
  const [apiKey, setApiKey] = useState("");
  const [openAiKey, setOpenAiKey] = useState("");

  useEffect(() => {
    if (isOpen) {
      // defer state update to avoid synchronous cascading renders during mount
      setTimeout(() => {
        setApiKey(localStorage.getItem(GEMINI_KEY_STORAGE) || "");
        setOpenAiKey(localStorage.getItem(OPENAI_KEY_STORAGE) || "");
      }, 0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem(GEMINI_KEY_STORAGE, apiKey.trim());
    localStorage.setItem(OPENAI_KEY_STORAGE, openAiKey.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-xl w-full max-w-md shadow-2xl shadow-black/20 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2 text-primary">
            <Key className="w-4 h-4" />
            <h3 className="font-semibold text-base">API Configuration</h3>
          </div>
          <button onClick={onClose} className="p-1 text-muted-foreground hover:text-destructive transition-colors rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-6">
          <label className="flex items-center justify-between text-sm font-medium text-foreground mb-2">
            <span>Google Gemini API Key</span>
            <span className="text-xs text-muted-foreground">Required</span>
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="AIzaSy..."
            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary transition-colors mb-4 font-mono"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") onClose();
            }}
          />

          <label className="flex items-center justify-between text-sm font-medium text-foreground mb-2 mt-2">
            <span>OpenAI API Key</span>
            <span className="text-xs text-muted-foreground">Optional</span>
          </label>
          <input
            type="password"
            value={openAiKey}
            onChange={(e) => setOpenAiKey(e.target.value)}
            placeholder="sk-proj-..."
            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary transition-colors mb-4 font-mono"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") onClose();
            }}
          />
          <p className="text-xs text-muted-foreground mb-6 leading-relaxed">
            Your API keys are stored locally in your browser and are only sent to the server for document ingestion. The OpenAI key is optionally used for higher-quality embeddings. <span className="text-amber-500/80 font-medium tracking-wide">Clearing your browser cache will remove these keys and your anonymous project history.</span>
          </p>
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-primary hover:bg-primary/80 text-primary-foreground rounded-lg text-sm font-bold transition-colors shadow-lg shadow-primary/20"
            >
              Save Key
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
