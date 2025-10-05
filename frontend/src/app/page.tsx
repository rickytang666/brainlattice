"use client";

import { useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { IconPlus } from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import PDFUpload from "@/components/PDFUpload";
import ProjectList from "@/components/ProjectList";
import Logo from "@/components/Logo";

export default function Home() {
  const [showUpload, setShowUpload] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-grid-pattern">
      {/* Header */}
      <header className="flex justify-between items-center p-6 border-b border-cyan-500/30 backdrop-blur-sm bg-background/80">
        <Logo size="md" showText={true} />
        <ThemeToggle />
      </header>

      {/* Main Content */}
      <main className="flex-1 px-6 py-8">
        {!showUpload ? (
          <div className="max-w-7xl mx-auto">
            <div className="mb-10">
              <h2 className="text-4xl font-bold text-foreground mb-3 tracking-tight">
                YOUR <span className="text-cyan-400 font-mono">PROJECTS</span>
              </h2>
              <p className="text-muted-foreground text-lg font-light">
                Browse and manage your knowledge graphs
              </p>
            </div>

            {/* Project List */}
            <ProjectList />

            {/* Upload Button */}
            <div className="mt-12 flex justify-center">
              <Button
                onClick={() => setShowUpload(true)}
                size="lg"
                className="relative bg-cyan-500 hover:bg-cyan-600 text-black font-semibold px-10 py-7 text-lg border-glow-cyan transition-all duration-300 hover:scale-105"
              >
                <IconPlus className="mr-2 h-6 w-6" />
                <span className="font-mono tracking-wide">
                  UPLOAD NEW PROJECT
                </span>
              </Button>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {/* Back Button */}
            <Button
              onClick={() => setShowUpload(false)}
              variant="outline"
              className="mb-8 border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10 hover:text-cyan-300 font-mono"
            >
              ← BACK TO PROJECTS
            </Button>

            <div className="text-center mb-10">
              <h2 className="text-5xl font-bold text-foreground mb-4 tracking-tight">
                UPLOAD NEW{" "}
                <span className="text-cyan-400 font-mono">PROJECT</span>
              </h2>
              <p className="text-xl text-muted-foreground font-light">
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
