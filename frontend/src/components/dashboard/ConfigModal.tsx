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
      setApiKey(localStorage.getItem(GEMINI_KEY_STORAGE) || "");
      setOpenAiKey(localStorage.getItem(OPENAI_KEY_STORAGE) || "");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem(GEMINI_KEY_STORAGE, apiKey.trim());
    localStorage.setItem(OPENAI_KEY_STORAGE, openAiKey.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-[#141414] border border-neutral-800 rounded-xl w-full max-w-md shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-neutral-800">
          <div className="flex items-center gap-2 text-emerald-400">
            <Key className="w-4 h-4" />
            <h3 className="font-bold tracking-widest uppercase text-sm">API Configuration</h3>
          </div>
          <button onClick={onClose} className="p-1 text-neutral-500 hover:text-red-400 transition-colors rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-6">
          <label className="flex items-center justify-between text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
            <span>Google Gemini API Key</span>
            <span className="text-[10px] text-emerald-500/80 bg-emerald-500/10 px-1.5 py-0.5 rounded">Required</span>
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="AIzaSy..."
            className="w-full bg-[#0a0a0a] border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-200 focus:outline-none focus:border-emerald-500 transition-colors mb-4 font-mono"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") onClose();
            }}
          />

          <label className="flex items-center justify-between text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2 mt-2">
            <span>OpenAI API Key</span>
            <span className="text-[10px] text-neutral-500 bg-neutral-800 px-1.5 py-0.5 rounded">Optional</span>
          </label>
          <input
            type="password"
            value={openAiKey}
            onChange={(e) => setOpenAiKey(e.target.value)}
            placeholder="sk-proj-..."
            className="w-full bg-[#0a0a0a] border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-200 focus:outline-none focus:border-emerald-500 transition-colors mb-4 font-mono"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") onClose();
            }}
          />
          <p className="text-xs text-neutral-500 mb-6 leading-relaxed">
            Your API keys are stored locally in your browser and are only sent to the server for document ingestion. The OpenAI key is optionally used for higher-quality embeddings. <span className="text-amber-500/80 font-medium tracking-wide">Clearing your browser cache will remove these keys and your anonymous project history.</span>
          </p>
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-neutral-400 hover:text-neutral-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-bold transition-colors shadow-lg shadow-emerald-500/20"
            >
              Save Key
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
