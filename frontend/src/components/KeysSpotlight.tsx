import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { SPOTLIGHT_DISMISSED_KEY } from "../config";

interface KeysSpotlightProps {
  targetSelector: string;
  onDismiss: () => void;
}

export function KeysSpotlight({ targetSelector, onDismiss }: KeysSpotlightProps) {
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    const measure = () => {
      const el = document.querySelector(targetSelector);
      if (el) {
        setRect(el.getBoundingClientRect());
      }
    };

    // wait to ensure all initial UI animations (like Navbar sliding in) complete
    const tId = window.setTimeout(measure, 1200);
    
    // also re-measure on resize
    window.addEventListener("resize", measure);
    
    return () => {
      window.clearTimeout(tId);
      window.removeEventListener("resize", measure);
    };
  }, [targetSelector]);

  const dismiss = () => {
    localStorage.setItem(SPOTLIGHT_DISMISSED_KEY, "1");
    onDismiss();
  };

  const handleClickThrough = (e: React.MouseEvent) => {
    e.stopPropagation();
    const el = document.querySelector(targetSelector) as HTMLElement;
    if (el) el.click();
    dismiss();
  };

  if (!rect) return null;

  return createPortal(
    <>
      <div 
        className="fixed inset-0 z-[200] cursor-default" 
        onClick={dismiss} 
      />

      {/* highlight cut out */}
      <div
        className="fixed z-[201] rounded-[10px] pointer-events-none transition-all duration-300"
        style={{
          top: rect.top - 6,
          left: rect.left - 6,
          width: rect.width + 12,
          height: rect.height + 12,
          boxShadow: "0 0 0 9999px rgba(0,0,0,0.6)",
        }}
      >
        <div 
          className="absolute inset-0 pointer-events-auto cursor-pointer" 
          onClick={handleClickThrough} 
        />
      </div>

      {/* ring */}
      <div
        className="fixed z-[201] rounded-[10px] border-2 border-primary/50 pointer-events-none"
        style={{
          top: rect.top - 6,
          left: rect.left - 6,
          width: rect.width + 12,
          height: rect.height + 12,
        }}
      />

      {/* tool tip card */}
      <div
        className="fixed z-[202] pointer-events-auto flex flex-col items-center animate-in fade-in slide-in-from-top-2 duration-500"
        style={{
          top: rect.bottom + 16,
          left: rect.left + rect.width / 2,
          transform: "translateX(-50%)",
        }}
      >
        {/* pointer triangle element */}
        <div className="w-0 h-0 border-l-[8px] border-r-[8px] border-b-[8px] border-l-transparent border-r-transparent border-b-primary relative top-[1px]" />
        
        {/* content */}
        <div className="bg-card border-2 border-primary/50 rounded-xl shadow-2xl p-4 w-[280px]">
          <p className="text-xs leading-relaxed mb-4">
            You'll need to provide your own API keys from <a href="https://aistudio.google.com" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline font-medium">Google AI</a> and <a href="https://openrouter.ai/settings/keys" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline font-medium">OpenRouter</a> to start processing documents.
          </p>
          <div className="flex justify-end gap-2">
            <button
              onClick={dismiss}
              className="text-xs font-medium text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-md transition-colors"
            >
              Skip
            </button>
            <button
              onClick={handleClickThrough}
              className="text-xs font-medium bg-primary text-primary-foreground hover:brightness-110 px-3 py-1.5 rounded-md transition-colors shadow-sm"
            >
              Add Keys
            </button>
          </div>
        </div>
      </div>
    </>,
    document.body
  );
}
