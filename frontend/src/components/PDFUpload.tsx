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
      <Card className="p-8">
        <div className="text-center mb-6">
          <IconFileText className="h-12 w-12 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Upload Your PDF
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            Drag and drop your PDF file here or click to browse
          </p>
        </div>

        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragOver
              ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
              : "border-gray-300 dark:border-gray-600"
          } ${isUploading ? "pointer-events-none opacity-50" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isUploading ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {uploadStage}
                </p>
                <Progress value={uploadProgress} className="w-full" />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {uploadProgress}% complete
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <IconUpload className="h-8 w-8 text-gray-400 mx-auto" />
              <div>
                <Button
                  onClick={() => document.getElementById("file-input")?.click()}
                  variant="outline"
                  className="mb-2"
                >
                  Choose File
                </Button>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  or drag and drop your PDF here
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
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center">
              <IconX className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        )}

        {uploadProgress === 100 && (
          <div className="mt-4 p-4 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-center">
              <IconCheck className="h-5 w-5 text-green-600 dark:text-green-400 mr-2" />
              <p className="text-sm text-green-800 dark:text-green-200">
                PDF processed successfully!
              </p>
            </div>
          </div>
        )}

        {graphData && (
          <Card className="mt-6 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Knowledge Graph
            </h3>
            <div className="mb-4 p-4 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded">
              <p className="text-sm text-green-800 dark:text-green-200 mb-3">
                🕸️ Knowledge graph generated with nodes and relationships from
                the AI digest.
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
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors shadow-sm"
              >
                View Knowledge Graph →
              </button>
            </div>
          </Card>
        )}
      </Card>
    </div>
  );
}
