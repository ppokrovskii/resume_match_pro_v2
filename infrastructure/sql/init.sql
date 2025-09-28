-- Resume Match Pro AI - Database Initialization
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Create user profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  organization_id UUID,
  role TEXT DEFAULT 'member' CHECK (role IN ('member', 'admin', 'owner')),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  owner_id UUID REFERENCES user_profiles(id),
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id),
  organization_id UUID REFERENCES organizations(id),
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL CHECK (file_type IN ('cv', 'job_description')),
  content_type TEXT,
  storage_path TEXT, -- Path in storage system
  text_content TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create document embeddings table
CREATE TABLE IF NOT EXISTS document_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  embedding VECTOR(1536), -- OpenAI embedding dimension
  text_chunks TEXT[],
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create match results table
CREATE TABLE IF NOT EXISTS match_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cv_id UUID REFERENCES documents(id),
  jd_id UUID REFERENCES documents(id),
  user_id UUID REFERENCES user_profiles(id),
  match_score FLOAT NOT NULL,
  similarity_breakdown JSONB DEFAULT '{}',
  matching_skills TEXT[],
  skill_gaps TEXT[],
  confidence_level FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- Vector similarity index (using ivfflat)
CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_match_results_cv_id ON match_results(cv_id);
CREATE INDEX IF NOT EXISTS idx_match_results_jd_id ON match_results(jd_id);
CREATE INDEX IF NOT EXISTS idx_match_results_user_id ON match_results(user_id);

-- Insert sample data for development
INSERT INTO user_profiles (id, email, name, role) 
VALUES 
  ('550e8400-e29b-41d4-a716-446655440001', 'admin@example.com', 'Admin User', 'admin'),
  ('550e8400-e29b-41d4-a716-446655440002', 'user@example.com', 'Regular User', 'member')
ON CONFLICT (email) DO NOTHING;

INSERT INTO organizations (id, name, owner_id)
VALUES 
  ('550e8400-e29b-41d4-a716-446655440010', 'Sample Organization', '550e8400-e29b-41d4-a716-446655440001')
ON CONFLICT DO NOTHING;

-- Update user profiles with organization
UPDATE user_profiles 
SET organization_id = '550e8400-e29b-41d4-a716-446655440010' 
WHERE email IN ('admin@example.com', 'user@example.com');

COMMIT;






