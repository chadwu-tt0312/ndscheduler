"""基礎 tornado.web.RequestHandler 類別。

此套件提供一組通用的 RequestHandler 物件，供應用程式中的其他 URL 處理程式繼承使用。
"""

import json
from concurrent import futures
import re
import logging

import tornado.web
from jwt import decode, ExpiredSignatureError, InvalidTokenError

from ndscheduler import settings


logger = logging.getLogger(__name__)


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

        try:
            # 檢查用戶是否已登入，避免因為資料庫連接問題而導致整個請求失敗
            user = self.get_current_user()
            if not user:
                # 判斷是 API 請求還是網頁請求
                if self.request.headers.get("Accept") == "application/json" or self.request.path.startswith("/api/"):
                    # API 請求返回 401 狀態碼
                    self.set_status(401)
                    self.write({"error": {"code": 401, "message": "Unauthorized"}})
                    self.finish()
                else:
                    # 網頁請求直接重定向到登入頁面
                    self.redirect("/login")
                return

            # 嘗試解析 JSON 請求內容
            try:
                if self.request.headers.get("Content-Type", "").startswith("application/json"):
                    self.json_args = json.loads(self.request.body.decode())
            except (KeyError, json.JSONDecodeError):
                self.json_args = None

            # 用於稽核日誌
            self.username = self.get_username()
            self.scheduler_manager = self.application.settings["scheduler_manager"]
            self.datastore = self.scheduler_manager.get_datastore()

        except Exception as e:
            logger.error(f"處理請求時發生錯誤: {str(e)}", exc_info=True)
            # 出現錯誤時，將用戶重定向到登入頁面
            if self.request.headers.get("Accept") == "application/json" or self.request.path.startswith("/api/"):
                self.set_status(401)
                self.write({"error": {"code": 401, "message": "Authentication error"}})
                self.finish()
            else:
                self.redirect("/login")
            return

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
            # 解析 JWT token
            payload = decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

            # 驗證用戶是否存在於資料庫中
            username = payload.get("username")
            if username:
                # 只在 JWT 有效且需要進一步驗證用戶時才連接資料庫
                try:
                    # 確保 scheduler_manager 和 datastore 已初始化
                    if not hasattr(self, "scheduler_manager"):
                        self.scheduler_manager = self.application.settings["scheduler_manager"]
                    if not hasattr(self, "datastore"):
                        self.datastore = self.scheduler_manager.get_datastore()

                    # 使用 with 語句來確保資料庫會話在使用後被正確關閉
                    session = None
                    try:
                        session = self.get_session()
                        user_exists = self.datastore.check_user_exists(username, session)

                        # 如果用戶不存在，返回 None
                        if not user_exists:
                            logger.warning(f"Token 中的用戶 {username} 不存在於資料庫中")
                            return None
                    finally:
                        # 確保資料庫會話被正確關閉
                        if session and hasattr(session, "close"):
                            session.close()
                except Exception as e:
                    logger.error(f"驗證用戶時發生錯誤: {str(e)}", exc_info=True)
                    # 資料庫錯誤時，暫時接受 JWT 驗證結果
                    logger.warning(f"因資料庫錯誤，暫時信任 JWT token: {username}")
                    # 仍然返回 payload，但記錄警告

            return payload
        except ExpiredSignatureError:
            logger.warning("Token 已過期")
            return None
        except InvalidTokenError:
            logger.warning("無效的 Token")
            return None
        except Exception as e:
            logger.error(f"解析 Token 時發生錯誤: {str(e)}", exc_info=True)
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
            logger.error(f"獲取資料庫連接時發生錯誤: {str(e)}", exc_info=True)
            raise
