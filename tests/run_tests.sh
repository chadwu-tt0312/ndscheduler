#!/bin/bash
# ndscheduler 測試執行腳本

# 確保使用正確的 Python 解釋器
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(dirname "$SOURCE_DIR")"

# 默認參數
SERVER_URL="http://localhost:8888"
USERNAME="user"
PASSWORD="password"

# 顯示幫助信息
show_help() {
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -h, --help                 顯示此幫助信息"
    echo "  -a, --api-only             僅運行 API 測試"
    echo "  -u, --ui-only              僅運行 UI 測試"
    echo "  -d, --headed               使用有界面的瀏覽器運行 UI 測試"
    echo "  -r, --report               生成 HTML 測試報告"
    echo "  --url=URL                  指定服務器地址 (默認: $SERVER_URL)"
    echo "  --username=USERNAME        指定測試用戶名 (默認: $USERNAME)"
    echo "  --password=PASSWORD        指定測試密碼 (默認: $PASSWORD)"
    echo ""
    echo "示例:"
    echo "  $0                         運行所有測試"
    echo "  $0 -a                      僅運行 API 測試"
    echo "  $0 -u -d                   以有界面模式運行 UI 測試"
    echo "  $0 --url=http://localhost:9999 --username=admin"
    echo ""
    exit 0
}

# 解析參數
API_ONLY=false
UI_ONLY=false
HEADED=""
REPORT=""

for i in "$@"; do
    case $i in
        -h|--help)
            show_help
            ;;
        -a|--api-only)
            API_ONLY=true
            shift
            ;;
        -u|--ui-only)
            UI_ONLY=true
            shift
            ;;
        -d|--headed)
            HEADED="--headed"
            shift
            ;;
        -r|--report)
            REPORT="--html=test_report.html --self-contained-html"
            shift
            ;;
        --url=*)
            SERVER_URL="${i#*=}"
            shift
            ;;
        --username=*)
            USERNAME="${i#*=}"
            shift
            ;;
        --password=*)
            PASSWORD="${i#*=}"
            shift
            ;;
        *)
            # 未知選項
            ;;
    esac
done

# 檢查 pytest 是否已安裝
if ! command -v pytest &> /dev/null; then
    echo "錯誤: 未找到 pytest，請執行 'pip install pytest' 安裝。"
    exit 1
fi

# 檢查測試報告插件
if [ ! -z "$REPORT" ]; then
    python -c "import pytest_html" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "警告: 未找到 pytest-html，正在安裝..."
        pip install pytest-html
    fi
fi

# 檢查 Playwright 依賴
if [ "$API_ONLY" = false ]; then
    python -c "from playwright.sync_api import sync_playwright" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "錯誤: 未找到 Playwright，請執行 'pip install playwright' 安裝。"
        exit 1
    fi
    
    # 檢查 Playwright 瀏覽器是否已安裝
    if ! python -c "from playwright.sync_api import sync_playwright; sync_playwright().__enter__().chromium.launch()" &>/dev/null; then
        echo "警告: Playwright 瀏覽器未安裝或配置錯誤，正在安裝瀏覽器..."
        playwright install
    fi
fi

# 構建命令行參數 (API 測試使用 --server-url)
COMMON_ARGS="--server-url=$SERVER_URL --username=$USERNAME --password=$PASSWORD $REPORT -v"

# UI 測試需要使用 playwright 的 base-url 參數
UI_ARGS="--base-url=$SERVER_URL $HEADED"

echo "開始運行測試..."
echo "服務器地址: $SERVER_URL"
echo "用戶名: $USERNAME"
echo "==========================="

cd "$PROJECT_ROOT"

# 根據選項決定運行哪些測試
if [ "$API_ONLY" = true ]; then
    echo "僅運行 API 測試"
    pytest tests/test_api_integration.py $COMMON_ARGS
elif [ "$UI_ONLY" = true ]; then
    echo "僅運行 UI 測試"
    pytest tests/test_web_ui_integration.py $COMMON_ARGS $UI_ARGS
else
    echo "運行 API 測試"
    pytest tests/test_api_integration.py $COMMON_ARGS
    API_RESULT=$?
    
    echo "運行 UI 測試"
    pytest tests/test_web_ui_integration.py $COMMON_ARGS $UI_ARGS
    UI_RESULT=$?
    
    # 合併結果
    if [ $API_RESULT -ne 0 ] || [ $UI_RESULT -ne 0 ]; then
        TEST_RESULT=1
    else
        TEST_RESULT=0
    fi
fi

# 檢查退出狀態
if [ ${TEST_RESULT:-$?} -eq 0 ]; then
    echo "==========================="
    echo "測試完成: 全部通過！"
    
    if [ ! -z "$REPORT" ]; then
        echo "測試報告已生成: $PROJECT_ROOT/test_report.html"
    fi
    
    exit 0
else
    echo "==========================="
    echo "測試完成: 存在失敗！"
    
    if [ ! -z "$REPORT" ]; then
        echo "詳細報告: $PROJECT_ROOT/test_report.html"
    fi
    
    exit 1
fi 