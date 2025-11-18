"""
Agent 1: TikTok Data Collection Agent (Scraper).
Ethically scrapes TikTok data using TikTok-Api library with rate limiting.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import yt_dlp
import structlog

from agents.base import DatabaseAgent, RetryableAgent
from models.database_models import Creator, Video
from utils.rate_limiter import AdaptiveRateLimiter
from config.settings import get_settings

logger = structlog.get_logger(__name__)


class ScraperAgent(DatabaseAgent, RetryableAgent):
    """
    Agent for scraping TikTok creator profiles and video metadata.
    Implements rate limiting and error handling to avoid detection.
    """

    def __init__(self):
        DatabaseAgent.__init__(self, "scraper")
        RetryableAgent.__init__(self, "scraper")

        self.rate_limiter = AdaptiveRateLimiter()
        self.tiktok_api = None
        self._init_tiktok_api()

    def _init_tiktok_api(self):
        """Initialize TikTok API with authentication."""
        try:
            from TikTokApi import TikTokApi

            # Note: TikTok-Api setup varies by version
            # For now, we'll prepare the structure; actual implementation
            # depends on having ms_token configured

            ms_token = self.settings.TIKTOK_MS_TOKEN

            if not ms_token or ms_token == "":
                self.logger.warning(
                    "tiktok_api_not_configured",
                    message="TIKTOK_MS_TOKEN not set in .env - scraper will run in SAFE_MODE"
                )
                self.tiktok_api = None
                return

            # Initialize TikTok API
            # Note: Actual initialization depends on TikTok-Api version
            # This is a placeholder structure
            self.tiktok_api = {
                "ms_token": ms_token,
                "initialized": False,  # Will be set to True when actually configured
            }

            self.logger.info("tiktok_api_initialized")

        except ImportError as e:
            self.logger.error("tiktok_api_import_error", error=str(e))
            self.tiktok_api = None
        except Exception as e:
            self.logger.error("tiktok_api_init_error", error=str(e))
            self.tiktok_api = None

    def execute(self, creator_handle: str, max_videos: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute scraping for a single creator.

        Args:
            creator_handle: TikTok handle (with or without @)
            max_videos: Maximum videos to scrape (uses settings if None)

        Returns:
            Dict[str, Any]: Scraping results
        """
        # Normalize handle
        handle = creator_handle if creator_handle.startswith("@") else f"@{creator_handle}"
        max_videos = max_videos or self.settings.MAX_VIDEOS_PER_CREATOR

        self.logger.info(
            "scraper_starting",
            handle=handle,
            max_videos=max_videos
        )

        # Check if in safe mode
        if self.settings.SAFE_MODE or not self.tiktok_api:
            return self._execute_safe_mode(handle, max_videos)

        # Real scraping
        try:
            # Scrape creator profile
            creator_data = self._scrape_creator_profile(handle)

            if not creator_data:
                return {
                    "success": False,
                    "handle": handle,
                    "error": "Failed to fetch creator profile"
                }

            # Save creator to database
            creator = self._save_creator(creator_data)

            # Scrape videos
            videos_data = self._scrape_creator_videos(handle, max_videos)

            # Save videos to database
            saved_videos = []
            for video_data in videos_data:
                video = self._save_video(video_data, creator.creator_id)
                if video:
                    saved_videos.append(video)

            self.logger.info(
                "scraper_completed",
                handle=handle,
                creator_id=creator.creator_id,
                videos_scraped=len(saved_videos)
            )

            return {
                "success": True,
                "handle": handle,
                "creator_id": creator.creator_id,
                "videos_scraped": len(saved_videos),
                "metadata": {
                    "follower_count": creator.follower_count,
                    "total_videos": creator.total_videos,
                }
            }

        except Exception as e:
            self.logger.error(
                "scraper_error",
                handle=handle,
                error=str(e),
                exc_info=True
            )
            raise

    def _execute_safe_mode(self, handle: str, max_videos: int) -> Dict[str, Any]:
        """
        Execute scraper in safe mode with mock data.
        Used for testing without actual API calls.

        Args:
            handle: Creator handle
            max_videos: Number of mock videos

        Returns:
            Dict[str, Any]: Mock results
        """
        self.logger.info("scraper_safe_mode", handle=handle)

        # Create mock creator data
        mock_creator = {
            "handle": handle,
            "follower_count": 15000,
            "total_videos": 120,
            "bio": "Mock creator for testing",
            "verified": False,
            "niche": "fitness",
        }

        # Save to database and get creator_id
        creator = self._save_creator(mock_creator)
        creator_id = creator.creator_id  # Store ID before session closes
        follower_count = creator.follower_count
        total_videos = creator.total_videos

        # Create mock videos
        saved_videos = []
        for i in range(min(max_videos, 10)):
            mock_video = {
                "video_id": f"mock_video_{handle}_{i}",
                "upload_date": datetime.now(),
                "caption": f"Mock video {i+1}",
                "view_count": 50000 + (i * 10000),
                "like_count": 5000 + (i * 1000),
                "comment_count": 200 + (i * 50),
                "share_count": 100 + (i * 20),
                "duration_seconds": 30,
                "hashtags": ["fitness", "workout", "fyp"],
            }

            video = self._save_video(mock_video, creator_id)
            if video:
                saved_videos.append(video)

        return {
            "success": True,
            "handle": handle,
            "creator_id": creator_id,
            "videos_scraped": len(saved_videos),
            "safe_mode": True,
            "metadata": {
                "follower_count": follower_count,
                "total_videos": total_videos,
            }
        }

    def _scrape_creator_profile(self, handle: str) -> Optional[Dict[str, Any]]:
        """
        Scrape creator profile data from TikTok.

        Args:
            handle: Creator handle

        Returns:
            Optional[Dict[str, Any]]: Creator data or None
        """
        # Apply rate limiting
        self.rate_limiter.wait()

        try:
            # TODO: Actual TikTok API call here
            # This is a placeholder structure
            # Real implementation requires configured TikTok-Api

            self.logger.info("scraping_creator_profile", handle=handle)

            # Placeholder: In real implementation, this would be:
            # async with TikTokApi() as api:
            #     user = api.user(username=handle)
            #     user_data = await user.info()

            # For now, return None to indicate not implemented
            return None

        except Exception as e:
            self.logger.error(
                "scrape_profile_error",
                handle=handle,
                error=str(e)
            )
            self.rate_limiter.report_error(type(e).__name__)
            return None

    def _scrape_creator_videos(self, handle: str, max_videos: int) -> List[Dict[str, Any]]:
        """
        Scrape videos from creator.

        Args:
            handle: Creator handle
            max_videos: Maximum videos to fetch

        Returns:
            List[Dict[str, Any]]: List of video data
        """
        videos = []

        try:
            # TODO: Actual TikTok API call here
            # Placeholder structure

            self.logger.info(
                "scraping_creator_videos",
                handle=handle,
                max_videos=max_videos
            )

            # Apply rate limiting for each video fetch
            for i in range(max_videos):
                self.rate_limiter.wait()

                # Placeholder: Real implementation would fetch video data
                # For now, return empty list
                pass

            self.rate_limiter.report_success()

        except Exception as e:
            self.logger.error(
                "scrape_videos_error",
                handle=handle,
                error=str(e)
            )
            self.rate_limiter.report_error(type(e).__name__)

        return videos

    def _save_creator(self, creator_data: Dict[str, Any]) -> Creator:
        """
        Save or update creator in database.

        Args:
            creator_data: Creator data dictionary

        Returns:
            Creator: Saved creator object (detached from session)
        """
        with self.get_db_session() as db:
            # Check if creator exists
            existing = db.query(Creator).filter_by(handle=creator_data["handle"]).first()

            if existing:
                # Update existing creator
                for key, value in creator_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)

                existing.last_scraped_at = datetime.now()
                creator = existing

                self.logger.info(
                    "creator_updated",
                    handle=creator_data["handle"],
                    creator_id=creator.creator_id
                )
            else:
                # Create new creator
                creator = Creator(**creator_data)
                db.add(creator)
                db.flush()  # Get creator_id

                self.logger.info(
                    "creator_created",
                    handle=creator_data["handle"],
                    creator_id=creator.creator_id
                )

            # Access all attributes we need before session closes
            # This loads them so they're available after detachment
            _ = creator.creator_id
            _ = creator.follower_count
            _ = creator.total_videos

            # Detach from session so we can use it outside
            db.expunge(creator)

            return creator

    def _save_video(self, video_data: Dict[str, Any], creator_id: int) -> Optional[Video]:
        """
        Save video to database.

        Args:
            video_data: Video data dictionary
            creator_id: Creator ID foreign key

        Returns:
            Optional[Video]: Saved video object (detached) or None
        """
        try:
            with self.get_db_session() as db:
                # Check if video exists
                existing = db.query(Video).filter_by(video_id=video_data["video_id"]).first()

                if existing:
                    self.logger.debug(
                        "video_exists",
                        video_id=video_data["video_id"]
                    )
                    # Load attributes and detach
                    _ = existing.video_id
                    _ = existing.engagement_rate
                    db.expunge(existing)
                    return existing

                # Create new video
                video = Video(creator_id=creator_id, **video_data)

                # Calculate engagement rate (important for SQLite)
                video.engagement_rate = video.calculate_engagement_rate()

                db.add(video)
                db.flush()

                self.logger.debug(
                    "video_saved",
                    video_id=video_data["video_id"],
                    creator_id=creator_id
                )

                # Load attributes before detaching
                _ = video.video_id
                _ = video.engagement_rate
                db.expunge(video)

                return video

        except Exception as e:
            self.logger.error(
                "save_video_error",
                video_id=video_data.get("video_id"),
                error=str(e)
            )
            return None

    def download_video(self, video_url: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Download video using yt-dlp.

        Args:
            video_url: TikTok video URL
            output_path: Output directory (uses settings if None)

        Returns:
            Optional[str]: Path to downloaded video or None
        """
        output_path = output_path or self.settings.VIDEO_STORAGE_PATH
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Apply rate limiting
        self.rate_limiter.wait()

        try:
            ydl_opts = {
                'outtmpl': f'{output_path}/%(id)s.%(ext)s',
                'format': 'best',
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)

                self.logger.info(
                    "video_downloaded",
                    video_url=video_url,
                    output_file=filename
                )

                self.rate_limiter.report_success()
                return filename

        except Exception as e:
            self.logger.error(
                "download_video_error",
                video_url=video_url,
                error=str(e)
            )
            self.rate_limiter.report_error("download_error")
            return None


if __name__ == "__main__":
    # Test scraper agent
    print("Testing ScraperAgent...")

    agent = ScraperAgent()

    # Test in safe mode
    print("\nRunning in SAFE_MODE (no actual API calls)...")
    result = agent.run(creator_handle="@test_creator", max_videos=5)

    print(f"\nResult: {result}")
    print(f"\nAgent stats: {agent.get_stats()}")

    print("\n✓ Scraper agent test complete!")
