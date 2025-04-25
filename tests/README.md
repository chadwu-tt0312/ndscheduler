# ndscheduler 測試套件

這個目錄包含了 ndscheduler 的測試套件，包括單元測試、API 整合測試和 Web UI 整合測試。

## 通用測試配置

所有測試都使用以下配置參數，可以通過命令行選項自定義：

```bash
# 指定服務器地址
pytest --server-url=http://your-server:8888    # API 測試用
pytest --base-url=http://your-server:8888    # Web UI 測試用

# 指定登入憑證
pytest --username=admin --password=admin123

# 組合使用
pytest --server-url=http://localhost:8888 --base-url=http://localhost:8888 --username=admin --password=secret
```

> 注意：API 測試使用 `--server-url` 參數，而 Web UI 測試使用 Playwright 的 `--base-url` 參數。使用執行腳本 `run_tests.sh` 可以自動處理這兩個參數。

## API 整合測試

API 整合測試檔案 `test_api_integration.py` 測試了 ndscheduler 的所有 API 端點，確保它們正常工作。

### 前提條件

運行整合測試前，請確保:

1. ndscheduler 服務器已經啟動並運行在 `http://localhost:8888`
2. 已安裝所需的測試依賴:
   ```
   pip install -r requirements-dev.txt
   ```
   或
   ```
   pip install pytest requests
   ```

### 運行測試

有幾種運行測試的方式:

#### 運行所有 API 整合測試

```bash
pytest tests/test_api_integration.py -v
```

#### 運行特定的測試

```bash
# 運行令牌驗證測試
pytest tests/test_api_integration.py::TestAPIIntegration::test_01_verify_token -v

# 運行作業生命週期測試
pytest tests/test_api_integration.py::TestAPIIntegration::test_07_job_lifecycle -v
```

#### 以更詳細的方式運行測試

```bash
pytest tests/test_api_integration.py -vv -s
```

### 測試說明

測試套件涵蓋以下功能:

1. **認證測試**:
   - 登入和令牌獲取 (在 setUp 中)
   - 令牌驗證

2. **類別管理**:
   - 獲取類別列表
   - 創建新類別

3. **用戶管理**:
   - 獲取用戶列表
   - 獲取當前用戶信息
   - 用戶生命週期 (創建、獲取、刪除)

4. **作業管理**:
   - 作業完整生命週期 (創建、獲取、修改、暫停、恢復、刪除)
   - 執行作業

5. **執行記錄和日誌**:
   - 獲取執行記錄
   - 獲取系統日誌

### 注意事項

- 測試依賴於 ndscheduler 服務器正在運行
- 測試預設使用用戶名 `user` 和密碼 `password` 進行身份驗證
- 每個測試執行前都會重新登入並獲取新的認證令牌
- 某些測試（如創建用戶和作業）使用時間戳來確保唯一性
- 對於創建操作 (POST)，測試接受 200 或 201 狀態碼
- 驗證 API 回應主要檢查資料是否存在，而非特定欄位，以提高測試對 API 變更的適應性

## Web UI 整合測試

Web UI 整合測試檔案 `test_web_ui_integration.py` 使用 Playwright 測試 ndscheduler 的網頁界面。

### 前提條件

運行 Web UI 測試前，請確保:

1. ndscheduler 服務器已經啟動並運行在 `http://localhost:8888`
2. 已安裝所需的測試依賴:
   ```
   pip install -r requirements-dev.txt
   ```

## 運行所有測試

若要運行所有測試，包括 API 測試和 Web UI 測試，推薦使用提供的腳本：

```bash
# 運行所有測試
./tests/run_tests.sh

# 僅運行 API 測試
./tests/run_tests.sh -a

# 僅運行 Web UI 測試
./tests/run_tests.sh -u

# 在有界面的瀏覽器中運行 UI 測試
./tests/run_tests.sh -u -d

# 生成 HTML 報告
./tests/run_tests.sh -r

# 指定服務器地址和憑證
./tests/run_tests.sh --url=http://localhost:9999 --username=admin --password=admin123
```

如果不使用腳本，則需要分別運行 API 和 Web UI 測試：

```bash
# API 測試
pytest tests/test_api_integration.py --server-url=http://localhost:8888

# Web UI 測試
pytest tests/test_web_ui_integration.py --base-url=http://localhost:8888
```

## 測試報告

生成詳細的 HTML 測試報告：

```bash
# 安裝報告插件
pip install pytest-html

# 生成 HTML 報告
pytest tests/ --html=report.html --self-contained-html
```

## 常見問題

1. **測試失敗**：
   - 確保服務器正在運行並可以使用瀏覽器訪問
   - 檢查用戶名和密碼是否正確
   - 檢查 CSS 選擇器是否與當前 UI 匹配

2. **Playwright 問題**：
   - 如果遇到瀏覽器問題，嘗試重新安裝：`playwright install --force`
   - 開啟有界面的模式調試：`pytest --headed`

3. **參數問題**：
   - API 測試使用 `--server-url` 參數
   - Web UI 測試使用 Playwright 的 `--base-url` 參數
   - 使用腳本 `run_tests.sh` 時只需使用 `--url` 參數