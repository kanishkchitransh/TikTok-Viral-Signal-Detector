"""
SQLAlchemy ORM models for TikTok Viral Signal Detector.
Maps to PostgreSQL database schema, with SQLite compatibility for testing.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text, TIMESTAMP,
    ForeignKey, BigInteger, CheckConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import JSONB, ENUM, ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from config.database import Base, get_engine


# Database-agnostic types
def get_json_type():
    """Returns JSONB for PostgreSQL, JSON for others."""
    engine = get_engine()
    if engine.dialect.name == 'postgresql':
        return JSONB
    return JSON


def get_array_type(item_type=String):
    """Returns ARRAY for PostgreSQL, JSON for others."""
    engine = get_engine()
    if engine.dialect.name == 'postgresql':
        return PG_ARRAY(item_type)
    return JSON  # Store arrays as JSON in SQLite


# Custom ENUM types (simplified for SQLite compatibility)
engagement_trend_enum = String(20)
embedding_type_enum = String(20)


class Creator(Base):
    """TikTok creator profile information."""

    __tablename__ = "creators"

    creator_id = Column(Integer, primary_key=True, autoincrement=True)
    handle = Column(String(255), unique=True, nullable=False, index=True)
    tiktok_user_id = Column(String(255))
    follower_count = Column(Integer)
    following_count = Column(Integer)
    total_videos = Column(Integer)
    total_likes = Column(BigInteger)
    account_age_days = Column(Integer)
    bio = Column(Text)
    verified = Column(Boolean, default=False)
    niche = Column(String(100), index=True)
    profile_image_url = Column(Text)

    # Timestamps
    first_scraped_at = Column(TIMESTAMP, default=func.now())
    last_scraped_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    videos = relationship("Video", back_populates="creator", cascade="all, delete-orphan")
    engagement_features = relationship("EngagementFeatures", back_populates="creator", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="creator", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('follower_count >= 0', name='check_follower_count'),
        CheckConstraint('total_videos >= 0', name='check_total_videos'),
        Index('idx_creator_follower_count', 'follower_count'),
        Index('idx_creator_last_scraped', 'last_scraped_at'),
    )

    def __repr__(self):
        return f"<Creator(handle='{self.handle}', followers={self.follower_count})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'creator_id': self.creator_id,
            'handle': self.handle,
            'follower_count': self.follower_count,
            'total_videos': self.total_videos,
            'niche': self.niche,
            'verified': self.verified,
            'bio': self.bio,
        }


class Video(Base):
    """TikTok video metadata and engagement metrics."""

    __tablename__ = "videos"

    video_id = Column(String(255), primary_key=True)
    creator_id = Column(Integer, ForeignKey('creators.creator_id', ondelete='CASCADE'), nullable=False, index=True)

    # Video metadata
    upload_date = Column(TIMESTAMP, index=True)
    caption = Column(Text)
    hashtags = Column(JSON)
    mentions = Column(JSON)
    music_name = Column(String(500))
    music_author = Column(String(255))
    duration_seconds = Column(Integer)
    video_url = Column(Text)
    download_url = Column(Text)

    # Engagement metrics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    save_count = Column(Integer, default=0)
    engagement_rate = Column(Float)

    # Computed fields
    virality_score = Column(Float)

    # Processing status
    downloaded = Column(Boolean, default=False)
    processed = Column(Boolean, default=False, index=True)

    # Timestamps
    scraped_at = Column(TIMESTAMP, default=func.now())
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("Creator", back_populates="videos")
    analysis = relationship("VideoAnalysis", back_populates="video", uselist=False, cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="video", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('view_count >= 0', name='check_view_count'),
        CheckConstraint('like_count >= 0', name='check_like_count'),
        CheckConstraint('duration_seconds > 0', name='check_duration'),
        CheckConstraint('engagement_rate >= 0 AND engagement_rate <= 1', name='check_engagement_rate'),
        Index('idx_video_engagement_rate', 'engagement_rate'),
        Index('idx_video_view_count', 'view_count'),
        Index('idx_video_upload_date', 'upload_date'),
    )

    def __repr__(self):
        return f"<Video(id='{self.video_id}', views={self.view_count})>"

    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate."""
        if self.view_count == 0:
            return 0.0
        total_engagement = (self.like_count or 0) + (self.comment_count or 0) + (self.share_count or 0)
        return total_engagement / self.view_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'video_id': self.video_id,
            'creator_id': self.creator_id,
            'caption': self.caption,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'engagement_rate': self.engagement_rate,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
        }


class VideoAnalysis(Base):
    """Multimodal AI analysis results for videos."""

    __tablename__ = "video_analysis"

    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(255), ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Audio analysis (Whisper)
    transcript = Column(Text)
    transcript_language = Column(String(10))
    transcript_confidence = Column(Float)
    audio_duration_seconds = Column(Float)
    speech_rate = Column(Float)

    # Visual analysis (CLIP)
    dominant_colors = Column(JSON)
    scene_changes = Column(Integer)
    average_brightness = Column(Float)

    # Hook analysis
    hook_score = Column(Float, index=True)
    has_face_in_hook = Column(Boolean)
    has_text_in_hook = Column(Boolean)
    has_motion_in_hook = Column(Boolean)
    audio_starts_immediately = Column(Boolean)

    # NLP analysis
    sentiment_score = Column(Float, index=True)
    sentiment_label = Column(String(20))
    topics = Column(JSON)
    keywords = Column(JSON)
    entities = Column(JSON)

    # Content characteristics
    face_time_ratio = Column(Float)
    motion_intensity = Column(Float)
    text_overlay_count = Column(Integer)

    # Quality metrics
    video_quality_score = Column(Float)
    content_uniqueness_score = Column(Float)

    # Timestamps
    analyzed_at = Column(TIMESTAMP, default=func.now())
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    video = relationship("Video", back_populates="analysis")

    # Constraints
    __table_args__ = (
        CheckConstraint('sentiment_score >= 0 AND sentiment_score <= 1', name='check_sentiment_score'),
        CheckConstraint('hook_score >= 0 AND hook_score <= 10', name='check_hook_score'),
        CheckConstraint('face_time_ratio >= 0 AND face_time_ratio <= 1', name='check_face_ratio'),
    )

    def __repr__(self):
        return f"<VideoAnalysis(video_id='{self.video_id}', hook_score={self.hook_score})>"


class EngagementFeatures(Base):
    """Time-series engagement pattern features for creators."""

    __tablename__ = "engagement_features"

    feature_id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey('creators.creator_id', ondelete='CASCADE'), nullable=False, index=True)

    # Growth metrics
    follower_velocity = Column(Float)
    follower_velocity_7d = Column(Float)
    follower_velocity_30d = Column(Float)
    growth_zscore = Column(Float, index=True)
    growth_acceleration = Column(Float)

    # Engagement metrics
    avg_engagement_rate = Column(Float, index=True)
    max_engagement_rate = Column(Float)
    min_engagement_rate = Column(Float)
    engagement_std = Column(Float)
    engagement_trend = Column(engagement_trend_enum)

    # Posting behavior
    posting_frequency = Column(Float)
    avg_interval_days = Column(Float)
    consistency_score = Column(Float)
    most_active_day = Column(String(10))
    most_active_hour = Column(Integer)

    # Content strategy
    content_diversity = Column(Float)
    avg_video_length = Column(Float)
    unique_hashtags_count = Column(Integer)
    total_hashtags_count = Column(Integer)
    hashtag_strategy_score = Column(Float)

    # Audience metrics
    authenticity_score = Column(Float)
    comment_like_ratio = Column(Float)
    avg_comments_per_video = Column(Float)
    audience_retention_proxy = Column(Float)

    # Viral potential indicators
    viral_video_count = Column(Integer)
    consistency_viral_score = Column(Float)
    best_performing_niche = Column(String(100))

    # Time windows
    analysis_window_days = Column(Integer, default=30)
    video_count_in_window = Column(Integer)

    # Timestamps
    calculated_at = Column(TIMESTAMP, default=func.now(), index=True)
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    creator = relationship("Creator", back_populates="engagement_features")

    # Constraints
    __table_args__ = (
        CheckConstraint('avg_engagement_rate >= 0', name='check_engagement_rate'),
        CheckConstraint('consistency_score >= 0 AND consistency_score <= 1', name='check_consistency'),
        CheckConstraint('authenticity_score >= 0 AND authenticity_score <= 1', name='check_authenticity'),
    )

    def __repr__(self):
        return f"<EngagementFeatures(creator_id={self.creator_id}, growth_zscore={self.growth_zscore})>"


class Prediction(Base):
    """ML model predictions for creator viral potential."""

    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey('creators.creator_id', ondelete='CASCADE'), nullable=False, index=True)

    # Prediction outputs
    viral_probability = Column(Float, nullable=False, index=True)
    confidence = Column(Float)
    prediction_label = Column(String(20))

    # Model information
    model_version = Column(String(50))
    model_type = Column(String(50))

    # Feature importance
    feature_importance = Column(JSON)
    top_positive_features = Column(JSON)
    top_negative_features = Column(JSON)

    # Risk assessment
    risk_factors = Column(JSON)
    opportunity_factors = Column(JSON)
    risk_score = Column(Float)

    # Intelligence report
    intelligence_report = Column(Text)
    report_summary = Column(Text)
    recommended_action = Column(String(100), index=True)
    optimal_outreach_timing = Column(String(50))

    # Personalization suggestions
    talking_points = Column(JSON)
    content_themes = Column(JSON)
    partnership_ideas = Column(JSON)

    # Validation
    actual_outcome = Column(String(20))
    prediction_correct = Column(Boolean)

    # Timestamps
    predicted_at = Column(TIMESTAMP, default=func.now(), index=True)
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    creator = relationship("Creator", back_populates="predictions")

    # Constraints
    __table_args__ = (
        CheckConstraint('viral_probability >= 0 AND viral_probability <= 1', name='check_viral_probability'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_confidence'),
        CheckConstraint('risk_score >= 0 AND risk_score <= 1', name='check_risk_score'),
    )

    def __repr__(self):
        return f"<Prediction(creator_id={self.creator_id}, probability={self.viral_probability:.2f})>"


class Embedding(Base):
    """References to embeddings stored in ChromaDB."""

    __tablename__ = "embeddings"

    embedding_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(255), ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, index=True)

    # Embedding metadata
    embedding_type = Column(embedding_type_enum, nullable=False, index=True)
    model_name = Column(String(100))
    embedding_dimension = Column(Integer)

    # ChromaDB reference
    chromadb_id = Column(String(255), unique=True, index=True)
    chromadb_collection = Column(String(100))

    # Quality metrics
    confidence_score = Column(Float)
    quality_score = Column(Float)

    # Timestamps
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    video = relationship("Video", back_populates="embeddings")

    # Constraints
    __table_args__ = (
        Index('unique_video_embedding_type', 'video_id', 'embedding_type', unique=True),
    )

    def __repr__(self):
        return f"<Embedding(video_id='{self.video_id}', type='{self.embedding_type}')>"


if __name__ == "__main__":
    # Test model definitions
    print("Testing ORM models...")
    print(f"✓ Creator model: {Creator.__tablename__}")
    print(f"✓ Video model: {Video.__tablename__}")
    print(f"✓ VideoAnalysis model: {VideoAnalysis.__tablename__}")
    print(f"✓ EngagementFeatures model: {EngagementFeatures.__tablename__}")
    print(f"✓ Prediction model: {Prediction.__tablename__}")
    print(f"✓ Embedding model: {Embedding.__tablename__}")
    print("\nAll models defined successfully!")
