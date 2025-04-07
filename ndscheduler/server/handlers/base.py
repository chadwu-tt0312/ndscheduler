"""基礎 tornado.web.RequestHandler 類別。

此套件提供一組通用的 RequestHandler 物件，供應用程式中的其他 URL 處理程式繼承使用。
"""

import json
from concurrent import futures

import tornado.web

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

        預設為空字串。可由子類別覆寫以實現自訂的使用者認證。

        :return: 使用者名稱
        :rtype: str
        """
        return ""
