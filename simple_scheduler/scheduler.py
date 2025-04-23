"""Run the scheduler process."""

import os
import logging
from sqlalchemy import select, asc

os.environ["NDSCHEDULER_SETTINGS_MODULE"] = "simple_scheduler.settings"
os.environ["PYTHONPATH"] = "."

from ndscheduler.server import server  # noqa: E402

logger = logging.getLogger(__name__)


class SimpleServer(server.SchedulerServer):

    def _get_first_admin_info(self) -> tuple[int, str]:
        """查詢資料庫中第一個管理員的 category_id 和 username。"""
        default_category_id = 0
        default_username = "SYSTEM"  # 設定預設使用者名稱
        try:
            datastore = self.scheduler_manager.get_datastore()
            users_table = datastore.users_table
            stmt = (
                select(users_table.c.category_id, users_table.c.username)  # 查詢兩個欄位
                .where(users_table.c.is_admin.is_(True))
                .order_by(asc(users_table.c.created_at))
                .limit(1)
            )
            with datastore.engine.connect() as connection:
                result = connection.execute(stmt).first()
                if result:
                    retrieved_id = result.category_id  # 使用欄位名稱獲取
                    retrieved_username = result.username  # 使用欄位名稱獲取

                    final_id = default_category_id
                    if retrieved_id is not None:
                        final_id = retrieved_id
                    else:
                        logger.warning("找到最早的管理員，但其 category_id 為 None")

                    final_username = default_username
                    if retrieved_username:
                        final_username = retrieved_username
                    else:
                        logger.warning("找到最早的管理員，但其 username 為空")

                    return final_id, final_username
                else:
                    logger.warning("找不到任何管理員使用者，將使用預設值")
        except Exception as e:
            logger.error(f"查詢第一個管理員資訊時發生錯誤: {e}，將使用預設值", exc_info=True)
        return default_category_id, default_username

    def post_scheduler_start(self):
        # New user experience! Make sure we have at least 1 job to demo!
        jobs = self.scheduler_manager.get_jobs()
        if len(jobs) == 0:
            # --- 獲取第一個管理員的資訊 ---
            first_admin_category_id, first_admin_username = self._get_first_admin_info()

            extra_kwargs = {}
            extra_kwargs["category_id"] = first_admin_category_id
            extra_kwargs["user"] = first_admin_username

            # 添加任務並保存返回的 job_id
            job_id = self.scheduler_manager.add_job(
                job_class_string="simple_scheduler.jobs.sample_job.AwesomeJob",
                name="My Awesome Job",
                pub_args=["first parameter", {"second parameter": "can be a dict"}],
                minute="*/1",
                **extra_kwargs,
            )

            if job_id is not None:
                # 重要：手動設置任務-類別關聯
                try:
                    datastore = self.scheduler_manager.get_datastore()
                    datastore.set_job_category(job_id, first_admin_category_id)
                except Exception as e:
                    logger.error(f"為示例任務設置類別時發生錯誤: {e}", exc_info=True)


if __name__ == "__main__":
    SimpleServer.run()
