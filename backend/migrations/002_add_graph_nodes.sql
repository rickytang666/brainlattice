-- migration: add graph_nodes table
-- description: stores the conceptual network nodes and their directed links.

CREATE TABLE IF NOT EXISTS graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL,
    description TEXT,
    aliases TEXT[] DEFAULT '{}',
    outbound_links TEXT[] DEFAULT '{}',
    inbound_links TEXT[] DEFAULT '{}',
    node_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- index for fast lookups by project and concept name
CREATE INDEX IF NOT EXISTS idx_graph_nodes_project_concept ON graph_nodes(project_id, concept_id);
