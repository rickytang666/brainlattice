"use client";

import { useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { IconBrain, IconPlus } from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import PDFUpload from "@/components/PDFUpload";
import ProjectList from "@/components/ProjectList";

export default function Home() {
  const [showUpload, setShowUpload] = useState(false);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex justify-between items-center p-6 border-b dark:border-gray-800">
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
        {!showUpload ? (
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Your Projects
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Browse and manage your knowledge graphs
              </p>
            </div>

            {/* Project List */}
            <ProjectList />

            {/* Upload Button */}
            <div className="mt-8 flex justify-center">
              <Button
                onClick={() => setShowUpload(true)}
                size="lg"
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg shadow-lg"
              >
                <IconPlus className="mr-2 h-6 w-6" />
                Upload New Project
              </Button>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {/* Back Button */}
            <Button
              onClick={() => setShowUpload(false)}
              variant="outline"
              className="mb-6"
            >
              ← Back to Projects
            </Button>

            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                Upload New Project
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-300">
                Transform your PDF into an interactive knowledge graph
              </p>
            </div>

            {/* Upload Section */}
            <PDFUpload onComplete={() => setShowUpload(false)} />
          </div>
        )}
      </main>
    </div>
  );
}
