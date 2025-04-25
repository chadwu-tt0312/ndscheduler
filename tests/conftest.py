"""
pytest 配置文件，為測試提供全局設置和共享 fixtures。
"""

import os
import pytest
import requests
from playwright.sync_api import Page


def pytest_addoption(parser):
    """為 pytest 添加命令行選項"""
    parser.addoption("--server-url", default="http://localhost:8888", help="ndscheduler 服務的基礎 URL")
    parser.addoption("--username", default="admin", help="測試用戶名")
    parser.addoption("--password", default="password", help="測試密碼")


@pytest.fixture(scope="session")
def base_url(request):
    """返回基礎 URL，兼容 playwright 和自定義參數"""
    # 首先嘗試從 --server-url 獲取
    try:
        return request.config.getoption("--server-url")
    except ValueError:
        # 如果 --server-url 未定義，則嘗試使用 playwright 的 --base-url
        try:
            return request.config.getoption("--base-url")
        except ValueError:
            # 如果兩者都未定義，返回默認值
            return "http://localhost:8888"


@pytest.fixture(scope="session")
def username(request):
    """返回測試用戶名"""
    return request.config.getoption("--username")


@pytest.fixture(scope="session")
def password(request):
    """返回測試密碼"""
    return request.config.getoption("--password")


@pytest.fixture(scope="session")
def auth_credentials(username, password):
    """返回認證憑證"""
    return {"username": username, "password": password}


@pytest.fixture(scope="session", autouse=True)
def check_env():
    """檢查測試環境並輸出信息"""
    print("\n測試環境準備中...")

    # 確認 test_api_integration.py 和 test_web_ui_integration.py 存在
    test_files = ["test_api_integration.py", "test_web_ui_integration.py"]
    missing_files = []

    for file in test_files:
        if not os.path.exists(os.path.join(os.path.dirname(__file__), file)):
            missing_files.append(file)

    if missing_files:
        print(f"警告: 以下測試文件不存在: {', '.join(missing_files)}")

    # 確認依賴已安裝
    try:
        print("✓ requests 已安裝")
    except ImportError:
        print("✗ requests 未安裝，API 測試將失敗")

    try:
        print("✓ playwright 已安裝")
    except ImportError:
        print("✗ playwright 未安裝，Web UI 測試將失敗")

    print("測試環境準備完成！\n")
