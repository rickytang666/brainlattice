"use client";

import { useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { IconBrain } from "@tabler/icons-react";
import PDFUpload from "@/components/PDFUpload";
import ProjectView from "@/components/ProjectView";

export default function Home() {
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);

  const handleBackToUpload = () => {
    setCurrentProjectId(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex justify-between items-center p-6">
        <div className="flex items-center space-x-2">
          <IconBrain className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            BrainLattice
          </h1>
        </div>
        <ThemeToggle />
      </header>

      {/* Main Content */}
      <main className="flex-1 px-6 py-8">
        {currentProjectId ? (
          <ProjectView
            projectId={currentProjectId}
            onBack={handleBackToUpload}
          />
        ) : (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
                Upload PDFs → Get Knowledge Graphs
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
                Transform massive course PDFs into interactive concept graphs
                with AI-powered study materials
              </p>
            </div>
            <PDFUpload />
          </div>
        )}
      </main>
    </div>
  );
}
