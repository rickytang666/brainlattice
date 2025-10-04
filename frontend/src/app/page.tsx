import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { IconUpload, IconBrain } from "@tabler/icons-react";

export default function Home() {
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
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="text-center max-w-2xl">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
            Upload PDFs → Get Knowledge Graphs
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
            Transform massive course PDFs into interactive concept graphs with
            AI-powered study materials
          </p>
          <Button size="lg" className="text-lg px-8 py-3">
            <IconUpload className="mr-2 h-5 w-5" />
            Upload PDF
          </Button>
        </div>
      </main>
    </div>
  );
}
