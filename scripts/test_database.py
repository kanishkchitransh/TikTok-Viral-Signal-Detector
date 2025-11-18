#!/usr/bin/env python3
"""
Test database connection and operations.
Verifies PostgreSQL setup and ORM models.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from config.database import (
    check_connection,
    get_db_stats,
    get_db_session,
    init_db,
)
from config.settings import get_settings
from models.database_models import Creator, Video
import structlog

logger = structlog.get_logger(__name__)


def test_connection():
    """Test basic database connection."""
    print("=" * 70)
    print("TEST 1: Database Connection")
    print("=" * 70)

    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"Database: {settings.DB_NAME}")
    print()

    if check_connection():
        print("✓ Database connection successful!\n")
        return True
    else:
        print("✗ Database connection failed!")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running:")
        print("   sudo systemctl status postgresql")
        print("2. Verify credentials in .env file")
        print("3. Create database if it doesn't exist:")
        print(f"   createdb -U {settings.DB_USER} {settings.DB_NAME}")
        print()
        return False


def test_connection_pool():
    """Test connection pooling."""
    print("=" * 70)
    print("TEST 2: Connection Pool")
    print("=" * 70)

    stats = get_db_stats()
    print("Connection pool statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("\n✓ Connection pool working!\n")


def test_table_creation():
    """Test table creation."""
    print("=" * 70)
    print("TEST 3: Table Creation")
    print("=" * 70)

    try:
        init_db()
        print("✓ All tables created successfully!\n")
        return True
    except Exception as e:
        print(f"✗ Table creation failed: {e}\n")
        return False


def test_crud_operations():
    """Test CRUD operations on database."""
    print("=" * 70)
    print("TEST 4: CRUD Operations")
    print("=" * 70)

    try:
        with get_db_session() as db:
            # CREATE
            print("Testing CREATE...")
            creator = Creator(
                handle="@test_creator_db",
                follower_count=10000,
                total_videos=50,
                bio="Test creator for database testing",
                verified=False,
                niche="tech",
            )
            db.add(creator)
            db.flush()  # Get the ID
            creator_id = creator.creator_id
            print(f"  ✓ Created creator with ID: {creator_id}")

            # READ
            print("Testing READ...")
            fetched = db.query(Creator).filter_by(handle="@test_creator_db").first()
            assert fetched is not None, "Creator not found"
            assert fetched.follower_count == 10000, "Follower count mismatch"
            print(f"  ✓ Read creator: {fetched.handle}")

            # UPDATE
            print("Testing UPDATE...")
            fetched.follower_count = 15000
            db.flush()
            updated = db.query(Creator).filter_by(creator_id=creator_id).first()
            assert updated.follower_count == 15000, "Update failed"
            print(f"  ✓ Updated follower count to: {updated.follower_count}")

            # CREATE related Video
            print("Testing FOREIGN KEY relationship...")
            video = Video(
                video_id="test_video_123",
                creator_id=creator_id,
                upload_date=datetime.now(),
                caption="Test video",
                view_count=50000,
                like_count=5000,
                comment_count=200,
                share_count=100,
                duration_seconds=30,
                hashtags=["tech", "test"],
            )
            db.add(video)
            db.flush()
            print(f"  ✓ Created video: {video.video_id}")

            # Test engagement rate calculation
            print("Testing AUTO-CALCULATION (engagement_rate)...")
            assert video.engagement_rate > 0, "Engagement rate not calculated"
            print(f"  ✓ Engagement rate auto-calculated: {video.engagement_rate:.4f}")

            # DELETE
            print("Testing DELETE...")
            db.delete(video)
            db.delete(fetched)
            db.flush()

            # Verify deletion
            deleted_creator = db.query(Creator).filter_by(creator_id=creator_id).first()
            assert deleted_creator is None, "Delete failed"
            print("  ✓ Deleted creator and video")

        print("\n✓ All CRUD operations successful!\n")
        return True

    except Exception as e:
        print(f"\n✗ CRUD operations failed: {e}\n")
        logger.error("crud_test_failed", error=str(e), exc_info=True)
        return False


def test_constraints():
    """Test database constraints."""
    print("=" * 70)
    print("TEST 5: Constraints")
    print("=" * 70)

    try:
        with get_db_session() as db:
            # Test CHECK constraint (follower_count >= 0)
            print("Testing CHECK constraint (follower_count >= 0)...")
            try:
                bad_creator = Creator(
                    handle="@bad_creator",
                    follower_count=-100,  # Should fail
                )
                db.add(bad_creator)
                db.flush()
                print("  ✗ Check constraint not working (negative followers allowed)")
                return False
            except Exception:
                print("  ✓ Check constraint working (negative followers rejected)")

            # Test UNIQUE constraint
            print("Testing UNIQUE constraint (handle)...")
            creator1 = Creator(handle="@unique_test", follower_count=1000)
            db.add(creator1)
            db.flush()

            try:
                creator2 = Creator(handle="@unique_test", follower_count=2000)
                db.add(creator2)
                db.flush()
                print("  ✗ Unique constraint not working (duplicate handles allowed)")
                return False
            except Exception:
                print("  ✓ Unique constraint working (duplicate handles rejected)")
                db.rollback()

            # Clean up
            db.query(Creator).filter_by(handle="@unique_test").delete()

        print("\n✓ All constraints working!\n")
        return True

    except Exception as e:
        print(f"\n✗ Constraint tests failed: {e}\n")
        return False


def test_indexes():
    """Test that indexes exist."""
    print("=" * 70)
    print("TEST 6: Indexes")
    print("=" * 70)

    try:
        with get_db_session() as db:
            # Query to check indexes
            result = db.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename IN ('creators', 'videos')
                ORDER BY indexname;
            """)

            indexes = [row[0] for row in result]

            expected_indexes = [
                'idx_creator_handle',
                'idx_video_creator',
                'idx_video_engagement_rate',
            ]

            print("Found indexes:")
            for idx in indexes:
                print(f"  - {idx}")

            missing = [idx for idx in expected_indexes if idx not in indexes]
            if missing:
                print(f"\n⚠ Missing indexes: {missing}")
            else:
                print("\n✓ All expected indexes present!")

        print()
        return True

    except Exception as e:
        print(f"\n✗ Index check failed: {e}\n")
        return False


def run_all_tests():
    """Run all database tests."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  DATABASE TEST SUITE".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()

    results = []

    # Test 1: Connection
    results.append(("Connection", test_connection()))

    if not results[-1][1]:
        print("\n❌ Database connection failed. Fix connection before proceeding.\n")
        return False

    # Test 2: Connection Pool
    try:
        test_connection_pool()
        results.append(("Connection Pool", True))
    except Exception as e:
        print(f"Connection pool test failed: {e}\n")
        results.append(("Connection Pool", False))

    # Test 3: Table Creation
    results.append(("Table Creation", test_table_creation()))

    # Test 4: CRUD Operations
    results.append(("CRUD Operations", test_crud_operations()))

    # Test 5: Constraints
    results.append(("Constraints", test_constraints()))

    # Test 6: Indexes
    results.append(("Indexes", test_indexes()))

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
        print("\n🎉 All tests passed! Database is ready.\n")
        return True
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please fix the issues.\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
