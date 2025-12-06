# Supabase Setup Guide for Metadata Presets

## Overview
The config tab now supports saving metadata presets to a Supabase database. This allows users to save presets like "Valorant", "Lethal Company", "Random Clips" etc. and sync them across devices.

## Prerequisites
- Supabase account (free tier available at https://supabase.com)
- Project created in Supabase

## Setup Steps

### 1. Create Supabase Project
- Go to https://supabase.com and create a new project
- Note your project's:
  - `SUPABASE_URL` - Found in project settings → API
  - `SUPABASE_ANON_KEY` - Found in project settings → API (use the public key)

### 2. Create Database Table
Run the following SQL in the Supabase SQL Editor (Query → Create new Query):

```sql
-- Create metadata_presets table
CREATE TABLE metadata_presets (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  title TEXT,
  description TEXT,
  tags TEXT,
  visibility VARCHAR(50) DEFAULT 'unlisted',
  made_for_kids BOOLEAN DEFAULT FALSE,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, name)
);

-- Create index for faster queries
CREATE INDEX metadata_presets_user_id_idx ON metadata_presets(user_id);

-- Enable Row Level Security
ALTER TABLE metadata_presets ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to see only their own presets
CREATE POLICY "Users can view their own presets"
  ON metadata_presets FOR SELECT
  USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own presets"
  ON metadata_presets FOR INSERT
  WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own presets"
  ON metadata_presets FOR UPDATE
  USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own presets"
  ON metadata_presets FOR DELETE
  USING (auth.uid()::text = user_id);
```

### 3. Configure Environment Variables
Create or update a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Or set them as system environment variables.

### 4. Update Application
Install the new Supabase dependency:
```bash
pip install -r requirements.txt
```

## Usage

### For Authenticated Users
In the Config Tab, you'll now see:

**Local Templates (JSON Files)**
- Save/Load templates as JSON files locally
- Good for quick testing or offline use

**Cloud Presets (Supabase Database)**
- **Save as Database Preset** - Saves current metadata as a named preset to the cloud
  - Examples: "Valorant gameplay", "Lethal Company clips", "Random edits"
  - Presets are stored with all metadata (title, description, tags, visibility)
  
- **Load from Database** - Opens a dialog showing all your saved presets
  - Click "Load" to populate the form with a preset's values
  - Click the delete icon to remove a preset
  - Presets are user-specific (privacy-first)

### Example Presets
1. **Valorant Preset**
   - Title: "Valorant Highlights - {filename}"
   - Tags: "valorant, gameplay, highlights, esports"
   - Visibility: "public"

2. **Lethal Company Preset**
   - Title: "Lethal Company Funny Moments"
   - Tags: "lethal-company, gaming, funny, horror"
   - Visibility: "unlisted"

3. **Random Clips Preset**
   - Title: "Random Stream Clips - {filename}"
   - Tags: "streaming, clips, highlights"
   - Visibility: "private"

## Security Notes
- Presets are encrypted in transit (Supabase uses HTTPS)
- Row-level security (RLS) ensures users can only access their own presets
- User IDs are stored securely via Firebase authentication
- Metadata is stored as JSON for flexibility

## Troubleshooting

### "Database connection not available"
- Check that `SUPABASE_URL` and `SUPABASE_KEY` environment variables are set
- Verify your Supabase project is active
- Test connection in Supabase Dashboard

### "Cannot save preset: No user ID found"
- This happens for guest users (expected)
- Sign in with Google first, then try saving presets

### "Preset name already exists"
- Each preset name must be unique per user
- Rename the preset or use a different name

## Future Enhancements
- [ ] Preset categories/tags for organization
- [ ] Share presets with other users
- [ ] Import/export presets as JSON
- [ ] Preset templates library (community presets)
- [ ] Backup all presets to local file
