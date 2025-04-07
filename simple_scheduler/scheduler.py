"""執行排程器程序。"""

import asyncio
import platform

from ndscheduler.server import server
from ndscheduler import settings


class SimpleServer(server.SchedulerServer):

    def post_scheduler_start(self):
        # 新使用者體驗！確保我們至少有一個示範任務！
        jobs = self.scheduler_manager.get_jobs()
        if len(jobs) == 0:
            # 設定任務參數
            argument1 = "這是第一個參數"
            argument2 = "這是第二個參數"

            self.scheduler_manager.add_job(
                job_class_string="simple_scheduler.jobs.sample_job.AwesomeJob",
                name="My Awesome Job",
                pub_args=[argument1, argument2],  # 作為位置參數傳遞
                minute="*/1",
                db_config=settings.DATABASE_CONFIG_DICT,
                db_tablenames=settings.DATABASE_TABLENAMES,
                argument1=argument1,  # 同時作為關鍵字參數傳遞
                argument2=argument2,  # 同時作為關鍵字參數傳遞
            )


if __name__ == "__main__":
    # 修正 Windows 上 Tornado+asyncio 的問題
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    SimpleServer.run()
