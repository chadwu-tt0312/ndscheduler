"""Unit tests for the SQLite async datastore provider."""

import os
import pytest
import pytest_asyncio
import datetime
import pytz
import asyncio
import uuid

from ndscheduler.corescheduler.datastore.providers import sqlite
from ndscheduler.corescheduler import constants

# Test database file path
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_async.db")


@pytest_asyncio.fixture(scope="function")
async def sqlite_store():
    """Create a test SQLite store."""
    # Remove the test database file if it exists
    max_retries = 5
    retry_delay = 0.2

    for _ in range(max_retries):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
                break
            except PermissionError:
                await asyncio.sleep(retry_delay)
        else:
            break

    # Setup
    store = sqlite.DatastoreSqlite.get_instance({"file_path": TEST_DB_PATH})
    yield store

    # Cleanup
    await store.destroy_instance()

    # Remove the test database file
    for _ in range(max_retries):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
                break
            except PermissionError:
                await asyncio.sleep(retry_delay)
        else:
            break


@pytest.mark.asyncio
async def test_execution_crud(sqlite_store):
    """Test Create/Read/Update/Delete operations for executions."""
    # Test data
    execution_id = f"test_execution_{uuid.uuid4()}"
    job_id = "test_job_1"
    state = constants.EXECUTION_STATUS_SCHEDULED  # Use the constant directly
    hostname = "test_host"
    pid = 12345
    now = datetime.datetime.now(pytz.utc)

    # Test Create
    await sqlite_store.add_execution(
        execution_id=execution_id,
        job_id=job_id,
        state=state,
        hostname=hostname,
        pid=pid,
        scheduled_time=now,
        updated_time=now,
    )

    # Test Read
    execution = await sqlite_store.get_execution(execution_id)
    assert execution is not None
    assert execution["execution_id"] == execution_id
    assert execution["state"] == constants.EXECUTION_STATUS_DICT[state]
    assert execution["hostname"] == hostname
    assert execution["pid"] == pid

    # Test Update
    new_state = constants.EXECUTION_STATUS_RUNNING
    await sqlite_store.update_execution(execution_id, state=new_state)

    updated_execution = await sqlite_store.get_execution(execution_id)
    assert updated_execution["state"] == constants.EXECUTION_STATUS_DICT[new_state]


@pytest.mark.asyncio
async def test_get_executions(sqlite_store):
    """Test getting multiple executions within a time range."""
    # Add test executions
    now = datetime.datetime.now(pytz.utc)
    one_hour_ago = now - datetime.timedelta(hours=1)
    one_hour_later = now + datetime.timedelta(hours=1)

    # Add three executions
    for i in range(3):
        await sqlite_store.add_execution(
            execution_id=f"test_execution_{uuid.uuid4()}",
            job_id=f"test_job_{i}",
            state=constants.EXECUTION_STATUS_SCHEDULED,
            hostname="test_host",
            scheduled_time=now,
            updated_time=now,
        )

    # Test getting executions within time range
    executions = await sqlite_store.get_executions(
        one_hour_ago.isoformat(), one_hour_later.isoformat()
    )

    assert executions is not None
    assert "executions" in executions
    assert len(executions["executions"]) == 3


@pytest.mark.asyncio
async def test_audit_log_crud(sqlite_store):
    """Test Create/Read operations for audit logs."""
    # Test data
    job_id = "test_job_1"
    job_name = "Test Job"
    event = constants.AUDIT_LOG_ADDED
    user = "test_user"
    description = "Test audit log"

    # Test Create
    await sqlite_store.add_audit_log(
        job_id=job_id, job_name=job_name, event=event, user=user, description=description
    )

    # Test Read
    now = datetime.datetime.now(pytz.utc)
    one_hour_ago = now - datetime.timedelta(hours=1)
    one_hour_later = now + datetime.timedelta(hours=1)

    logs = await sqlite_store.get_audit_logs(one_hour_ago.isoformat(), one_hour_later.isoformat())

    assert logs is not None
    assert "logs" in logs
    assert len(logs["logs"]) > 0

    log = logs["logs"][0]
    assert log["job_id"] == job_id
    assert log["job_name"] == job_name
    assert log["user"] == user
    assert log["description"] == description


@pytest.mark.asyncio
async def test_time_format_handling(sqlite_store):
    """Test time format handling for both sync and async operations."""
    # Test string time (sync operation simulation)
    time_str = "2024-01-01 12:00:00.000000"
    iso_time = sqlite_store.get_time_isoformat_from_db(time_str)
    assert "T" in iso_time  # ISO format contains 'T' between date and time
    assert iso_time.endswith("+00:00")  # UTC timezone

    # Test datetime object (async operation simulation)
    now = datetime.datetime.now()
    iso_time = sqlite_store.get_time_isoformat_from_db(now)
    assert "T" in iso_time
    assert iso_time.endswith("+00:00")  # UTC timezone
