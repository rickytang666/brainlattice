-- one graph node per (project_id, concept_id) so re-ingest updates notes in place
BEGIN;

-- drop duplicates first: keep a row with a real note, then the most recently updated
WITH ranked AS (
    SELECT
        id,
        row_number() OVER (
            PARTITION BY project_id, concept_id
            ORDER BY
                (content IS NOT NULL
                    AND content <> ''
                    AND content NOT LIKE 'failed to generate note for %') DESC,
                updated_at DESC NULLS LAST,
                created_at DESC NULLS LAST,
                id
        ) AS rn
    FROM graph_nodes
)
DELETE FROM graph_nodes g
USING ranked r
WHERE g.id = r.id AND r.rn > 1;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_graph_nodes_project_concept'
    ) THEN
        ALTER TABLE graph_nodes
            ADD CONSTRAINT uq_graph_nodes_project_concept UNIQUE (project_id, concept_id);
    END IF;
END $$;

-- the unique constraint's index covers these lookups
DROP INDEX IF EXISTS idx_graph_nodes_project_concept;
DROP INDEX IF EXISTS idx_project_concept;

COMMIT;
