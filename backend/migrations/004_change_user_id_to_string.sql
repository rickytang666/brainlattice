-- Change user_id from UUID to VARCHAR to support Clerk authentication IDs
ALTER TABLE projects ALTER COLUMN user_id TYPE VARCHAR USING user_id::text;
