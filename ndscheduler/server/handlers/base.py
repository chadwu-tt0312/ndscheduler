"""基礎 tornado.web.RequestHandler 類別。

此套件提供一組通用的 RequestHandler 物件，供應用程式中的其他 URL 處理程式繼承使用。
"""

import json
from concurrent import futures
import re

import tornado.web
from jwt import decode, ExpiredSignatureError, InvalidTokenError

from ndscheduler import settings


class BaseHandler(tornado.web.RequestHandler):
    """基礎處理程式類別，提供共用功能。"""

    executor = futures.ThreadPoolExecutor(max_workers=settings.TORNADO_MAX_WORKERS)

    # 不需要驗證的路徑列表
    WHITELIST_PATHS = [r"^/login$", r"^/api/v1/auth/login$", r"^/static/.*$"]

    def _is_path_whitelisted(self, path):
        """檢查路徑是否在白名單中。"""
        return any(re.match(pattern, path) for pattern in self.WHITELIST_PATHS)

    def prepare(self) -> None:
        """預處理請求。

        - 解析 JSON 請求內容
        - 設定使用者名稱
        - 初始化排程管理器和資料儲存連接
        - 檢查用戶身份驗證
        """
        # 檢查是否為白名單路徑
        if self._is_path_whitelisted(self.request.path):
            return

        # 檢查用戶是否已登入
        user = self.get_current_user()
        if not user:
            self.set_status(401)
            self.write({"error": {"code": 401, "message": "Unauthorized"}})
            self.finish()
            return

        try:
            if self.request.headers.get("Content-Type", "").startswith("application/json"):
                self.json_args = json.loads(self.request.body.decode())
        except (KeyError, json.JSONDecodeError):
            self.json_args = None

        # 用於稽核日誌
        self.username = self.get_username()
        self.scheduler_manager = self.application.settings["scheduler_manager"]
        self.datastore = self.scheduler_manager.get_datastore()

    def get_username(self) -> str:
        """取得登入使用者名稱。

        從 JWT token 中取得使用者名稱。

        :return: 使用者名稱
        :rtype: str
        """
        user = self.get_current_user()
        return user.get("username", "") if user else ""

    def get_current_user(self):
        """取得目前登入的使用者。

        從 JWT token 中取得使用者資訊。
        token 可以從 Authorization 標頭或 cookie 中取得。

        :return: 使用者資訊字典或 None
        :rtype: dict or None
        """
        # 先嘗試從 Authorization 標頭取得 token
        auth_header = self.request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            # 如果沒有 Authorization 標頭，嘗試從 cookie 取得 token
            token = self.get_secure_cookie("token")
            if token:
                token = token.decode("utf-8")

        if not token:
            return None

        try:
            payload = decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except ExpiredSignatureError:
            return None
        except InvalidTokenError:
            return None

    def write_error(self, status_code: int, **kwargs) -> None:
        """自訂錯誤回應格式。

        :param status_code: HTTP 狀態碼
        :type status_code: int
        """
        self.set_header("Content-Type", "application/json")
        self.write({"error": {"code": status_code, "message": self._reason}})

    def get_session(self):
        """獲取資料庫會話。

        :return: SQLAlchemy 會話
        """
        try:
            # 首先嘗試使用 session_factory 方法（新版方法）
            if hasattr(self.datastore, "session_factory"):
                return self.datastore.session_factory()
            # 如果沒有 session_factory 方法，則使用 datastore 直接提供的 Session 對象或連接
            elif hasattr(self.datastore, "session"):
                return self.datastore.session
            # 兼容舊版 SQLAlchemy
            elif hasattr(self.datastore, "engine"):
                from sqlalchemy.orm import Session

                return Session(self.datastore.engine)
            else:
                raise AttributeError("無法獲取資料庫連接，datastore 缺少必要的屬性")
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"獲取資料庫連接時發生錯誤: {str(e)}", exc_info=True)
            raise
