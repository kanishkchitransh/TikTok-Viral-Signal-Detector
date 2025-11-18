"""
Base agent class for TikTok Viral Signal Detector.
All agents inherit from this base class for common functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
from enum import Enum
import structlog

from config.settings import get_settings
from config.database import get_db_session
from utils.logging_config import log_agent_start, log_agent_complete, log_agent_error


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Provides common functionality for logging, error handling, and state management.
    """

    def __init__(self, name: str):
        """
        Initialize base agent.

        Args:
            name: Agent name (e.g., "scraper", "video_analyzer")
        """
        self.name = name
        self.status = AgentStatus.IDLE
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.name)

        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.error_count = 0
        self.success_count = 0
        self.retry_count = 0

        self.logger.info("agent_initialized", agent=self.name)

    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        Must be implemented by subclasses.

        Returns:
            Dict[str, Any]: Agent execution results
        """
        pass

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run the agent with error handling and logging.

        Args:
            *args: Positional arguments for execute()
            **kwargs: Keyword arguments for execute()

        Returns:
            Dict[str, Any]: Execution results including status and data
        """
        self.start_time = time.time()
        self.status = AgentStatus.RUNNING

        log_agent_start(self.logger, self.name, **kwargs)

        try:
            # Execute agent logic
            result = self.execute(*args, **kwargs)

            # Mark as successful
            self.status = AgentStatus.COMPLETED
            self.success_count += 1
            self.end_time = time.time()
            duration = self.end_time - self.start_time

            log_agent_complete(
                self.logger,
                self.name,
                duration=duration,
                **result.get("metadata", {})
            )

            return {
                "status": "success",
                "agent": self.name,
                "duration": duration,
                "data": result,
            }

        except Exception as e:
            # Mark as failed
            self.status = AgentStatus.FAILED
            self.error_count += 1
            self.end_time = time.time()
            duration = self.end_time - self.start_time if self.start_time else 0

            log_agent_error(self.logger, self.name, e, duration=duration)

            return {
                "status": "error",
                "agent": self.name,
                "duration": duration,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Returns:
            Dict[str, Any]: Agent performance statistics
        """
        return {
            "agent": self.name,
            "status": self.status.value,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "last_duration": self.end_time - self.start_time if self.start_time and self.end_time else None,
        }

    def reset(self):
        """Reset agent state."""
        self.status = AgentStatus.IDLE
        self.start_time = None
        self.end_time = None
        self.error_count = 0
        self.success_count = 0
        self.retry_count = 0

        self.logger.info("agent_reset", agent=self.name)

    def is_enabled(self) -> bool:
        """
        Check if this agent is enabled in configuration.

        Returns:
            bool: True if agent is enabled
        """
        # Map agent names to config flags
        agent_flags = {
            "scraper": self.settings.ENABLE_SCRAPER_AGENT,
            "video_analyzer": self.settings.ENABLE_VIDEO_ANALYSIS_AGENT,
            "engagement_analyzer": self.settings.ENABLE_ENGAGEMENT_AGENT,
            "predictor": self.settings.ENABLE_PREDICTION_AGENT,
            "report_generator": self.settings.ENABLE_REPORT_AGENT,
        }

        return agent_flags.get(self.name, True)

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')>"


class DatabaseAgent(BaseAgent):
    """
    Base class for agents that interact with the database.
    Provides database session management.
    """

    def __init__(self, name: str):
        super().__init__(name)

    def get_db_session(self):
        """
        Get database session context manager.

        Usage:
            with self.get_db_session() as db:
                db.query(Creator).all()
        """
        return get_db_session()

    def save_to_db(self, obj: Any, db_session: Any = None):
        """
        Save object to database.

        Args:
            obj: SQLAlchemy model instance
            db_session: Optional existing session, creates new if None
        """
        if db_session:
            db_session.add(obj)
            db_session.flush()
        else:
            with self.get_db_session() as db:
                db.add(obj)
                db.flush()

        self.logger.debug(
            "database_save",
            table=obj.__tablename__,
            object_id=getattr(obj, 'id', None)
        )


class RetryableAgent(BaseAgent):
    """
    Base class for agents that support automatic retries on failure.
    """

    def __init__(self, name: str, max_retries: Optional[int] = None):
        """
        Initialize retryable agent.

        Args:
            name: Agent name
            max_retries: Maximum retry attempts (uses settings if None)
        """
        super().__init__(name)
        self.max_retries = max_retries or self.settings.MAX_RETRY_ATTEMPTS
        self.retry_delay = 1  # Initial retry delay (seconds)

    def run_with_retry(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run agent with automatic retries on failure.

        Args:
            *args: Positional arguments for execute()
            **kwargs: Keyword arguments for execute()

        Returns:
            Dict[str, Any]: Execution results
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                self.status = AgentStatus.RETRYING
                self.retry_count = attempt

                # Exponential backoff
                wait_time = self.retry_delay * (self.settings.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))

                self.logger.warning(
                    "agent_retrying",
                    agent=self.name,
                    attempt=attempt,
                    max_retries=self.max_retries,
                    wait_time=wait_time
                )

                time.sleep(wait_time)

            # Try to run
            result = self.run(*args, **kwargs)

            if result["status"] == "success":
                return result
            else:
                last_error = result.get("error")

        # All retries failed
        self.logger.error(
            "agent_retries_exhausted",
            agent=self.name,
            attempts=self.max_retries + 1,
            last_error=last_error
        )

        return {
            "status": "error",
            "agent": self.name,
            "error": f"Failed after {self.max_retries + 1} attempts: {last_error}",
            "retries_exhausted": True,
        }


if __name__ == "__main__":
    # Test base agent
    class TestAgent(BaseAgent):
        def execute(self, test_param: str = "test"):
            self.logger.info("test_agent_executing", param=test_param)
            time.sleep(0.1)  # Simulate work
            return {
                "result": "success",
                "param": test_param,
                "metadata": {"items_processed": 42}
            }

    class TestRetryAgent(RetryableAgent):
        def __init__(self):
            super().__init__("test_retry", max_retries=3)
            self.attempt_count = 0

        def execute(self, should_fail: bool = False):
            self.attempt_count += 1
            if should_fail and self.attempt_count < 3:
                raise ValueError(f"Simulated failure (attempt {self.attempt_count})")
            return {"result": "success", "attempts": self.attempt_count}

    print("Testing BaseAgent...")
    agent = TestAgent("test_agent")
    result = agent.run(test_param="hello")
    print(f"Result: {result}")
    print(f"Stats: {agent.get_stats()}")

    print("\nTesting RetryableAgent (with failures)...")
    retry_agent = TestRetryAgent()
    result = retry_agent.run_with_retry(should_fail=True)
    print(f"Result: {result}")
    print(f"Stats: {retry_agent.get_stats()}")

    print("\n✓ Base agent tests complete!")
