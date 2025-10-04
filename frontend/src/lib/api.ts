import { GraphData } from "@/types/graph";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface PDFExtractionResponse {
  filename: string;
  text: string;
  success: boolean;
  error_message?: string;
}

export interface DigestResponse {
  digest_data: Record<string, unknown>;
  success: boolean;
  error_message?: string;
}

export interface RelationshipResponse {
  graph_data: Record<string, unknown>;
  success: boolean;
  error_message?: string;
}

export interface OverviewResponse {
  overview_text: string;
  success: boolean;
  error_message?: string;
}

export interface AudioScriptResponse {
  script_text: string;
  success: boolean;
  error_message?: string;
}

export interface AudioResponse {
  audio_url: string;
  success: boolean;
  error_message?: string;
}

export interface ProjectSaveResponse {
  project_id: string;
  success: boolean;
  error_message?: string;
}

export interface ProjectGetResponse {
  project_data: {
    graph: {
      nodes: Array<{
        name: string;
        ins: string[];
        outs: string[];
      }>;
      graph_metadata: {
        title: string;
        subject: string;
        total_concepts: number;
        depth_levels: number;
      };
    };
    reference: Record<string, unknown>;
    created_at: {
      seconds: number;
    };
  };
  success: boolean;
  error_message?: string;
}

// PDF Processing API calls
export async function extractPDFText(file: File): Promise<PDFExtractionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to extract PDF text: ${response.statusText}`);
  }

  return response.json();
}

export async function createAIDigest(text: string): Promise<DigestResponse> {
  const response = await fetch(`${API_BASE_URL}/digest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create AI digest: ${response.statusText}`);
  }

  return response.json();
}

export async function generateRelationships(structuredData: Record<string, unknown>): Promise<RelationshipResponse> {
  const response = await fetch(`${API_BASE_URL}/relationships`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ structured_data: structuredData }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate relationships: ${response.statusText}`);
  }

  return response.json();
}

export async function generateOverview(digestData: Record<string, unknown>, graphData?: GraphData): Promise<OverviewResponse> {
  const response = await fetch(`${API_BASE_URL}/overview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ 
      digest_data: digestData,
      graph_data: graphData 
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate overview: ${response.statusText}`);
  }

  return response.json();
}

export async function generateAudioScript(digestData: Record<string, unknown>, graphData?: GraphData): Promise<AudioScriptResponse> {
  const response = await fetch(`${API_BASE_URL}/audio-script`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ 
      digest_data: digestData,
      graph_data: graphData 
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate audio script: ${response.statusText}`);
  }

  return response.json();
}

export async function generateAudio(scriptText: string): Promise<AudioResponse> {
  const response = await fetch(`${API_BASE_URL}/audio`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ script_text: scriptText }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate audio: ${response.statusText}`);
  }

  return response.json();
}

// Project Management API calls
export async function saveProject(digestData: Record<string, unknown>, graphData: Record<string, unknown>): Promise<ProjectSaveResponse> {
  const response = await fetch(`${API_BASE_URL}/project/save`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      digest_data: digestData,
      graph_data: graphData,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to save project: ${response.statusText}`);
  }

  return response.json();
}

export async function getProject(projectId: string): Promise<ProjectGetResponse> {
  const response = await fetch(`${API_BASE_URL}/project/${projectId}`);

  if (!response.ok) {
    throw new Error(`Failed to get project: ${response.statusText}`);
  }

  return response.json();
}

export async function listProjects(): Promise<Array<{ id: string; [key: string]: unknown }>> {
  const response = await fetch(`${API_BASE_URL}/projects/list`);

  if (!response.ok) {
    throw new Error(`Failed to list projects: ${response.statusText}`);
  }

  return response.json();
}

export async function updateProjectTitle(projectId: string, newTitle: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/project/${projectId}/title`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title: newTitle }),
  });

  if (!response.ok) {
    throw new Error(`Failed to update project title: ${response.statusText}`);
  }

  return response.json();
}

export async function deleteProject(projectId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/project/${projectId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to delete project: ${response.statusText}`);
  }

  return response.json();
}

// Complete PDF processing pipeline
export async function processPDF(file: File, onProgress?: (stage: string, progress: number) => void): Promise<string> {
  try {
    // Step 1: Extract text
    onProgress?.("Extracting text from PDF...", 20);
    const extractData = await extractPDFText(file);

    // Step 2: Create AI digest
    onProgress?.("Creating AI digest...", 40);
    const digestData = await createAIDigest(extractData.text);

    // Step 3: Generate relationships
    onProgress?.("Generating knowledge graph...", 60);
    const relationshipsData = await generateRelationships(digestData.digest_data);

    // Step 4: Save project
    onProgress?.("Saving project...", 80);
    const saveData = await saveProject(digestData.digest_data, relationshipsData.graph_data);

    onProgress?.("Complete!", 100);
    return saveData.project_id;

  } catch (error) {
    throw new Error(`PDF processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}
