"""Handler for executions endpoint."""

from datetime import datetime
from datetime import timedelta

import tornado.gen
import tornado.web

from ndscheduler import settings
from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler import utils
from ndscheduler.server.handlers import base


class Handler(base.BaseHandler):

    def _get_execution(self, execution_id):
        """Returns a dictionary of a job execution info.

        This is a blocking operation.

        Args:
            execution_id (str): Execution id.

        Returns:
            dict: If success, a dictionary of a job execution info; otherwise, a dictionary
                of error message.
        """
        execution = self.datastore.get_execution(execution_id)
        if not execution:
            self.set_status(400)
            return {"error": "Execution not found: %s" % execution_id}
        return execution

    @tornado.concurrent.run_on_executor
    def get_execution(self, execution_id):
        """Wrapper for _get_execution() to run on threaded executor.

        Args:
            execution_id (str): Execution id.

        Returns:
            dict: Job execution info.
        """
        return self._get_execution(execution_id)

    @tornado.gen.coroutine
    def get_execution_yield(self, execution_id):
        """Wrapper for get_execution to run in async mode.

        Args:
            execution_id (str): Execution id.

        Returns:
            dict: Job execution info.
        """
        return_json = yield self.get_execution(execution_id)
        self.finish(return_json)

    def _get_executions(self):
        """Returns a dictionary of executions in a specific time range, filtered by user's category_id.

        This is a blocking operation.

        Returns:
            dict: Executions info.
        """
        # 獲取時間範圍參數
        now = datetime.utcnow()
        time_range_end = self.get_argument("time_range_end", now.isoformat())
        ten_minutes_ago = now - timedelta(minutes=10)
        time_range_start = self.get_argument("time_range_start", ten_minutes_ago.isoformat())

        # 獲取使用者 category_id
        user_info = self.get_current_user()
        user_category_id = user_info.get("category_id", 0) if user_info else 0

        # 根據 category_id 呼叫不同的 datastore 方法
        if user_category_id == 0:
            # category_id 為 0，獲取所有 Executions
            executions = self.datastore.get_executions(time_range_start, time_range_end)
        else:
            # category_id 不為 0，根據分類獲取 Executions
            executions = self.datastore.get_executions_by_category(user_category_id, time_range_start, time_range_end)

        return executions

    @tornado.concurrent.run_on_executor
    def get_executions(self):
        """Wrapper for _get_executions to run on threaded executor.

        Returns:
            dict: Executions info.
        """
        return self._get_executions()

    @tornado.gen.coroutine
    def get_executions_yield(self):
        """Wrapper for get_executions to run in async mode.

        Returns:
            dict: Executions info.
        """
        return_json = yield self.get_executions()
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def get(self, execution_id=None):
        """Returns a execution or multiple executions.

        Handles two endpoints:
            GET /api/v1/executions                 (when execution_id == None)
                It takes two query string parameters:
                - time_range_end - unix epoch timestamp. Default: now
                - time_range_start - unix epoch timestamp. Default: 10 minutes ago.
                These two parameters limit the executions to return:
                time_range_start <= execution.scheduled_time <= time_range_end

            GET /api/v1/executions/{execution_id}  (when execution_id != None)

        Args:
            execution_id (str, optional): Execution id.
        """
        if execution_id is None:
            yield self.get_executions_yield()
        else:
            yield self.get_execution_yield(execution_id)

    def _run_job(self, job_id):
        """Kicks off a job.

        Args:
            job_id (str): Job id.

        Returns:
            dict: A dictionary with the only field of execution_id.
        """
        job = self.scheduler_manager.get_job(job_id)
        if not job:
            self.set_status(400)
            return {"error": "Job not found: %s" % job_id}
        job_name = utils.get_job_name(job)
        args = utils.get_job_args(job)
        kwargs = job.kwargs.copy()  # 創建一個副本以避免修改原始對象

        # 確保這些參數不在 kwargs 中
        kwargs.pop("db_config", None)
        kwargs.pop("db_class_path", None)
        kwargs.pop("db_tablenames", None)

        scheduler = utils.import_from_path(settings.SCHEDULER_CLASS)
        execution_id = scheduler.run_job(
            job_name,
            job_id,
            settings.DATABASE_CLASS,
            self.datastore.db_config,
            self.datastore.table_names,
            *args,
            **kwargs
        )

        # Audit log
        self.datastore.add_audit_log(
            job_id,
            job.name,
            constants.AUDIT_LOG_CUSTOM_RUN,
            user=self.username,
            category_id=getattr(job, "category_id", 0),
            description=execution_id,
        )

        return {"execution_id": execution_id}

    @tornado.concurrent.run_on_executor
    def run_job(self, job_id):
        """Wrapper for _run_job() to run on threaded executor.

        Args:
            job_id (str): String for a job id.

        Returns:
            dict: A dictionary with the only field of execution_id.
        """
        return self._run_job(job_id)

    @tornado.gen.coroutine
    def run_job_yield(self, job_id):
        """Wrapper for run_job to run in async mode.

        Args:
            job_id (str): Job id.

        Returns:
            dict: A dictionary with the only field of execution_id.
        """
        return_json = yield self.run_job(job_id)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def post(self, job_id):
        """Runs a job.

        Handles an endpoint:
            POST /api/v1/executions

        Args:
            job_id (str): String for job id.
        """
        yield self.run_job_yield(job_id)

    @tornado.web.removeslash
    def delete(self, job_id):
        """Stops a job execution.

        Handles an endpoint:
            POST /api/v1/executions

        Args:
            job_id (str): Job id.
        """
        raise tornado.web.HTTPError(501, "Not implemented yet.")
