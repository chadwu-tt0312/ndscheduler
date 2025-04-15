"""Serves the single page app web ui."""

import json

from ndscheduler import settings
from ndscheduler import utils
from ndscheduler.server.handlers import base
from ndscheduler.server.handlers.auth import authenticated


class Handler(base.BaseHandler):
    """Index page request handler."""

    @authenticated
    def get(self):
        """Serve up the single page app for scheduler dashboard."""
        try:
            meta_info = utils.get_all_available_jobs() or []  # 確保返回列表，即使是空的
            print(f"正在渲染主頁，meta_info: {meta_info}")
            print(f"使用模板: {settings.APP_INDEX_PAGE}")
            print(f"模板目錄: {settings.TEMPLATE_DIR_PATH}")
            self.render(settings.APP_INDEX_PAGE, jobs_meta_info=json.dumps(meta_info))
        except Exception as e:
            print(f"渲染主頁時發生錯誤: {str(e)}")
            import traceback

            traceback.print_exc()
            raise


class LoginHandler(base.BaseHandler):
    """Login page request handler."""

    def get(self):
        """Serve up the login page."""
        current_user = self.get_current_user()
        print(f"當前用戶狀態: {current_user}")

        if current_user:
            print("用戶已登入，重定向到主頁")
            self.redirect("/")
            return
        else:
            print("用戶未登入，顯示登入頁面")
            self.render("login.html")
