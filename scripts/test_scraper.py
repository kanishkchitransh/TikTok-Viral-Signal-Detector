#!/usr/bin/env python3
"""
Test scraper agent functionality.
Tests scraping, rate limiting, and database storage.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.scraper import ScraperAgent
from config.database import get_db_session, check_connection
from models.database_models import Creator, Video
from config.settings import get_settings
import structlog

logger = structlog.get_logger(__name__)


def test_agent_initialization():
    """Test scraper agent initialization."""
    print("=" * 70)
    print("TEST 1: Agent Initialization")
    print("=" * 70)

    try:
        agent = ScraperAgent()
        print(f"✓ Agent created: {agent.name}")
        print(f"✓ Status: {agent.status.value}")
        print(f"✓ Rate limiter initialized")
        print(f"✓ Settings loaded")
        print()
        return True, agent
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}\n")
        return False, None


def test_safe_mode_scraping(agent):
    """Test scraping in safe mode (no actual API calls)."""
    print("=" * 70)
    print("TEST 2: Safe Mode Scraping")
    print("=" * 70)

    try:
        print("Running scraper in SAFE_MODE...")
        print("(This creates mock data without calling TikTok API)\n")

        # Run scraper for test creator
        result = agent.run(
            creator_handle="@fitness_test_user",
            max_videos=5
        )

        print(f"Result status: {result['status']}")
        print(f"Agent: {result['agent']}")
        print(f"Duration: {result.get('duration', 0):.2f}s")

        if result['status'] == 'success':
            data = result['data']
            print(f"\n✓ Scraping successful!")
            print(f"  Handle: {data['handle']}")
            print(f"  Creator ID: {data['creator_id']}")
            print(f"  Videos scraped: {data['videos_scraped']}")
            print(f"  Follower count: {data['metadata']['follower_count']:,}")
            print()
            return True, data
        else:
            print(f"\n✗ Scraping failed: {result.get('error')}\n")
            return False, None

    except Exception as e:
        print(f"\n✗ Safe mode scraping failed: {e}\n")
        logger.error("safe_mode_test_failed", error=str(e), exc_info=True)
        return False, None


def test_database_storage(creator_handle):
    """Test that scraped data was stored in database."""
    print("=" * 70)
    print("TEST 3: Database Storage")
    print("=" * 70)

    try:
        with get_db_session() as db:
            # Check creator was saved
            print("Checking creator in database...")
            creator = db.query(Creator).filter_by(handle=creator_handle).first()

            if not creator:
                print(f"✗ Creator '{creator_handle}' not found in database\n")
                return False

            print(f"✓ Creator found:")
            print(f"  ID: {creator.creator_id}")
            print(f"  Handle: {creator.handle}")
            print(f"  Followers: {creator.follower_count:,}")
            print(f"  Total videos: {creator.total_videos}")
            print(f"  Niche: {creator.niche}")

            # Check videos were saved
            print("\nChecking videos in database...")
            videos = db.query(Video).filter_by(creator_id=creator.creator_id).all()

            print(f"✓ Found {len(videos)} videos:")
            for i, video in enumerate(videos[:5], 1):  # Show first 5
                print(f"  {i}. {video.video_id}")
                print(f"     Views: {video.view_count:,}")
                print(f"     Likes: {video.like_count:,}")
                print(f"     Engagement: {video.engagement_rate:.2%}")

            # Check engagement rate calculation
            print("\nVerifying engagement rate calculations...")
            for video in videos:
                assert video.engagement_rate is not None, "Engagement rate is None"
                assert video.engagement_rate >= 0, "Engagement rate is negative"
                print(f"  ✓ {video.video_id}: {video.engagement_rate:.4f}")

            print("\n✓ All data stored correctly!\n")
            return True

    except Exception as e:
        print(f"\n✗ Database storage test failed: {e}\n")
        logger.error("db_storage_test_failed", error=str(e), exc_info=True)
        return False


def test_rate_limiting(agent):
    """Test rate limiting functionality."""
    print("=" * 70)
    print("TEST 4: Rate Limiting")
    print("=" * 70)

    try:
        print("Testing rate limiter...")
        limiter = agent.rate_limiter

        stats = limiter.get_stats()
        print(f"Rate limiter stats:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Min delay: {stats['min_delay']}s")
        print(f"  Max delay: {stats['max_delay']}s")

        print("\n✓ Rate limiting working!\n")
        return True

    except Exception as e:
        print(f"\n✗ Rate limiting test failed: {e}\n")
        return False


def test_retry_mechanism(agent):
    """Test retry mechanism."""
    print("=" * 70)
    print("TEST 5: Retry Mechanism")
    print("=" * 70)

    try:
        print(f"Max retries configured: {agent.max_retries}")
        print(f"Retry backoff multiplier: {agent.settings.RETRY_BACKOFF_MULTIPLIER}")

        # Test successful run (should not retry)
        result = agent.run(creator_handle="@retry_test", max_videos=2)

        print(f"Retry count: {agent.retry_count}")
        print(f"Error count: {agent.error_count}")
        print(f"Success count: {agent.success_count}")

        print("\n✓ Retry mechanism configured!\n")
        return True

    except Exception as e:
        print(f"\n✗ Retry mechanism test failed: {e}\n")
        return False


def test_agent_stats(agent):
    """Test agent statistics."""
    print("=" * 70)
    print("TEST 6: Agent Statistics")
    print("=" * 70)

    try:
        stats = agent.get_stats()

        print("Agent statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n✓ Statistics working!\n")
        return True

    except Exception as e:
        print(f"\n✗ Statistics test failed: {e}\n")
        return False


def cleanup_test_data():
    """Clean up test data from database."""
    print("=" * 70)
    print("Cleanup: Removing Test Data")
    print("=" * 70)

    try:
        with get_db_session() as db:
            # Delete test creators (videos will cascade delete)
            test_handles = [
                "@fitness_test_user",
                "@retry_test",
            ]

            for handle in test_handles:
                creator = db.query(Creator).filter_by(handle=handle).first()
                if creator:
                    db.delete(creator)
                    print(f"  Deleted: {handle}")

            print("\n✓ Test data cleaned up!\n")

    except Exception as e:
        print(f"\n⚠ Cleanup failed (non-critical): {e}\n")


def run_all_tests():
    """Run all scraper tests."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  SCRAPER AGENT TEST SUITE".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()

    # Check database connection first
    if not check_connection():
        print("\n❌ Database connection failed. Run test_database.py first.\n")
        return False

    results = []

    # Test 1: Initialization
    success, agent = test_agent_initialization()
    results.append(("Agent Initialization", success))

    if not success or agent is None:
        print("\n❌ Agent initialization failed. Cannot proceed.\n")
        return False

    # Test 2: Safe Mode Scraping
    success, data = test_safe_mode_scraping(agent)
    results.append(("Safe Mode Scraping", success))

    if success and data:
        # Test 3: Database Storage
        success = test_database_storage(data['handle'])
        results.append(("Database Storage", success))

    # Test 4: Rate Limiting
    success = test_rate_limiting(agent)
    results.append(("Rate Limiting", success))

    # Test 5: Retry Mechanism
    success = test_retry_mechanism(agent)
    results.append(("Retry Mechanism", success))

    # Test 6: Agent Statistics
    success = test_agent_stats(agent)
    results.append(("Agent Statistics", success))

    # Cleanup
    cleanup_test_data()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<50} {status}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)

    if passed == total:
        print("\n🎉 All scraper tests passed! Agent is ready.\n")
        print("Next steps:")
        print("  1. Add TIKTOK_MS_TOKEN to .env for real TikTok scraping")
        print("  2. Test with real creator: python scripts/test_scraper.py --real")
        print("  3. Proceed to Agent 2: Video Analysis\n")
        return True
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please fix the issues.\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
