
## setup (origin)

1. uv venv --python=3.9
2. export NDSCHEDULER_SETTINGS_MODULE=simple_scheduler.settings
3. export PYTHONPATH=.
4. fix makefile
5. simple_scheduler/requirements.txt fix (mark git)
6. simple_scheduler/scheduler.py fix (Fix for Tornado+asyncio on Windows)
7. add requirements.txt
    - tornado>=6.4.2
    - SQLAlchemy>=2.0.39
    - apscheduler>=3.11.0
    - future>=0.18.3
    - python-dateutil>=2.8.2
    - pytz>=2025.2
8. uv pip install -r requirements.txt
9. (X)uv pip install setuptools
10. (X)uv run setup.py install
11. make simple
12. uv pip install -e .
13. uv run simple_scheduler/scheduler.py

## setup (origin-new)

1. uv venv --python=3.11
2. source .venv/Scripts/activate
3. uv pip install -r requirements.txt
4. uv pip install -e . --no-cache-dir --force-reinstall

## setup (palto42)

1. uv venv --python=3.11
2. source .venv/Scripts/activate
3. export NDSCHEDULER_SETTINGS_MODULE=simple_scheduler.settings
4. export PYTHONPATH=.
5. uv pip install setuptools
6. uv pip install ldap/python_ldap-3.4.4-cp311-cp311-win_amd64.whl
7. fix makefile/setup.cfg/setup.py
8. add test_requirements.txt
    - pytz>=2025.2
9. uv pip install -r test_requirements.txt
10. make install
11. make test
12. del build/dist/doc/ndscheduler.egg-info path
13. uv pip install -e .
14. uv run simple_scheduler/scheduler.py

## update to python 3.11 (origin)

1. Tornado 相關更新
    - ...
2. SQLAlchemy 相關更新
    - ...
3. APScheduler 相關更新
    - n/a
4. del .venv/
    - close IDE and open cmd to run
5. uv venv --python=3.11
6. .venv/Scripts/activate
7. uv pip install -r requirements.txt
8. fix setup.py
9. uv pip install -e .

## RUN(old)

1. export NDSCHEDULER_SETTINGS_MODULE=simple_scheduler.settings
2. export PYTHONPATH=.
3. uv run simple_scheduler/scheduler.py

## RUN

1. uv run simple_scheduler/scheduler.py

## Memo (origin)

1. 確保 Python 能夠正確找到並載入 simple_scheduler 模組。
    - uv run -m simple_scheduler.scheduler
    - 設定 PYTHONPATH (export PYTHONPATH=.)
2. DB tablename
    - DEFAULT_JOBS_TABLENAME = 'scheduler_jobs'
    - DEFAULT_EXECUTIONS_TABLENAME = 'scheduler_execution'
    - DEFAULT_AUDIT_LOGS_TABLENAME = 'scheduler_jobauditlog'
3. AUDIT_LOGS 只儲存 job 變更紀錄，EXECUTIONS 只儲存 job 執行紀錄。
4. DEFAULT_TIMEZONE = 'UTC'
5. NDSCHEDULER_SETTINGS_MODULE=simple_scheduler.settings 用來決定要載入哪個設定檔。當這個環境變數沒有設定時，系統會使用預設設定（default_settings.py），而不是我們的自定義設定（simple_scheduler/settings.py）。在預設設定中，HTTP_PORT 被設定為 7777。
6. move base_test.py
    - from `\ndscheduler\corescheduler\datastore\base_test.py`
    - to `\tests\ndscheduler\corescheduler\datastore\test_base.py`
7. move another *_test.py
8. htpasswd -nbB username password
9. 在執行 pip install -e . 時，Python 套件安裝系統可能使用的是安裝前已經緩存的元數據，或者是已經解析過的套件信息。所以需要"清除構建緩存"
    - uv pip install -e . --no-cache-dir --force-reinstall
10. 使用 u02 API call。只能看到 u02 相關資料。使用 admin API call 可以看到全部。(04-25 chg user to admin)
11. chrome browser 執行檔在 `C:\Users\chad\AppData\Local\ms-playwright\chromium-1161\chrome-win`
    - install path `C:\Users\chad\AppData\Local\ms-playwright\chromium-1161`
12. test_web_ui_integration.py test_03_add_job()=fail
    - select Job Class

### cUrl

```bash
curl -X POST http://localhost:8888/api/v1/auth/login 
  -H 'Content-Type: application/json' 
  -d '{
    "username": "admin",
    "password": "password"
  }'

curl -X POST http://localhost:8888/api/v1/jobs 
  -H 'Content-Type: application/json' 
  -H 'Authorization: Bearer {{LOGIN_TOKEN}}' 
  -d '{
    "job_class_string": "simple_scheduler.jobs.sample_job.AwesomeJob",
    "name": "API 新增的任務",
    "pub_args": ["API參數1", "API參數2"],
    "minute": "*/5"
  }'
```

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
    category_id INTEGER,
    created_time DATETIME NOT NULL, 
    description TEXT
)

CREATE TABLE scheduler_execution (
    eid VARCHAR(191) NOT NULL, 
    hostname TEXT, 
    pid INTEGER, 
    state INTEGER NOT NULL,
    category_id INTEGER, 
    scheduled_time DATETIME NOT NULL, 
    updated_time DATETIME, 
    description TEXT, 
    result TEXT, 
    job_id TEXT NOT NULL, 
    task_id TEXT, 
    PRIMARY KEY (eid)
)

CREATE TABLE scheduler_job_categories (
    job_id VARCHAR(191) NOT NULL, 
    category_id INTEGER NOT NULL, 
    created_at DATETIME NOT NULL, 
    PRIMARY KEY (job_id), 
    FOREIGN KEY(category_id) REFERENCES scheduler_categories (id)
)

CREATE TABLE scheduler_users (
    id INTEGER NOT NULL, 
    username VARCHAR(50) NOT NULL, 
    password VARCHAR(255) NOT NULL, 
    category_id INTEGER, 
    is_admin BOOLEAN, 
    is_permission BOOLEAN, 
    created_at DATETIME NOT NULL, 
    updated_at DATETIME, 
    PRIMARY KEY (id), 
    UNIQUE (username), 
    FOREIGN KEY(category_id) REFERENCES scheduler_categories (id)
)

CREATE TABLE scheduler_categories (
    id INTEGER NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    description TEXT, 
    created_at DATETIME NOT NULL, 
    updated_at DATETIME, 
    PRIMARY KEY (id), 
    UNIQUE (name)
)
```

### cmd (origin)

```cmd
netstat -ano | findstr :8888

# pytest
uv pip install pytest pytest_asyncio
pytest tests/test_main.py -v
pytest tests/ndscheduler/corescheduler/datastore/test_base.py -v
# pytest ndscheduler/server/handlers/executions_test.py -v
pytest tests/test_api_integration.py -v
pytest tests/test_api_integration.py::TestAPIIntegration::test_06_user_lifecycle -v
pytest tests/test_web_ui_integration.py --headed -v
pytest tests/test_web_ui_integration.py::TestWebUIIntegration::test_01_login --headed -v

# temp
pytest tests/corescheduler/datastore/providers/test_sqlite_async.py -v
pytest tests/integration/test_server.py -v
pytest tests/integration/test_server.py -vv -s
```

### Issue

1. settting 中的 DEBUG = False 時需要將所有前端的 console.log() 紀錄關閉，DEBUG = True 時才開啟 console.log() 紀錄。因此需要將 setting 的 DEBUG flag 傳遞給前端。
    - 兩次修改都失敗
