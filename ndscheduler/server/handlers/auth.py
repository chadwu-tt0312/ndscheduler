"""Authentication handlers."""

import json
import logging
import datetime
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError

import tornado.web

from ndscheduler import settings

logger = logging.getLogger(__name__)


class LoginHandler(tornado.web.RequestHandler):
    """處理使用者登入請求。"""

    def initialize(self):
        """初始化處理器。"""
        self.scheduler_manager = self.application.settings["scheduler_manager"]
        self.datastore = self.scheduler_manager.get_datastore()

    def set_default_headers(self):
        """設定回應標頭。"""
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def options(self):
        """處理 OPTIONS 請求。"""
        self.set_status(204)
        self.finish()

    def post(self):
        """處理登入請求。

        Body:
            username: 使用者名稱
            password: 使用者密碼

        Returns:
            成功時返回 JWT token
            失敗時返回錯誤訊息
        """
        try:
            # 記錄請求資訊（開發時使用）
            logger.debug("收到登入請求：%s", self.request.body.decode("utf-8"))

            data = json.loads(self.request.body.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                self.set_status(400)
                self.write({"error": "使用者名稱和密碼不能為空"})
                return

            # 驗證使用者
            if not self.datastore.verify_user(username, password):
                self.set_status(401)
                self.write({"error": "使用者名稱或密碼錯誤"})
                return

            # 取得使用者資訊
            user = self.datastore.get_user(username)
            if not user:
                self.set_status(401)
                self.write({"error": "使用者不存在"})
                return

            # 生成 JWT token
            payload = {
                "user_id": user["id"],
                "username": user["username"],
                "category_id": user["category_id"],
                "is_admin": user["is_admin"],
                "is_permission": user["is_permission"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=settings.JWT_EXPIRATION_DAYS),
            }
            token = encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

            # 設置 secure cookie
            self.set_secure_cookie("token", token, expires_days=settings.JWT_EXPIRATION_DAYS)

            response_data = {
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "category_id": user["category_id"],
                    "is_admin": user["is_admin"],
                    "is_permission": user["is_permission"],
                },
            }

            # 記錄成功登入（開發時使用）
            logger.debug("使用者 %s 登入成功", username)

            self.write(response_data)

        except json.JSONDecodeError as e:
            logger.error("無效的 JSON 格式")
            self.set_status(400)
            self.write({"error": f"Invalid JSON format: {str(e)}"})
        except Exception as e:
            logger.exception("登入失敗")
            self.set_status(500)
            self.write({"error": str(e)})


def authenticated(method):
    """裝飾器：要求認證。

    如果用戶未認證，將重定向到登入頁面。
    對於 API 請求（Accept: application/json），返回 401 錯誤。
    """

    def wrapper(self, *args, **kwargs):
        if not isinstance(self, tornado.web.RequestHandler):
            raise TypeError("authenticated 只能用於 RequestHandler 類別")

        user = self.get_current_user()
        if not user:
            # 檢查是否為 API 請求
            if self.request.headers.get("Accept") == "application/json":
                self.set_status(401)
                self.write({"error": "未認證或 token 已過期"})
            else:
                # 網頁請求，重定向到登入頁面
                self.redirect("/login")
            return

        return method(self, *args, **kwargs)

    return wrapper


def admin_required(method):
    """裝飾器：要求管理員權限。"""

    @authenticated
    def wrapper(self, *args, **kwargs):
        if not self.current_user.get("is_admin"):
            self.set_status(403)
            self.write({"error": "需要管理員權限"})
            return
        return method(self, *args, **kwargs)

    return wrapper


class VerifyHandler(tornado.web.RequestHandler):
    """處理用戶身份驗證檢查請求。"""

    def initialize(self):
        """初始化處理器。"""
        self.scheduler_manager = self.application.settings["scheduler_manager"]
        self.datastore = self.scheduler_manager.get_datastore()

    def set_default_headers(self):
        """設定回應標頭。"""
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "GET, OPTIONS")

    def options(self):
        """處理 OPTIONS 請求。"""
        self.set_status(204)
        self.finish()

    def get(self):
        """處理身份驗證檢查請求。

        檢查用戶是否已登入並且存在於資料庫中。

        Returns:
            成功時返回用戶資訊
            失敗時返回錯誤訊息
        """
        try:
            # 從 cookie 中取得 token
            token = self.get_secure_cookie("token")
            if not token:
                # 從 Authorization 標頭取得 token
                auth_header = self.request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                else:
                    self.set_status(401)
                    self.write({"error": "未提供 token"})
                    return
            else:
                token = token.decode("utf-8")

            # 解析 token
            try:
                payload = decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
                username = payload.get("username")

                # 檢查用戶是否存在
                if not username:
                    self.set_status(401)
                    self.write({"error": "無效的 token 格式"})
                    return

                user = self.datastore.get_user(username)
                if not user:
                    self.set_status(401)
                    self.write({"error": "用戶不存在"})
                    return

                # 返回用戶資訊
                response_data = {
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "category_id": user["category_id"],
                        "is_admin": user["is_admin"],
                        "is_permission": user["is_permission"],
                    }
                }

                self.write(response_data)

            except ExpiredSignatureError:
                self.set_status(401)
                self.write({"error": "token 已過期"})
            except InvalidTokenError:
                self.set_status(401)
                self.write({"error": "無效的 token"})

        except Exception as e:
            logger.error("驗證失敗: %s", str(e), exc_info=True)
            self.set_status(500)
            self.write({"error": str(e)})
