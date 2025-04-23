# ndscheduler API 呼叫列表

## 目錄
- [身份驗證](#身份驗證)
- [作業管理](#作業管理)
- [執行記錄](#執行記錄)
- [稽核日誌](#稽核日誌)
- [分類管理](#分類管理)
- [用戶管理](#用戶管理)

## 身份驗證

### 登入

**URL**: `/api/v1/auth/login`

**方法**: `POST`

**請求內容**:
```json
{
    "username": "user",
    "password": "password"
}
```

**成功回應**:
```json
{
    "token": "JWT_TOKEN",
    "user": {
        "id": "使用者ID",
        "username": "使用者名稱",
        "category_id": "分類ID",
        "is_admin": true,
        "is_permission": true
    }
}
```

### 驗證身份

**URL**: `/api/v1/auth/verify`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "user": {
        "id": "使用者ID",
        "username": "使用者名稱",
        "category_id": "分類ID",
        "is_admin": true,
        "is_permission": true
    }
}
```

## 作業管理

### 獲取所有作業

**URL**: `/api/v1/jobs`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "jobs": [
        {
            "job_id": "d8f376e858a411e4b6ae22000ac58d05",
            "job_class_string": "simple_scheduler.jobs.clean_apns.CleanAPNsJob",
            "name": "Clean APNs",
            "pub_args": ["arg1", "arg2"],
            "month": "*",
            "day_of_week": "*",
            "day": "*",
            "hour": "*/1",
            "minute": "*"
        },
        ...
    ]
}
```

### 獲取單個作業

**URL**: `/api/v1/jobs/{job_id}`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "job_id": "d8f376e858a411e4b6ae22000ac58d05",
    "job_class_string": "simple_scheduler.jobs.clean_apns.CleanAPNsJob",
    "name": "Clean APNs",
    "pub_args": ["arg1", "arg2"],
    "month": "*",
    "day_of_week": "*",
    "day": "*",
    "hour": "*/1",
    "minute": "*"
}
```

### 新增作業

**URL**: `/api/v1/jobs`

**方法**: `POST`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
Content-Type: application/json
```

**請求內容**:
```json
{
    "job_class_string": "simple_scheduler.jobs.sample_job.AwesomeJob",
    "name": "API 新增的任務",
    "pub_args": ["API參數1", "API參數2"],
    "minute": "*/5",
    "month": "*",
    "day_of_week": "*",
    "day": "*",
    "hour": "*"
}
```

**成功回應**:
```json
{
    "job_id": "d8f376e858a411e4b6ae32000ac58d05"
}
```

### 修改作業

**URL**: `/api/v1/jobs/{job_id}`

**方法**: `PUT`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
Content-Type: application/json
```

**請求內容**:
```json
{
    "job_class_string": "simple_scheduler.jobs.sample_job.AwesomeJob",
    "name": "API 修改的任務",
    "pub_args": ["API參數1", "API參數2"],
    "minute": "*/10",
    "month": "*",
    "day_of_week": "*",
    "day": "*",
    "hour": "*"
}
```

**成功回應**:
```json
{
    "job_id": "d8f376e858a411e4b6ae22000ac58d05"
}
```

### 刪除作業

**URL**: `/api/v1/jobs/{job_id}`

**方法**: `DELETE`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "job_id": "d8f376e858a411e4b6ae22000ac58d05"
}
```

### 暫停作業

**URL**: `/api/v1/jobs/{job_id}`

**方法**: `PATCH`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "job_id": "d8f376e858a411e4b6ae22000ac58d05"
}
```

### 恢復作業

**URL**: `/api/v1/jobs/{job_id}`

**方法**: `OPTIONS`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "job_id": "d8f376e858a411e4b6ae22000ac58d05"
}
```

## 執行記錄

### 獲取指定時間範圍內的執行記錄

**URL**: `/api/v1/executions?time_range_start={start_time}&time_range_end={end_time}`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**請求參數**:
- `time_range_start`: ISO格式的開始時間，例如 `2023-01-01T00:00:00.000Z`
- `time_range_end`: ISO格式的結束時間，例如 `2023-01-02T00:00:00.000Z`

**成功回應**:
```json
{
    "executions": [
        {
            "description": "",
            "execution_id": "7252d7a6a80f11e58bcc02ba903740c3",
            "hostname": "",
            "job": {
                "day": "*",
                "day_of_week": "*",
                "hour": "*",
                "job_id": "bb0dec52797f11e4a14122000a150f89",
                "minute": "*/5",
                "month": "*",
                "name": "Poll sendgrid for bounces and spamreports",
                "pub_args": [],
                "job_class_string": "simple_scheduler.jobs.sample_job.ImportDataJob",
                "week": "*"
            },
            "pid": -1,
            "scheduled_time": "2023-01-01T18:20:05.604708+00:00",
            "state": "scheduled",
            "task_id": "",
            "updated_time": "2023-01-01T18:20:05.604732+00:00"
        },
        ...
    ]
}
```

### 獲取單個執行記錄

**URL**: `/api/v1/executions/{execution_id}`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "description": "",
    "execution_id": "7252d7a6a80f11e58bcc02ba903740c3",
    "hostname": "",
    "job": {
        "day": "*",
        "day_of_week": "*",
        "hour": "*",
        "job_id": "bb0dec52797f11e4a14122000a150f89",
        "minute": "*/5",
        "month": "*",
        "name": "Poll sendgrid for bounces and spamreports",
        "pub_args": [],
        "job_class_string": "simple_scheduler.jobs.sample_job.ImportDataJob",
        "week": "*"
    },
    "pid": -1,
    "scheduled_time": "2023-01-01T18:20:05.604708+00:00",
    "state": "scheduled",
    "task_id": "",
    "updated_time": "2023-01-01T18:20:05.604732+00:00"
}
```

### 立即執行作業

**URL**: `/api/v1/executions/{job_id}`

**方法**: `POST`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "execution_id": "d8f376e858a411e4b6ae32000ac58d05"
}
```

## 稽核日誌

### 獲取稽核日誌

**URL**: `/api/v1/logs?time_range_start={start_time}&time_range_end={end_time}`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**請求參數**:
- `time_range_start`: ISO格式的開始時間，例如 `2023-01-01T00:00:00.000Z`
- `time_range_end`: ISO格式的結束時間，例如 `2023-01-02T00:00:00.000Z`

**成功回應**:
```json
{
    "logs": [
        {
            "job_id": "5052939245f611e5bef70610a8516d8b",
            "job_name": "Import Data Job",
            "event": "custom_run",
            "user": "admin",
            "description": "ad9bb256a2ee11e5bbf702ba903740c3",
            "created_time": "2023-01-01T01:20:23.843895+00:00"
        },
        ...
    ],
    "total": 10
}
```

## 分類管理

### 獲取所有分類

**URL**: `/api/v1/categories`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "categories": [
        {
            "id": 1,
            "name": "系統管理",
            "description": "系統管理類別的任務",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z"
        },
        ...
    ]
}
```

### 獲取單個分類

**URL**: `/api/v1/categories/{category_id}`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "id": 1,
    "name": "系統管理",
    "description": "系統管理類別的任務",
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z"
}
```

### 新增分類

**URL**: `/api/v1/categories`

**方法**: `POST`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
Content-Type: application/json
```

**請求內容**:
```json
{
    "name": "新分類名稱",
    "description": "新分類的描述"
}
```

**成功回應**:
```json
{
    "id": 2
}
```

### 修改分類

**URL**: `/api/v1/categories/{category_id}`

**方法**: `PUT`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
Content-Type: application/json
```

**請求內容**:
```json
{
    "name": "修改後的分類名稱",
    "description": "修改後的分類描述"
}
```

**成功回應**:
```json
{
    "id": 2
}
```

### 刪除分類

**URL**: `/api/v1/categories/{category_id}`

**方法**: `DELETE`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "id": 2
}
```

## 用戶管理

### 獲取所有用戶

**URL**: `/api/v1/users`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "users": [
        {
            "id": 1,
            "username": "admin",
            "category_id": 0,
            "is_admin": true,
            "is_permission": true,
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z"
        },
        ...
    ]
}
```

### 獲取單個用戶

**URL**: `/api/v1/users/{user_id}`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "id": 1,
    "username": "admin",
    "category_id": 0,
    "is_admin": true,
    "is_permission": true,
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z"
}
```

### 獲取當前用戶信息

**URL**: `/api/v1/users/current`

**方法**: `GET`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "id": 1,
    "username": "admin",
    "category_id": 0,
    "is_admin": true,
    "is_permission": true,
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z"
}
```

### 新增用戶

**URL**: `/api/v1/users`

**方法**: `POST`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
Content-Type: application/json
```

**請求內容**:
```json
{
    "username": "新用戶名稱",
    "password": "密碼",
    "category_id": 1,
    "is_admin": false,
    "is_permission": true
}
```

**成功回應**:
```json
{
    "id": 2
}
```

### 修改用戶

**URL**: `/api/v1/users/{user_id}`

**方法**: `PUT`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
Content-Type: application/json
```

**請求內容**:
```json
{
    "username": "修改後的用戶名稱",
    "password": "新密碼",
    "category_id": 2,
    "is_admin": true,
    "is_permission": true
}
```

**成功回應**:
```json
{
    "id": 2
}
```

### 刪除用戶

**URL**: `/api/v1/users/{user_id}`

**方法**: `DELETE`

**請求標頭**:
```
Authorization: Bearer JWT_TOKEN
```

**成功回應**:
```json
{
    "id": 2
}
```
