-- =============================================================================
-- TikTok Viral Signal Detector - Database Schema
-- =============================================================================
-- PostgreSQL 14+ required
-- This script initializes the complete database schema
-- =============================================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS embeddings CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS engagement_features CASCADE;
DROP TABLE IF EXISTS video_analysis CASCADE;
DROP TABLE IF EXISTS videos CASCADE;
DROP TABLE IF EXISTS creators CASCADE;

-- Drop existing types if they exist
DROP TYPE IF EXISTS engagement_trend_type CASCADE;
DROP TYPE IF EXISTS embedding_type CASCADE;

-- =============================================================================
-- Custom Types
-- =============================================================================

CREATE TYPE engagement_trend_type AS ENUM ('increasing', 'decreasing', 'stable');
CREATE TYPE embedding_type AS ENUM ('visual', 'text', 'audio');

-- =============================================================================
-- Table: creators
-- =============================================================================
-- Stores TikTok creator profile information
-- =============================================================================

CREATE TABLE creators (
    creator_id SERIAL PRIMARY KEY,
    handle VARCHAR(255) UNIQUE NOT NULL,
    tiktok_user_id VARCHAR(255),  -- TikTok's internal user ID
    follower_count INTEGER,
    following_count INTEGER,
    total_videos INTEGER,
    total_likes BIGINT,
    account_age_days INTEGER,
    bio TEXT,
    verified BOOLEAN DEFAULT FALSE,
    niche VARCHAR(100),
    profile_image_url TEXT,

    -- Timestamps
    first_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_follower_count CHECK (follower_count >= 0),
    CONSTRAINT check_total_videos CHECK (total_videos >= 0)
);

-- Indexes for creators table
CREATE INDEX idx_creator_handle ON creators(handle);
CREATE INDEX idx_creator_niche ON creators(niche);
CREATE INDEX idx_creator_follower_count ON creators(follower_count);
CREATE INDEX idx_creator_last_scraped ON creators(last_scraped_at DESC);

-- Comments
COMMENT ON TABLE creators IS 'TikTok creator profile information';
COMMENT ON COLUMN creators.handle IS 'TikTok username (e.g., @fitnessguru123)';
COMMENT ON COLUMN creators.niche IS 'Creator category (e.g., fitness, tech, beauty)';

-- =============================================================================
-- Table: videos
-- =============================================================================
-- Stores TikTok video metadata and engagement metrics
-- =============================================================================

CREATE TABLE videos (
    video_id VARCHAR(255) PRIMARY KEY,
    creator_id INTEGER NOT NULL REFERENCES creators(creator_id) ON DELETE CASCADE,

    -- Video metadata
    upload_date TIMESTAMP,
    caption TEXT,
    hashtags TEXT[],
    mentions TEXT[],
    music_name VARCHAR(500),
    music_author VARCHAR(255),
    duration_seconds INTEGER,
    video_url TEXT,
    download_url TEXT,

    -- Engagement metrics
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    save_count INTEGER DEFAULT 0,
    engagement_rate FLOAT,

    -- Computed fields
    virality_score FLOAT,  -- Custom metric combining view/engagement velocity

    -- Processing status
    downloaded BOOLEAN DEFAULT FALSE,
    processed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_view_count CHECK (view_count >= 0),
    CONSTRAINT check_like_count CHECK (like_count >= 0),
    CONSTRAINT check_duration CHECK (duration_seconds > 0),
    CONSTRAINT check_engagement_rate CHECK (engagement_rate >= 0 AND engagement_rate <= 1)
);

-- Indexes for videos table
CREATE INDEX idx_video_creator ON videos(creator_id);
CREATE INDEX idx_video_upload_date ON videos(upload_date DESC);
CREATE INDEX idx_video_engagement_rate ON videos(engagement_rate DESC);
CREATE INDEX idx_video_view_count ON videos(view_count DESC);
CREATE INDEX idx_video_processed ON videos(processed);
CREATE INDEX idx_video_hashtags ON videos USING GIN(hashtags);

-- Comments
COMMENT ON TABLE videos IS 'TikTok video metadata and engagement metrics';
COMMENT ON COLUMN videos.engagement_rate IS 'Calculated as (likes + comments + shares) / views';
COMMENT ON COLUMN videos.virality_score IS 'Custom metric for viral potential';

-- =============================================================================
-- Table: video_analysis
-- =============================================================================
-- Stores multimodal AI analysis results for videos
-- =============================================================================

CREATE TABLE video_analysis (
    analysis_id SERIAL PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,

    -- Audio analysis (Whisper)
    transcript TEXT,
    transcript_language VARCHAR(10),
    transcript_confidence FLOAT,
    audio_duration_seconds FLOAT,
    speech_rate FLOAT,  -- Words per minute

    -- Visual analysis (CLIP)
    dominant_colors JSONB,  -- Array of RGB values
    scene_changes INTEGER,  -- Number of scene transitions
    average_brightness FLOAT,

    -- Hook analysis (first 3 seconds)
    hook_score FLOAT,
    has_face_in_hook BOOLEAN,
    has_text_in_hook BOOLEAN,
    has_motion_in_hook BOOLEAN,
    audio_starts_immediately BOOLEAN,

    -- NLP analysis
    sentiment_score FLOAT,  -- 0-1 scale (0=negative, 1=positive)
    sentiment_label VARCHAR(20),  -- positive, negative, neutral
    topics TEXT[],
    keywords TEXT[],
    entities JSONB,  -- Named entities: [{"text": "Nike", "label": "ORG"}]

    -- Content characteristics
    face_time_ratio FLOAT,  -- Percentage of video showing faces
    motion_intensity FLOAT,  -- Average optical flow magnitude
    text_overlay_count INTEGER,  -- Number of text overlays detected

    -- Quality metrics
    video_quality_score FLOAT,  -- Technical quality assessment
    content_uniqueness_score FLOAT,  -- How unique compared to similar videos

    -- Timestamps
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_sentiment_score CHECK (sentiment_score >= 0 AND sentiment_score <= 1),
    CONSTRAINT check_hook_score CHECK (hook_score >= 0 AND hook_score <= 10),
    CONSTRAINT check_face_ratio CHECK (face_time_ratio >= 0 AND face_time_ratio <= 1),
    CONSTRAINT unique_video_analysis UNIQUE (video_id)
);

-- Indexes for video_analysis table
CREATE INDEX idx_analysis_video ON video_analysis(video_id);
CREATE INDEX idx_analysis_hook_score ON video_analysis(hook_score DESC);
CREATE INDEX idx_analysis_sentiment ON video_analysis(sentiment_score);
CREATE INDEX idx_analysis_topics ON video_analysis USING GIN(topics);

-- Comments
COMMENT ON TABLE video_analysis IS 'Multimodal AI analysis results for videos';
COMMENT ON COLUMN video_analysis.hook_score IS 'Score 0-10 for first 3 seconds quality';
COMMENT ON COLUMN video_analysis.sentiment_score IS '0=negative, 0.5=neutral, 1=positive';

-- =============================================================================
-- Table: engagement_features
-- =============================================================================
-- Stores time-series engagement pattern features for creators
-- =============================================================================

CREATE TABLE engagement_features (
    feature_id SERIAL PRIMARY KEY,
    creator_id INTEGER NOT NULL REFERENCES creators(creator_id) ON DELETE CASCADE,

    -- Growth metrics
    follower_velocity FLOAT,  -- % change in followers (estimated)
    follower_velocity_7d FLOAT,  -- 7-day velocity
    follower_velocity_30d FLOAT,  -- 30-day velocity
    growth_zscore FLOAT,  -- Statistical significance of growth
    growth_acceleration FLOAT,  -- Rate of change of velocity

    -- Engagement metrics
    avg_engagement_rate FLOAT,
    max_engagement_rate FLOAT,
    min_engagement_rate FLOAT,
    engagement_std FLOAT,  -- Standard deviation
    engagement_trend engagement_trend_type,

    -- Posting behavior
    posting_frequency FLOAT,  -- Videos per week
    avg_interval_days FLOAT,  -- Average days between posts
    consistency_score FLOAT,  -- 0-1, based on posting regularity
    most_active_day VARCHAR(10),  -- Monday, Tuesday, etc.
    most_active_hour INTEGER,  -- 0-23

    -- Content strategy
    content_diversity FLOAT,  -- 0-1, hashtag and topic variety
    avg_video_length FLOAT,  -- Seconds
    unique_hashtags_count INTEGER,
    total_hashtags_count INTEGER,
    hashtag_strategy_score FLOAT,  -- Quality of hashtag usage

    -- Audience metrics
    authenticity_score FLOAT,  -- 0-1, bot detection
    comment_like_ratio FLOAT,
    avg_comments_per_video FLOAT,
    audience_retention_proxy FLOAT,  -- Estimated from engagement patterns

    -- Viral potential indicators
    viral_video_count INTEGER,  -- Videos with >1M views
    consistency_viral_score FLOAT,  -- How often creator goes viral
    best_performing_niche VARCHAR(100),

    -- Time windows
    analysis_window_days INTEGER DEFAULT 30,
    video_count_in_window INTEGER,

    -- Timestamps
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_engagement_rate CHECK (avg_engagement_rate >= 0),
    CONSTRAINT check_consistency CHECK (consistency_score >= 0 AND consistency_score <= 1),
    CONSTRAINT check_authenticity CHECK (authenticity_score >= 0 AND authenticity_score <= 1)
);

-- Indexes for engagement_features table
CREATE INDEX idx_features_creator ON engagement_features(creator_id);
CREATE INDEX idx_features_growth_zscore ON engagement_features(growth_zscore DESC);
CREATE INDEX idx_features_engagement ON engagement_features(avg_engagement_rate DESC);
CREATE INDEX idx_features_calculated ON engagement_features(calculated_at DESC);

-- Comments
COMMENT ON TABLE engagement_features IS 'Time-series engagement pattern features';
COMMENT ON COLUMN engagement_features.growth_zscore IS 'Z-score > 2.0 indicates significant growth';
COMMENT ON COLUMN engagement_features.consistency_score IS 'Higher = more regular posting schedule';

-- =============================================================================
-- Table: predictions
-- =============================================================================
-- Stores ML model predictions for viral potential
-- =============================================================================

CREATE TABLE predictions (
    prediction_id SERIAL PRIMARY KEY,
    creator_id INTEGER NOT NULL REFERENCES creators(creator_id) ON DELETE CASCADE,

    -- Prediction outputs
    viral_probability FLOAT NOT NULL,  -- 0-1 probability score
    confidence FLOAT,  -- Model confidence in prediction
    prediction_label VARCHAR(20),  -- 'viral', 'non-viral', 'uncertain'

    -- Model information
    model_version VARCHAR(50),
    model_type VARCHAR(50),  -- 'ensemble', 'xgboost', 'neural_net'

    -- Feature importance
    feature_importance JSONB,  -- {"growth_zscore": 0.25, "hook_score": 0.18, ...}
    top_positive_features TEXT[],
    top_negative_features TEXT[],

    -- Risk assessment
    risk_factors TEXT[],
    opportunity_factors TEXT[],
    risk_score FLOAT,  -- 0-1, higher = riskier investment

    -- Intelligence report
    intelligence_report TEXT,  -- Generated by Gemini
    report_summary TEXT,  -- Short 2-3 sentence summary
    recommended_action VARCHAR(100),  -- 'reach_out_now', 'monitor', 'pass'
    optimal_outreach_timing VARCHAR(50),  -- 'immediate', 'within_1_week', etc.

    -- Personalization suggestions
    talking_points TEXT[],
    content_themes TEXT[],
    partnership_ideas TEXT[],

    -- Validation (if we have ground truth later)
    actual_outcome VARCHAR(20),  -- 'viral', 'non-viral' (filled later)
    prediction_correct BOOLEAN,

    -- Timestamps
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_viral_probability CHECK (viral_probability >= 0 AND viral_probability <= 1),
    CONSTRAINT check_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT check_risk_score CHECK (risk_score >= 0 AND risk_score <= 1)
);

-- Indexes for predictions table
CREATE INDEX idx_prediction_creator ON predictions(creator_id);
CREATE INDEX idx_prediction_probability ON predictions(viral_probability DESC);
CREATE INDEX idx_prediction_date ON predictions(predicted_at DESC);
CREATE INDEX idx_prediction_action ON predictions(recommended_action);

-- Comments
COMMENT ON TABLE predictions IS 'ML model predictions for creator viral potential';
COMMENT ON COLUMN predictions.viral_probability IS 'Probability of going viral in next 30 days';
COMMENT ON COLUMN predictions.feature_importance IS 'JSON object with feature importance scores';

-- =============================================================================
-- Table: embeddings
-- =============================================================================
-- Stores references to embeddings stored in ChromaDB
-- =============================================================================

CREATE TABLE embeddings (
    embedding_id SERIAL PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,

    -- Embedding metadata
    embedding_type embedding_type NOT NULL,  -- 'visual', 'text', 'audio'
    model_name VARCHAR(100),  -- 'clip-vit-b-32', 'sentence-transformers', etc.
    embedding_dimension INTEGER,  -- 512, 768, etc.

    -- ChromaDB reference
    chromadb_id VARCHAR(255) UNIQUE,  -- ID in ChromaDB for retrieval
    chromadb_collection VARCHAR(100),  -- Collection name in ChromaDB

    -- Quality metrics
    confidence_score FLOAT,
    quality_score FLOAT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_video_embedding_type UNIQUE (video_id, embedding_type)
);

-- Indexes for embeddings table
CREATE INDEX idx_embedding_video ON embeddings(video_id);
CREATE INDEX idx_embedding_type ON embeddings(embedding_type);
CREATE INDEX idx_embedding_chromadb ON embeddings(chromadb_id);

-- Comments
COMMENT ON TABLE embeddings IS 'References to vector embeddings stored in ChromaDB';
COMMENT ON COLUMN embeddings.chromadb_id IS 'Unique ID for retrieval from ChromaDB';

-- =============================================================================
-- Views for common queries
-- =============================================================================

-- View: Creator performance summary
CREATE OR REPLACE VIEW creator_performance_summary AS
SELECT
    c.creator_id,
    c.handle,
    c.follower_count,
    c.niche,
    COUNT(v.video_id) as total_videos,
    AVG(v.engagement_rate) as avg_engagement_rate,
    MAX(v.view_count) as max_views,
    ef.growth_zscore,
    ef.posting_frequency,
    p.viral_probability,
    p.recommended_action
FROM creators c
LEFT JOIN videos v ON c.creator_id = v.creator_id
LEFT JOIN engagement_features ef ON c.creator_id = ef.creator_id
LEFT JOIN predictions p ON c.creator_id = p.creator_id
GROUP BY c.creator_id, ef.growth_zscore, ef.posting_frequency, p.viral_probability, p.recommended_action;

COMMENT ON VIEW creator_performance_summary IS 'Quick overview of creator metrics and predictions';

-- View: Top viral candidates
CREATE OR REPLACE VIEW top_viral_candidates AS
SELECT
    c.creator_id,
    c.handle,
    c.follower_count,
    p.viral_probability,
    p.confidence,
    p.recommended_action,
    ef.growth_zscore,
    ef.avg_engagement_rate,
    p.predicted_at
FROM creators c
INNER JOIN predictions p ON c.creator_id = p.creator_id
LEFT JOIN engagement_features ef ON c.creator_id = ef.creator_id
WHERE p.viral_probability >= 0.7
ORDER BY p.viral_probability DESC, p.confidence DESC;

COMMENT ON VIEW top_viral_candidates IS 'Creators with high viral probability (>= 0.7)';

-- View: Recent high-performing videos
CREATE OR REPLACE VIEW recent_viral_videos AS
SELECT
    v.video_id,
    c.handle,
    v.caption,
    v.view_count,
    v.engagement_rate,
    va.hook_score,
    va.sentiment_score,
    v.upload_date
FROM videos v
INNER JOIN creators c ON v.creator_id = c.creator_id
LEFT JOIN video_analysis va ON v.video_id = va.video_id
WHERE v.view_count >= 1000000
ORDER BY v.upload_date DESC;

COMMENT ON VIEW recent_viral_videos IS 'Videos with 1M+ views';

-- =============================================================================
-- Functions for common calculations
-- =============================================================================

-- Function: Calculate engagement rate
CREATE OR REPLACE FUNCTION calculate_engagement_rate(
    p_view_count INTEGER,
    p_like_count INTEGER,
    p_comment_count INTEGER,
    p_share_count INTEGER
) RETURNS FLOAT AS $$
BEGIN
    IF p_view_count = 0 THEN
        RETURN 0;
    END IF;

    RETURN ((p_like_count + p_comment_count + p_share_count)::FLOAT / p_view_count::FLOAT);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_engagement_rate IS 'Calculate engagement rate from video metrics';

-- Function: Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Triggers
-- =============================================================================

-- Auto-update updated_at column
CREATE TRIGGER update_creators_updated_at
    BEFORE UPDATE ON creators
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_videos_updated_at
    BEFORE UPDATE ON videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-calculate engagement rate when video metrics change
CREATE OR REPLACE FUNCTION auto_calculate_engagement_rate()
RETURNS TRIGGER AS $$
BEGIN
    NEW.engagement_rate = calculate_engagement_rate(
        NEW.view_count,
        NEW.like_count,
        NEW.comment_count,
        NEW.share_count
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_video_engagement_rate
    BEFORE INSERT OR UPDATE ON videos
    FOR EACH ROW
    EXECUTE FUNCTION auto_calculate_engagement_rate();

-- =============================================================================
-- Grants and Permissions
-- =============================================================================

-- Grant appropriate permissions (adjust based on your security requirements)
-- Example: GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;

-- =============================================================================
-- Sample Data (Optional - for testing)
-- =============================================================================

-- Insert a sample creator
INSERT INTO creators (handle, follower_count, total_videos, bio, niche, verified)
VALUES
    ('@sample_creator', 15000, 120, 'Fitness enthusiast sharing daily workouts', 'fitness', false)
ON CONFLICT (handle) DO NOTHING;

-- =============================================================================
-- Database initialization complete
-- =============================================================================

-- Display table information
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Database initialization complete!';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Tables created: 6';
    RAISE NOTICE 'Views created: 3';
    RAISE NOTICE 'Functions created: 3';
    RAISE NOTICE 'Triggers created: 3';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Verify database connection from Python';
    RAISE NOTICE '2. Run data collection scripts to populate tables';
    RAISE NOTICE '3. Monitor database with: SELECT * FROM creator_performance_summary;';
    RAISE NOTICE '=============================================================================';
END $$;
