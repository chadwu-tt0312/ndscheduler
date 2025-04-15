"""基礎 tornado.web.RequestHandler 類別。

此套件提供一組通用的 RequestHandler 物件，供應用程式中的其他 URL 處理程式繼承使用。
"""

import json
from concurrent import futures

import tornado.web
from jwt import decode, ExpiredSignatureError, InvalidTokenError

from ndscheduler import settings


class BaseHandler(tornado.web.RequestHandler):
    """基礎處理程式類別，提供共用功能。"""

    executor = futures.ThreadPoolExecutor(max_workers=settings.TORNADO_MAX_WORKERS)

    def prepare(self) -> None:
        """預處理請求。

        - 解析 JSON 請求內容
        - 設定使用者名稱
        - 初始化排程管理器和資料儲存連接
        """
        try:
            if self.request.headers["Content-Type"].startswith("application/json"):
                self.json_args = json.loads(self.request.body.decode())
        except KeyError:
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
