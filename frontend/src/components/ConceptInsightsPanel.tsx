"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  IconX,
  IconBrain,
  IconMath,
  IconBulb,
  IconLoader,
} from "@tabler/icons-react";
import "katex/dist/katex.min.css";
import { InlineMath, BlockMath } from "react-katex";

// Helper function to render text with LaTeX math support
const renderTextWithMath = (text: string) => {
  // Split text by LaTeX delimiters
  const parts = text.split(/(\$\$.*?\$\$|\$.*?\$)/);

  return parts.map((part, index) => {
    if (part.startsWith("$$") && part.endsWith("$$")) {
      // Block math (display mode)
      const mathContent = part.slice(2, -2).trim();
      return <BlockMath key={index} math={mathContent} />;
    } else if (part.startsWith("$") && part.endsWith("$")) {
      // Inline math
      const mathContent = part.slice(1, -1).trim();
      return <InlineMath key={index} math={mathContent} />;
    } else {
      // Regular text
      return <span key={index}>{part}</span>;
    }
  });
};

interface ConceptInsights {
  concept_name: string;
  overview: string;
  related_concepts: string[];
  important_formulas: string[];
  key_theorems: string[];
  success: boolean;
  error?: string;
}

interface ConceptInsightsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  conceptName: string;
  graphMetadata?: {
    title: string;
    subject: string;
    total_concepts: number;
    depth_levels: number;
  };
  relatedConcepts?: string[];
}

export default function ConceptInsightsPanel({
  isOpen,
  onClose,
  conceptName,
  graphMetadata,
  relatedConcepts = [],
}: ConceptInsightsPanelProps) {
  const [insights, setInsights] = useState<ConceptInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const fetchInsights = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const contextData = {
        subject: graphMetadata?.subject || "Unknown",
        title: graphMetadata?.title || "Unknown",
        related_concepts: relatedConcepts,
      };

      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
      const response = await fetch(`${API_BASE_URL}/concept-insights`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          concept_name: conceptName,
          context_data: contextData,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch insights");
    } finally {
      setLoading(false);
    }
  }, [conceptName, graphMetadata, relatedConcepts]);

  // Clear insights when concept changes or panel closes
  useEffect(() => {
    setInsights(null);
    setError("");
    setLoading(false);
  }, [conceptName]);

  // Auto-fetch insights when panel opens
  useEffect(() => {
    if (isOpen && !loading) {
      fetchInsights();
    }
  }, [isOpen, fetchInsights]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden bg-card/95 backdrop-blur-sm border-cyan-500/30">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-cyan-500/20">
          <div className="flex items-center gap-3">
            <IconBrain className="h-6 w-6 text-cyan-400" />
            <div>
              <h2 className="text-xl font-bold text-foreground font-mono">
                Concept Insights
              </h2>
              <p className="text-sm text-cyan-400 font-mono">{conceptName}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <IconX className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <IconLoader className="h-8 w-8 text-cyan-400 animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground font-mono">
                  Generating AI insights...
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <p className="text-red-400 font-mono mb-4">{error}</p>
              <Button onClick={fetchInsights} variant="outline">
                Try Again
              </Button>
            </div>
          )}

          {insights && insights.success && (
            <div className="space-y-6">
              {/* Overview */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <IconBulb className="h-5 w-5 text-cyan-400" />
                  <h3 className="text-lg font-semibold text-foreground font-mono">
                    Overview
                  </h3>
                </div>
                <div className="text-muted-foreground leading-relaxed">
                  {renderTextWithMath(insights.overview)}
                </div>
              </div>

              {/* Related Concepts */}
              {insights.related_concepts.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <IconBrain className="h-5 w-5 text-cyan-400" />
                    <h3 className="text-lg font-semibold text-foreground font-mono">
                      Related Concepts
                    </h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {insights.related_concepts.map((concept, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-cyan-500/10 text-cyan-400 rounded-full text-sm font-mono border border-cyan-500/30"
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Important Formulas */}
              {insights.important_formulas.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <IconMath className="h-5 w-5 text-cyan-400" />
                    <h3 className="text-lg font-semibold text-foreground font-mono">
                      Important Formulas
                    </h3>
                  </div>
                  <div className="space-y-2">
                    {insights.important_formulas.map((formula, index) => (
                      <div
                        key={index}
                        className="p-3 bg-muted/30 rounded-lg border border-cyan-500/20 font-mono text-sm"
                      >
                        {renderTextWithMath(formula)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Theorems */}
              {insights.key_theorems.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <IconBulb className="h-5 w-5 text-cyan-400" />
                    <h3 className="text-lg font-semibold text-foreground font-mono">
                      Key Theorems & Principles
                    </h3>
                  </div>
                  <div className="space-y-2">
                    {insights.key_theorems.map((theorem, index) => (
                      <div
                        key={index}
                        className="p-3 bg-muted/30 rounded-lg border border-cyan-500/20"
                      >
                        <div className="text-muted-foreground text-sm leading-relaxed">
                          {renderTextWithMath(theorem)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {insights && !insights.success && (
            <div className="text-center py-12">
              <p className="text-red-400 font-mono mb-4">
                Failed to generate insights: {insights.error}
              </p>
              <Button onClick={fetchInsights} variant="outline">
                Try Again
              </Button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-cyan-500/20 bg-muted/20">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button
                onClick={fetchInsights}
                variant="outline"
                size="sm"
                disabled={loading || insights?.success === true}
                className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {insights?.success === true ? "Loaded" : "Refresh"}
              </Button>
              <Button
                onClick={onClose}
                size="sm"
                className="bg-cyan-500 hover:bg-cyan-600 text-black font-semibold"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
