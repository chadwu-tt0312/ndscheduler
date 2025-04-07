
## setup

1. uv venv (--python=3.9)
2. export NDSCHEDULER_SETTINGS_MODULE=simple_scheduler.settings
3. makefile fix
4. simple_scheduler/requirements.txt fix (mark git)
5. simple_scheduler/scheduler.py fix (Fix for Tornado+asyncio on Windows)
6. add requirements.txt
   - APScheduler>=3.0.0
   - SQLAlchemy>=1.0.0
   - future>=0.15.2
   - tornado<6
   - python-dateutil>=2.2
7. uv pip install -r requirements.txt
8. (X)uv pip install setuptools
9. (X)uv run setup.py install
10. make simple
11. uv pip install -e .
12. uv run simple_scheduler/scheduler.py

## RUN

1. export NDSCHEDULER_SETTINGS_MODULE=simple_scheduler.settings
2. uv run simple_scheduler/scheduler.py

## Memo

1. DB tablename
   - DEFAULT_JOBS_TABLENAME = 'scheduler_jobs'
   - DEFAULT_EXECUTIONS_TABLENAME = 'scheduler_execution'
   - DEFAULT_AUDIT_LOGS_TABLENAME = 'scheduler_jobauditlog'
2. AUDIT_LOGS 只儲存 job 變更紀錄，EXECUTIONS 只儲存 job 執行紀錄。
3. DEFAULT_TIMEZONE = 'UTC'
4. NDSCHEDULER_SETTINGS_MODULE=simple_scheduler.settings 用來決定要載入哪個設定檔。當這個環境變數沒有設定時，系統會使用預設設定（default_settings.py），而不是我們的自定義設定（simple_scheduler/settings.py）。在預設設定中，HTTP_PORT 被設定為 7777。

### DDL (datastore.db)

```SQL
CREATE TABLE scheduler_jobs (
    id VARCHAR(191) NOT NULL, 
    next_run_time FLOAT, 
    job_state BLOB NOT NULL, 
    PRIMARY KEY (id)
)

CREATE TABLE scheduler_jobauditlog (
    job_id TEXT NOT NULL, 
    job_name TEXT NOT NULL, 
    event INTEGER NOT NULL, 
    user TEXT, 
    created_time DATETIME NOT NULL, 
    description TEXT
)

CREATE TABLE scheduler_execution (
    eid VARCHAR(191) NOT NULL, 
    hostname TEXT, 
    pid INTEGER, 
    state INTEGER NOT NULL, 
    scheduled_time DATETIME NOT NULL, 
    updated_time DATETIME, 
    description TEXT, 
    result TEXT, 
    job_id TEXT NOT NULL, 
    task_id TEXT, 
    PRIMARY KEY (eid)
)
```

### cmd

```cmd
netstat -ano | findstr :8888

# pytest
uv pip install pytest pytest_asyncio
pytest tests/test_main.py -v
pytest tests/corescheduler/datastore/providers/test_sqlite_async.py -v
pytest tests/integration/test_server.py -v
pytest tests/integration/test_server.py -vv -s
```
