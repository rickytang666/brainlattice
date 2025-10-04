"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  IconDownload,
  IconVolume,
  IconRefresh,
  IconArrowLeft,
} from "@tabler/icons-react";
import KnowledgeGraph from "./KnowledgeGraph";
import {
  getProject,
  generateOverview,
  generateAudioScript,
  generateAudio,
} from "@/lib/api";
import { ProjectData } from "@/types/graph";

interface ProjectViewProps {
  projectId: string;
  onBack: () => void;
}

export default function ProjectView({ projectId, onBack }: ProjectViewProps) {
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [overview, setOverview] = useState<string>("");
  const [audioScript, setAudioScript] = useState<string>("");
  const [audioUrl, setAudioUrl] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [generatingOverview, setGeneratingOverview] = useState(false);
  const [generatingAudio, setGeneratingAudio] = useState(false);
  const [error, setError] = useState("");

  const loadProject = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getProject(projectId);
      setProjectData(response.project_data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  const handleGenerateOverview = async () => {
    if (!projectData?.graph) return;

    try {
      setGeneratingOverview(true);
      const response = await generateOverview(projectData.graph);
      setOverview(response.overview_text);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate overview"
      );
    } finally {
      setGeneratingOverview(false);
    }
  };

  const handleGenerateAudio = async () => {
    if (!projectData?.graph) return;

    try {
      setGeneratingAudio(true);

      // Generate script first
      const scriptResponse = await generateAudioScript(projectData.graph);
      setAudioScript(scriptResponse.script_text);

      // Then generate audio
      const audioResponse = await generateAudio(scriptResponse.script_text);
      setAudioUrl(audioResponse.audio_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate audio");
    } finally {
      setGeneratingAudio(false);
    }
  };

  const downloadOverview = () => {
    if (!overview) return;

    const blob = new Blob([overview], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${
      projectData?.graph?.graph_metadata?.title || "study-guide"
    }.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
        <Button onClick={loadProject} variant="outline">
          <IconRefresh className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  if (!projectData) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600 dark:text-gray-300">Project not found</p>
        <Button onClick={onBack} variant="outline" className="mt-4">
          <IconArrowLeft className="mr-2 h-4 w-4" />
          Back to Upload
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button onClick={onBack} variant="outline" size="sm">
            <IconArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {projectData.graph?.graph_metadata?.title || "Knowledge Graph"}
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              {projectData.graph?.graph_metadata?.subject} •{" "}
              {projectData.graph?.graph_metadata?.total_concepts} concepts
            </p>
          </div>
        </div>
      </div>

      {/* Knowledge Graph */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Interactive Knowledge Graph
        </h2>
        <KnowledgeGraph graphData={projectData.graph} />
      </Card>

      {/* Study Materials */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overview */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Study Guide Overview
            </h3>
            <div className="space-x-2">
              <Button
                onClick={handleGenerateOverview}
                disabled={generatingOverview}
                size="sm"
                variant="outline"
              >
                {generatingOverview ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                ) : (
                  "Generate"
                )}
              </Button>
              {overview && (
                <Button onClick={downloadOverview} size="sm" variant="outline">
                  <IconDownload className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {overview ? (
            <div className="prose dark:prose-invert max-w-none">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                {overview}
              </pre>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Click &quot;Generate&quot; to create a study guide overview
            </div>
          )}
        </Card>

        {/* Audio */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Audio Study Material
            </h3>
            <Button
              onClick={handleGenerateAudio}
              disabled={generatingAudio}
              size="sm"
              variant="outline"
            >
              {generatingAudio ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              ) : (
                <>
                  <IconVolume className="mr-2 h-4 w-4" />
                  Generate Audio
                </>
              )}
            </Button>
          </div>

          {audioScript ? (
            <div className="space-y-4">
              <div className="prose dark:prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg max-h-48 overflow-y-auto">
                  {audioScript}
                </pre>
              </div>
              {audioUrl && (
                <div className="text-center">
                  <audio controls className="w-full">
                    <source src={audioUrl} type="audio/mpeg" />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Click &quot;Generate Audio&quot; to create a podcast-style study
              material
            </div>
          )}
        </Card>
      </div>

      {/* Project Metadata */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Project Information
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-500 dark:text-gray-400">Total Concepts</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {projectData.graph?.graph_metadata?.total_concepts || 0}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Depth Levels</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {projectData.graph?.graph_metadata?.depth_levels || 0}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Subject</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {projectData.graph?.graph_metadata?.subject || "N/A"}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Created</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {projectData.created_at
                ? new Date(
                    projectData.created_at.seconds * 1000
                  ).toLocaleDateString()
                : "N/A"}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
