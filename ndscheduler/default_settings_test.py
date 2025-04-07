"""Settings for unit tests."""

import logging

DEBUG = True

DATABASE_CLASS = "ndscheduler.corescheduler.datastore.providers.sqlite.DatastoreSqlite"
DATABASE_CONFIG_DICT = {
    # Use in-memory sqlite for unit tests
    "file_path": ":memory:",
    "echo": False,
    "future": True,  # Required for SQLAlchemy 2.0
    "pool_pre_ping": True,
}

# APScheduler settings for tests
JOB_DEFAULTS = {
    "coalesce": True,
    "max_instances": 1,
    "misfire_grace_time": 60,  # Shorter grace time for tests
}

EXECUTORS = {"default": {"type": "threadpool", "max_workers": 2}}  # Fewer workers for tests

# Disable most logging during tests
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
