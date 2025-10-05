"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import Logo from "@/components/Logo";
import {
  IconArrowLeft,
  IconGraph,
  IconBook,
  IconBrain,
  IconCalendar,
  IconLayersLinked,
  IconDownload,
  IconRefresh,
  IconVolume,
} from "@tabler/icons-react";
import {
  getProject,
  generateOverview,
  generateAudioScript,
  generateAudio,
} from "@/lib/api";
import { GraphData } from "@/types/graph";

interface ProjectData {
  title: string;
  subject: string;
  total_concepts: number;
  depth_levels: number;
  created_at: string;
  graph_data?: Record<string, unknown>;
  digest_data?: Record<string, unknown>;
}

export default function ProjectPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [overview, setOverview] = useState<string>("");
  const [generatingOverview, setGeneratingOverview] = useState(false);
  const [audioScript, setAudioScript] = useState<string>("");
  const [audioUrl, setAudioUrl] = useState<string>("");
  const [generatingAudio, setGeneratingAudio] = useState(false);

  const loadProject = async () => {
    try {
      setLoading(true);
      const response = await getProject(projectId);

      // Handle both old and new formats
      const projectData = response.project_data as Record<string, unknown>;
      const graphData = (projectData.graph_data || projectData.graph) as Record<
        string,
        unknown
      >;
      const digestData = (projectData.digest_data ||
        projectData.reference) as Record<string, unknown>;
      const metadata = graphData?.graph_metadata as Record<string, unknown>;

      setProject({
        title:
          (projectData.title as string) ||
          (metadata?.title as string) ||
          "Untitled Project",
        subject:
          (projectData.subject as string) ||
          (metadata?.subject as string) ||
          "Unknown",
        total_concepts:
          (projectData.total_concepts as number) ||
          (metadata?.total_concepts as number) ||
          0,
        depth_levels:
          (projectData.depth_levels as number) ||
          (metadata?.depth_levels as number) ||
          0,
        created_at: projectData.created_at as string,
        graph_data: graphData,
        digest_data: digestData,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProject();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const handleViewGraph = () => {
    if (project?.graph_data) {
      sessionStorage.setItem("graphData", JSON.stringify(project.graph_data));
      sessionStorage.setItem("currentProjectId", projectId);
      router.push("/graph");
    }
  };

  const handleGenerateOverview = async () => {
    if (!project?.digest_data) return;

    try {
      setGeneratingOverview(true);
      // Use digest_data (reference) as primary input, with graph data as optional context
      const response = await generateOverview(
        project.digest_data,
        project.graph_data as GraphData | undefined
      );
      setOverview(response.overview_text);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate overview"
      );
    } finally {
      setGeneratingOverview(false);
    }
  };

  const downloadOverview = () => {
    if (!overview) return;

    // Create a clean filename from the title
    const cleanFilename =
      project?.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "") || "study-guide";

    const blob = new Blob([overview], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${cleanFilename}-cheatsheet.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleGenerateAudio = async () => {
    if (!project?.digest_data) return;

    try {
      setGeneratingAudio(true);

      // Generate script first using digest data
      const scriptResponse = await generateAudioScript(
        project.digest_data,
        project.graph_data as GraphData | undefined
      );
      setAudioScript(scriptResponse.script_text);

      // Then generate audio from script
      const audioResponse = await generateAudio(scriptResponse.script_text);

      // audio_url is already a data URL (data:audio/mpeg;base64,...)
      setAudioUrl(audioResponse.audio_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate audio");
    } finally {
      setGeneratingAudio(false);
    }
  };

  const downloadAudio = () => {
    if (!audioUrl) return;

    // Create download link
    const a = document.createElement("a");
    a.href = audioUrl;
    const cleanFilename =
      project?.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "") || "study-guide";
    a.download = `${cleanFilename}-audio.mp3`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-300">
          Loading project...
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Card className="p-6 bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
          <p className="text-red-600 dark:text-red-400">
            {error || "Project not found"}
          </p>
          <Button onClick={() => router.push("/projects")} className="mt-4">
            ← Back to Projects
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-grid-pattern">
      {/* Header */}
      <header className="flex justify-between items-center p-6 border-b border-cyan-500/30 backdrop-blur-sm bg-background/80">
        <Logo size="md" showText={true} />
        <ThemeToggle />
      </header>

      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Back Button */}
        <Button
          onClick={() => router.push("/projects")}
          variant="outline"
          className="mb-8 border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10 hover:text-cyan-300 font-mono"
        >
          <IconArrowLeft className="h-4 w-4 mr-2" />
          BACK TO PROJECTS
        </Button>

        {/* Project Header */}
        <div className="mb-10">
          <h1 className="text-5xl font-bold text-foreground mb-4 tracking-tight">
            {project.title}
          </h1>
          <div className="flex flex-wrap gap-6 text-muted-foreground font-mono">
            <div className="flex items-center">
              <IconBook className="h-5 w-5 mr-2 text-cyan-400/70" />
              <span className="text-lg">{project.subject}</span>
            </div>
            <div className="flex items-center">
              <IconCalendar className="h-5 w-5 mr-2 text-cyan-400/70" />
              <span className="text-lg">
                {new Date(project.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          <Card className="p-6 border-cyan-500/30 bg-card/50 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1 font-mono">
                  TOTAL CONCEPTS
                </p>
                <p className="text-3xl font-bold text-foreground">
                  {project.total_concepts}
                </p>
              </div>
              <IconBrain className="h-12 w-12 text-cyan-400" />
            </div>
          </Card>

          <Card className="p-6 border-cyan-500/30 bg-card/50 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1 font-mono">
                  DEPTH LEVELS
                </p>
                <p className="text-3xl font-bold text-foreground">
                  {project.depth_levels}
                </p>
              </div>
              <IconLayersLinked className="h-12 w-12 text-cyan-400" />
            </div>
          </Card>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          {/* View Graph Button */}
          <Card className="p-8 text-center border-cyan-500/30 bg-card/50 backdrop-blur-sm">
            <IconGraph className="h-16 w-16 mx-auto mb-4 text-cyan-400" />
            <h2 className="text-2xl font-bold text-foreground mb-2">
              KNOWLEDGE GRAPH
            </h2>
            <p className="text-muted-foreground mb-6 font-light">
              Explore the interactive visualization of concepts and their
              relationships
            </p>
            <Button
              onClick={handleViewGraph}
              size="lg"
              className="bg-cyan-500 hover:bg-cyan-600 text-black font-semibold px-8 py-6 text-lg font-mono tracking-wide"
            >
              <IconGraph className="h-6 w-6 mr-2" />
              VIEW GRAPH
            </Button>
          </Card>

          {/* Study Guide */}
          <Card className="p-8 text-center border-cyan-500/30 bg-card/50 backdrop-blur-sm">
            <IconBook className="h-16 w-16 mx-auto mb-4 text-cyan-400" />
            <h2 className="text-2xl font-bold text-foreground mb-2">
              STUDY GUIDE
            </h2>
            <p className="text-muted-foreground mb-6 font-light">
              Generate a comprehensive markdown cheatsheet for download
            </p>
            <div className="flex gap-3 justify-center">
              <Button
                onClick={handleGenerateOverview}
                disabled={generatingOverview}
                size="lg"
                variant="outline"
                className="px-8 py-6 text-lg border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10 hover:text-cyan-300 font-mono"
              >
                {generatingOverview ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-cyan-400 mr-2"></div>
                    GENERATING...
                  </>
                ) : (
                  <>
                    <IconRefresh className="h-6 w-6 mr-2" />
                    {overview ? "REGENERATE" : "GENERATE"}
                  </>
                )}
              </Button>
              {overview && (
                <Button
                  onClick={downloadOverview}
                  size="lg"
                  className="bg-cyan-500 hover:bg-cyan-600 text-black font-semibold px-8 py-6 text-lg font-mono tracking-wide"
                >
                  <IconDownload className="h-6 w-6 mr-2" />
                  DOWNLOAD
                </Button>
              )}
            </div>
          </Card>
        </div>

        {/* Overview Preview */}
        {overview && (
          <Card className="p-6 mb-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Study Guide Preview
            </h3>
            <div className="prose dark:prose-invert max-w-none overflow-y-auto max-h-[500px]">
              <div className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 p-6 rounded-lg font-mono border border-gray-200 dark:border-gray-700">
                {overview}
              </div>
            </div>
          </Card>
        )}

        {/* Audio Podcast Card */}
        <Card className="p-8 text-center mb-8">
          <IconVolume className="h-16 w-16 mx-auto mb-4 text-green-600 dark:text-green-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Audio Study Podcast
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            Generate a 1-2 minute sharp, no-fluff podcast with AI narration
          </p>
          <div className="flex gap-3 justify-center mb-6">
            <Button
              onClick={handleGenerateAudio}
              disabled={generatingAudio}
              size="lg"
              variant="outline"
              className="px-8 py-6 text-lg"
            >
              {generatingAudio ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600 mr-2"></div>
                  Generating...
                </>
              ) : (
                <>
                  <IconRefresh className="h-6 w-6 mr-2" />
                  {audioScript ? "Regenerate" : "Generate"}
                </>
              )}
            </Button>
            {audioUrl && (
              <Button
                onClick={downloadAudio}
                size="lg"
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-6 text-lg"
              >
                <IconDownload className="h-6 w-6 mr-2" />
                Download MP3
              </Button>
            )}
          </div>

          {/* Audio Player */}
          {audioUrl && (
            <div className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 mt-6">
              <div className="flex items-center gap-3 mb-4">
                <IconVolume className="h-6 w-6 text-green-600 dark:text-green-400" />
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  Your audio podcast is ready!
                </span>
              </div>
              <audio controls className="w-full">
                <source src={audioUrl} type="audio/mpeg" />
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
