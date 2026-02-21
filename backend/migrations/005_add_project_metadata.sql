-- Migration: Add project_metadata to projects table
ALTER TABLE projects ADD COLUMN project_metadata JSONB DEFAULT '{}';
