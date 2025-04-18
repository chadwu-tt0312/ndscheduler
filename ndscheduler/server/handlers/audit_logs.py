"""Handler for endpoint of audit logs."""

import json
import logging
from datetime import datetime, timedelta

import tornado.web
import tornado.gen
import tornado.concurrent
import dateutil.parser
import dateutil.tz

from ndscheduler.server.handlers import base

logger = logging.getLogger(__name__)


class Handler(base.BaseHandler):

    def _get_logs(self):
        """取得指定時間範圍內的稽核日誌，根據使用者的 category_id 過濾。

        這是一個阻塞操作。

        Returns:
            dict: 稽核日誌資訊，格式為：
            {
                "logs": [
                    {
                        "job_id": str,
                        "job_name": str,
                        "event": str,
                        "user": str,
                        "description": str,
                        "created_time": str (ISO format)
                    },
                    ...
                ],
                "total": int
            }
        """
        try:
            # 取得查詢時間範圍
            now = datetime.utcnow()
            time_range_end = self.get_argument("time_range_end", now.isoformat())

            # 預設查詢最近 24 小時的日誌
            one_day_ago = now - timedelta(days=1)
            time_range_start = self.get_argument("time_range_start", one_day_ago.isoformat())

            # 驗證時間格式
            try:
                dateutil.parser.parse(time_range_start)
                dateutil.parser.parse(time_range_end)
            except ValueError as e:
                self.set_status(400)
                return {"error": f"無效的時間格式：{str(e)}"}

            # 獲取使用者 category_id
            user_info = self.get_current_user()
            user_category_id = user_info.get("category_id", 0) if user_info else 0
            # logger.info(f"Audit Logs - User: {self.username}, Retrieved Category ID: {user_category_id}")

            # 根據 category_id 呼叫不同的 datastore 方法
            if user_category_id == 0:
                # logger.info("Audit Logs - Calling datastore.get_audit_logs()")
                # category_id 為 0，獲取所有 Audit Logs
                result = self.datastore.get_audit_logs(time_range_start, time_range_end)
            else:
                # logger.info(f"Audit Logs - Calling datastore.get_audit_logs_by_category({user_category_id})")
                # category_id 不為 0，根據分類獲取 Audit Logs
                result = self.datastore.get_audit_logs_by_category(user_category_id, time_range_start, time_range_end)

            # 處理日誌資料
            logs = []
            for log in result.get("audit_logs", []):
                try:
                    # 確保 description 欄位正確處理
                    description = log.get("description", "")
                    if description:
                        try:
                            # 如果是 JSON 字串，嘗試解析並重新格式化
                            if isinstance(description, str):
                                if description.startswith("{") and description.endswith("}"):
                                    try:
                                        description_obj = json.loads(description)
                                        description = json.dumps(description_obj, ensure_ascii=False, indent=2)
                                    except json.JSONDecodeError:
                                        # 如果解析失敗，保持原始字串
                                        pass
                        except Exception as e:
                            logger.error(f"處理 description 時發生錯誤：{str(e)}", exc_info=True)
                            # 如果處理失敗，保持原始內容
                            pass

                    # 確保回傳的資料格式符合前端期望
                    log_entry = {
                        "job_id": log.get("job_id", ""),
                        "job_name": log.get("job_name", ""),
                        "event": log.get("event", "UNKNOWN"),
                        "user": log.get("user", ""),
                        "description": description,  # 確保這裡的值不是 None
                        "created_time": log.get("created_time", ""),
                    }

                    # 加入除錯資訊
                    logger.debug(f"處理的日誌項目：{log_entry}")

                    logs.append(log_entry)
                except Exception as e:
                    logger.error(f"處理日誌項目時發生錯誤：{str(e)}", exc_info=True)
                    continue

            response_data = {"logs": logs, "total": len(logs)}

            # 加入除錯資訊
            logger.debug(f"回傳的資料：{response_data}")

            return response_data

        except Exception as e:
            logger.error(f"取得稽核日誌時發生錯誤：{str(e)}", exc_info=True)
            self.set_status(500)
            return {"error": f"取得稽核日誌失敗：{str(e)}"}

    @tornado.concurrent.run_on_executor
    def get_logs(self):
        """在執行緒執行器上執行 _get_logs 的包裝器。

        Returns:
            dict: 稽核日誌資訊。
        """
        return self._get_logs()

    @tornado.gen.coroutine
    def get_logs_yield(self):
        """非同步取得稽核日誌。

        Returns:
            dict: 稽核日誌資訊。
        """
        return_json = yield self.get_logs()
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def get(self):
        """返回稽核日誌。

        處理端點：GET /api/v1/logs
        """
        yield self.get_logs_yield()
