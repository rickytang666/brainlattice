"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  IconUpload,
  IconFileText,
  IconX,
  IconCheck,
} from "@tabler/icons-react";
import {
  extractPDFText,
  createAIDigest,
  generateRelationships,
  saveProject,
} from "@/lib/api";

interface PDFUploadProps {
  onComplete?: () => void;
}

export default function PDFUpload({ onComplete }: PDFUploadProps = {}) {
  const router = useRouter();
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState("");
  const [error, setError] = useState("");
  const [graphData, setGraphData] = useState<Record<string, unknown> | null>(
    null
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleFileUpload = useCallback(
    async (file: File) => {
      if (file.type !== "application/pdf") {
        setError("Please upload a PDF file");
        return;
      }

      setIsUploading(true);
      setError("");
      setUploadProgress(0);
      setUploadStage("Processing PDF...");

      try {
        // Step 1: Extract text from PDF
        setUploadStage("Extracting text from PDF...");
        setUploadProgress(25);

        const extractData = await extractPDFText(file);
        setUploadProgress(50);

        // Step 2: Create AI digest
        setUploadStage("Creating AI digest...");
        setUploadProgress(60);

        const digestData = await createAIDigest(extractData.text);
        setUploadProgress(80);

        // Step 3: Generate knowledge graph
        setUploadStage("Generating knowledge graph...");
        setUploadProgress(90);

        const graphData = await generateRelationships(digestData.digest_data);
        setUploadProgress(95);

        // Store the knowledge graph
        setGraphData(graphData.graph_data);

        // Step 4: Save to Firebase
        setUploadStage("Saving to Firebase...");
        setUploadProgress(98);

        const saveData = await saveProject(
          digestData.digest_data,
          graphData.graph_data
        );

        setUploadProgress(100);
        setUploadStage("Complete!");

        // Stop the spinner
        setIsUploading(false);

        // Log the project ID for debugging
        console.log("Project saved with ID:", saveData.project_id);

        // Call onComplete callback if provided
        if (onComplete) {
          setTimeout(() => onComplete(), 2000); // Give user time to see success message
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
        setIsUploading(false);
        setUploadProgress(0);
        setUploadStage("");
      }
    },
    [onComplete]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      const pdfFile = files.find((file) => file.type === "application/pdf");

      if (pdfFile) {
        handleFileUpload(pdfFile);
      } else {
        setError("Please upload a PDF file");
      }
    },
    [handleFileUpload]
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <Card className="p-8 border-cyan-500/30 bg-card/50 backdrop-blur-sm">
        <div className="text-center mb-6">
          <IconFileText className="h-12 w-12 text-cyan-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-foreground mb-2 font-mono">
            UPLOAD YOUR PDF
          </h3>
          <p className="text-muted-foreground font-mono">
            DRAG AND DROP YOUR PDF FILE HERE OR CLICK TO BROWSE
          </p>
        </div>

        <div
          className={`border-2 border-dashed rounded-sm p-8 text-center transition-all duration-300 ${
            isDragOver
              ? "border-cyan-500 bg-cyan-500/10 backdrop-blur-sm"
              : "border-cyan-500/30 bg-card/50 backdrop-blur-sm"
          } ${isUploading ? "pointer-events-none opacity-50" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isUploading ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground font-mono">
                  {uploadStage}
                </p>
                <Progress value={uploadProgress} className="w-full" />
                <p className="text-xs text-muted-foreground font-mono">
                  {uploadProgress}% COMPLETE
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <IconUpload className="h-8 w-8 text-cyan-400 mx-auto" />
              <div>
                <Button
                  onClick={() => document.getElementById("file-input")?.click()}
                  variant="outline"
                  className="mb-2 border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10 hover:text-cyan-300 font-mono"
                >
                  CHOOSE FILE
                </Button>
                <p className="text-sm text-muted-foreground font-mono">
                  OR DRAG AND DROP YOUR PDF HERE
                </p>
              </div>
              <input
                id="file-input"
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-sm backdrop-blur-sm">
            <div className="flex items-center">
              <IconX className="h-5 w-5 text-red-400 mr-2" />
              <p className="text-sm text-red-400 font-mono">{error}</p>
            </div>
          </div>
        )}

        {uploadProgress === 100 && (
          <div className="mt-4 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-sm backdrop-blur-sm">
            <div className="flex items-center">
              <IconCheck className="h-5 w-5 text-cyan-400 mr-2" />
              <p className="text-sm text-cyan-400 font-mono">
                PDF PROCESSED SUCCESSFULLY!
              </p>
            </div>
          </div>
        )}

        {graphData && (
          <Card className="mt-6 p-6 border-cyan-500/30 bg-card/50 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-foreground mb-4 font-mono">
              KNOWLEDGE GRAPH
            </h3>
            <div className="mb-4 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-sm backdrop-blur-sm">
              <p className="text-sm text-cyan-400 mb-3 font-mono">
                🕸️ KNOWLEDGE GRAPH GENERATED WITH NODES AND RELATIONSHIPS FROM
                THE AI DIGEST.
              </p>
              <button
                onClick={() => {
                  // Store graph data in sessionStorage
                  sessionStorage.setItem(
                    "graphData",
                    JSON.stringify(graphData)
                  );
                  // Navigate to graph page
                  router.push("/graph");
                }}
                className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-black rounded-sm font-semibold font-mono tracking-wide transition-colors shadow-sm"
              >
                VIEW KNOWLEDGE GRAPH →
              </button>
            </div>
          </Card>
        )}
      </Card>
    </div>
  );
}
