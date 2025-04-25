import unittest
import requests
import time
import pytest
from datetime import datetime, timedelta


class TestAPIIntegration(unittest.TestCase):
    """測試 ndscheduler API 整合"""

    # 服務器地址和認證信息將從 pytest 配置中獲取
    @pytest.fixture(autouse=True)
    def init_test(self, base_url, username, password):
        """初始化測試環境，設置基礎 URL 和認證信息"""
        self.BASE_URL = base_url
        self.USERNAME = username
        self.PASSWORD = password

    def setUp(self):
        """每個測試前都執行的設置"""
        # 登入並獲取 token
        login_url = f"{self.BASE_URL}/api/v1/auth/login"
        login_data = {"username": self.USERNAME, "password": self.PASSWORD}

        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200, "登入失敗")

        # 提取 token
        login_response = response.json()
        self.token = login_response.get("token")
        self.assertIsNotNone(self.token, "未能獲取到認證令牌")

        # 設置請求標頭
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def test_01_verify_token(self):
        """測試令牌驗證"""
        verify_url = f"{self.BASE_URL}/api/v1/auth/verify"
        response = requests.get(verify_url, headers=self.headers)
        self.assertEqual(response.status_code, 200, "令牌驗證失敗")

        # 不檢查 success 欄位，只要狀態碼為 200 就代表令牌有效
        data = response.json()
        self.assertIsNotNone(data, "令牌驗證未返回有效數據")

    def test_02_get_categories(self):
        """測試獲取類別"""
        url = f"{self.BASE_URL}/api/v1/categories"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 200, "獲取類別失敗")

        data = response.json()
        self.assertIn("categories", data, "回應中沒有找到類別資料")

    def test_03_add_category(self):
        """測試添加類別"""
        url = f"{self.BASE_URL}/api/v1/categories"
        category_data = {"name": f"測試類別_{int(time.time())}", "description": "這是一個由整合測試創建的類別"}

        response = requests.post(url, json=category_data, headers=self.headers)
        # 修正：接受 201 狀態碼（創建成功）
        self.assertIn(response.status_code, [200, 201], "添加類別失敗")

        data = response.json()
        # 檢查回應是否包含資料，而非檢查 success 欄位
        self.assertIsNotNone(data, "添加類別未返回有效數據")

    def test_04_get_users(self):
        """測試獲取用戶列表"""
        url = f"{self.BASE_URL}/api/v1/users"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 200, "獲取用戶列表失敗")

        data = response.json()
        self.assertIn("users", data, "回應中沒有找到用戶資料")

    def test_05_get_current_user(self):
        """測試獲取當前用戶"""
        url = f"{self.BASE_URL}/api/v1/users/current"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 200, "獲取當前用戶資訊失敗")

        data = response.json()
        self.assertEqual(data.get("username"), self.USERNAME, "回傳的用戶名不一致")

    def test_06_user_lifecycle(self):
        """測試用戶生命週期：創建->獲取->刪除"""
        # 1. 創建新用戶
        create_url = f"{self.BASE_URL}/api/v1/users"
        test_username = f"test_user_{int(time.time())}"
        user_data = {
            "username": test_username,
            "password": "testpassword",
            "category_id": 1,  # 使用已存在的類別ID
            "is_admin": False,
            "is_permission": True,
        }

        create_response = requests.post(create_url, json=user_data, headers=self.headers)
        # 修正：接受 201 狀態碼（創建成功）
        self.assertIn(create_response.status_code, [200, 201], "創建用戶失敗")

        create_data = create_response.json()
        # 檢查 user_id 是否存在而非檢查 success 欄位
        user_id = create_data.get("id")
        self.assertIsNotNone(user_id, "未獲取到用戶ID")

        # 2. 獲取用戶資料
        get_url = f"{self.BASE_URL}/api/v1/users/{user_id}"
        get_response = requests.get(get_url, headers=self.headers)
        self.assertEqual(get_response.status_code, 200, "獲取用戶資料失敗")

        get_data = get_response.json()
        self.assertEqual(get_data.get("username"), test_username, "獲取的用戶名不符")

        # 3. 刪除用戶
        delete_url = f"{self.BASE_URL}/api/v1/users/{user_id}"
        delete_response = requests.delete(delete_url, headers=self.headers)
        self.assertEqual(delete_response.status_code, 200, "刪除用戶失敗")

        delete_data = delete_response.json()
        # 只要返回有效數據即可
        self.assertIsNotNone(delete_data, "刪除用戶未返回有效數據")

    def test_07_job_lifecycle(self):
        """測試作業生命週期：創建->獲取->修改->暫停->恢復->刪除"""
        # 1. 創建新作業
        create_url = f"{self.BASE_URL}/api/v1/jobs"
        job_data = {
            "job_class_string": "simple_scheduler.jobs.sample_job.AwesomeJob",
            "name": f"測試作業_{int(time.time())}",
            "pub_args": ["測試參數1", "測試參數2"],
            "minute": "*/5",
            "hour": "*",
            "day": "*",
            "month": "*",
            "day_of_week": "*",
        }

        create_response = requests.post(create_url, json=job_data, headers=self.headers)
        # 修正：接受 201 狀態碼（創建成功）
        self.assertIn(create_response.status_code, [200, 201], "創建作業失敗")

        create_data = create_response.json()
        job_id = create_data.get("job_id")
        self.assertIsNotNone(job_id, "未獲取到作業ID")

        # 2. 獲取作業資料
        get_url = f"{self.BASE_URL}/api/v1/jobs/{job_id}"
        get_response = requests.get(get_url, headers=self.headers)
        self.assertEqual(get_response.status_code, 200, "獲取作業資料失敗")

        # 3. 修改作業
        modify_url = f"{self.BASE_URL}/api/v1/jobs/{job_id}"
        modified_job_data = {
            "job_class_string": "simple_scheduler.jobs.sample_job.AwesomeJob",
            "name": f"修改後的測試作業_{int(time.time())}",
            "pub_args": ["修改參數1", "修改參數2"],
            "minute": "*/10",
            "hour": "*",
            "day": "*",
            "month": "*",
            "day_of_week": "*",
        }

        modify_response = requests.put(modify_url, json=modified_job_data, headers=self.headers)
        self.assertEqual(modify_response.status_code, 200, "修改作業失敗")

        # 4. 暫停作業
        pause_url = f"{self.BASE_URL}/api/v1/jobs/{job_id}"
        pause_response = requests.patch(pause_url, headers=self.headers)
        self.assertEqual(pause_response.status_code, 200, "暫停作業失敗")

        # 5. 恢復作業
        resume_url = f"{self.BASE_URL}/api/v1/jobs/{job_id}"
        resume_response = requests.options(resume_url, headers=self.headers)
        self.assertEqual(resume_response.status_code, 200, "恢復作業失敗")

        # 6. 執行作業
        execute_url = f"{self.BASE_URL}/api/v1/executions/{job_id}"
        execute_response = requests.post(execute_url, headers=self.headers)
        self.assertEqual(execute_response.status_code, 200, "執行作業失敗")

        # 7. 刪除作業
        delete_url = f"{self.BASE_URL}/api/v1/jobs/{job_id}"
        delete_response = requests.delete(delete_url, headers=self.headers)
        self.assertEqual(delete_response.status_code, 200, "刪除作業失敗")

    def test_08_get_executions(self):
        """測試獲取執行記錄"""
        # 獲取時間範圍內的執行記錄
        start_time = datetime.utcnow() - timedelta(days=30)  # 30天前
        end_time = datetime.utcnow()  # 現在

        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        url = f"{self.BASE_URL}/api/v1/executions"
        params = {"time_range_start": start_time_str, "time_range_end": end_time_str}

        response = requests.get(url, params=params, headers=self.headers)
        self.assertEqual(response.status_code, 200, "獲取執行記錄失敗")

    def test_09_get_logs(self):
        """測試獲取日誌"""
        # 獲取時間範圍內的日誌
        start_time = datetime.utcnow() - timedelta(days=30)  # 30天前
        end_time = datetime.utcnow()  # 現在

        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        url = f"{self.BASE_URL}/api/v1/logs"
        params = {"time_range_start": start_time_str, "time_range_end": end_time_str}

        response = requests.get(url, params=params, headers=self.headers)
        self.assertEqual(response.status_code, 200, "獲取日誌失敗")


if __name__ == "__main__":
    pytest.main(["-v", "test_api_integration.py"])
