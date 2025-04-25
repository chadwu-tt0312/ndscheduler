# NDScheduler 架構分析

## 專案概述
NDScheduler 是一個靈活的 Python 庫，用於構建類似 cron 的任務調度系統。它提供了一個 FastAPI 服務器來提供 REST API 和 Web UI。

## 目錄結構說明

| 目錄 | 作用 |
|------|------|
| ndscheduler/corescheduler/core | 核心調度器實現，包含任務調度的核心邏輯 |
| ndscheduler/corescheduler/datastore | 數據存儲層，管理數據庫連接和查詢 |
| ndscheduler/server/routes | FastAPI 路由處理器，提供 REST API |
| ndscheduler/server/models | Pydantic 數據模型定義 |
| ndscheduler/static | 靜態資源文件，包含 Web UI 相關文件 |
| ndscheduler/static/js/models | 前端數據模型定義 |
| ndscheduler/static/js/views | 前端視圖組件，包含任務、執行和日誌等頁面 |
| simple_scheduler | 示例實現，包含設置、服務器和示例任務 |

## 架構模式
該專案採用 MVC（Model-View-Controller）架構模式：

- **Model**: 
  - `corescheduler/datastore` 中的數據模型
  - `server/models` 中的 Pydantic 模型
  - `static/js/models` 中的前端數據模型

- **View**: 
  - `static/js/views` 中的前端視圖組件
  - `static/css` 中的樣式文件

- **Controller**: 
  - `server/routes` 中的 API 路由處理器
  - `corescheduler/core` 中的核心調度邏輯

## 核心邏輯閱讀順序
1. `simple_scheduler/settings.py` - 了解系統配置
2. `simple_scheduler/scheduler.py` - 了解服務器啟動流程
3. `ndscheduler/corescheduler/core/scheduler.py` - 了解核心調度邏輯
4. `ndscheduler/corescheduler/datastore/providers/` - 了解數據存儲實現
5. `ndscheduler/server/routes/` - 了解 API 接口

## 界面修改指南
要修改界面，需要關注以下目錄：

1. `ndscheduler/static/css/` - 修改樣式
2. `ndscheduler/static/js/views/` - 修改頁面組件
3. `ndscheduler/static/js/templates/` - 修改頁面模板
4. `ndscheduler/static/js/models/` - 修改數據模型（如果需要）

## 關鍵組件
1. **CoreScheduler**: 封裝所有核心調度功能
2. **Datastore**: 管理數據庫連接和查詢
3. **ScheduleManager**: 通過 Datastore 管理任務
4. **Server**: FastAPI 服務器，提供 REST API 和 UI
5. **Web UI**: 單頁面 HTML 應用程序

## 框架遷移說明
該專案正在從 Tornado 遷移到 FastAPI 框架，主要變更包括：

1. **API 層面**：
   - 使用 FastAPI 的 APIRouter 替代 Tornado 的 handlers
   - 使用 Pydantic 模型進行請求/響應數據驗證
   - 自動生成 OpenAPI 文檔

2. **服務器層面**：
   - 使用 Uvicorn 作為 ASGI 服務器
   - 改進的異步支持
   - 更好的類型提示支持

3. **前端適配**：
   - 更新 API 響應格式
   - 優化數據模型定義
   - 改進錯誤處理機制

4. **配置管理**：
   - 使用 Pydantic 的 Settings 管理配置
   - 更靈活的環境變量支持
   - 更好的配置驗證
