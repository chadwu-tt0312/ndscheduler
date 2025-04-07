"""Ensure there's only one scheduler instancing running."""

import json
import logging
from typing import Optional, Dict, Any, List

from apscheduler.schedulers import tornado as apscheduler_tornado
from apscheduler.triggers.cron import CronTrigger

from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler import utils
from ndscheduler.corescheduler.job import JobBase


class BaseScheduler(apscheduler_tornado.TornadoScheduler):
    """It's a scheduler instance."""

    # Seconds to wake up to see if it's okay to run.
    DEFAULT_WAIT_SECONDS = 60

    def __init__(self, datastore_class_path: str, *args, **kwargs):
        """Initialize the scheduler.

        Args:
            datastore_class_path: Path to the datastore class
            *args: Additional positional arguments for TornadoScheduler
            **kwargs: Additional keyword arguments for TornadoScheduler
        """
        self.datastore_class_path = datastore_class_path

        # Set default job defaults if not provided
        job_defaults = kwargs.get("job_defaults", {})
        job_defaults.setdefault("coalesce", True)
        job_defaults.setdefault("max_instances", 3)
        job_defaults.setdefault("misfire_grace_time", constants.DEFAULT_JOB_MISFIRE_GRACE_SEC)
        kwargs["job_defaults"] = job_defaults

        # Set default executor config if not provided
        executors = kwargs.get("executors", {})
        executors.setdefault(
            "default", {"type": "threadpool", "max_workers": constants.DEFAULT_THREAD_POOL_SIZE}
        )
        kwargs["executors"] = executors

        super(BaseScheduler, self).__init__(*args, **kwargs)

        # Configure logging
        logging.getLogger("apscheduler").setLevel(logging.INFO)

    @classmethod
    def is_okay_to_run(cls, datastore) -> bool:
        """Determine if it's okay to schedule jobs.
        Could override this function to dynamically decide whether to run jobs by current process.
        Typically, we try to avoid running multiple scheduler processes that schedule same jobs.

        Args:
            datastore: A DatastoreBase instance.

        Returns:
            bool: True if it's okay to run jobs, False otherwise.
        """
        return True

    @classmethod
    def run_job(
        cls,
        job_class_path: str,
        job_id: str,
        db_class_path: str,
        db_config: Optional[Dict[str, Any]],
        db_tablenames: Optional[Dict[str, str]],
        *args,
        **kwargs,
    ) -> Optional[str]:
        """Run a job.

        Args:
            job_class_path: String for job class, e.g., 'myscheduler.jobs.a_job.NiceJob'
            job_id: Job id
            db_class_path: String for datstore class, e.g. 'datastores.DatastoreSqlite'
            db_config: Dictionary containing values for db connection
            db_tablenames: Dictionary containing the names for the jobs,
                executions, or audit logs table
            *args: List of args provided to the job class to be run
            **kwargs: Keyword arguments

        Returns:
            str: Execution id if successful, None otherwise
        """
        execution_id = utils.generate_uuid()
        datastore = utils.get_datastore_instance(db_class_path, db_config, db_tablenames)

        try:
            job_class = utils.import_from_path(job_class_path)

            # Add execution record
            datastore.add_execution(
                execution_id,
                job_id,
                constants.EXECUTION_STATUS_SCHEDULED,
                description=job_class.get_scheduled_description(),
            )

            # Run the job
            cls.run_scheduler_job(job_class, job_id, execution_id, datastore, *args, **kwargs)

        except Exception as e:
            logging.exception(f"Error running job {job_id}: {str(e)}")
            datastore.update_execution(
                execution_id,
                state=constants.EXECUTION_STATUS_SCHEDULED_ERROR,
                description=JobBase.get_scheduled_error_description(),
                result=JobBase.get_scheduled_error_result(),
            )
            return None

        return execution_id

    @classmethod
    def pre_run(cls, job_class: JobBase, job_id: str, execution_id: str, *args, **kwargs) -> None:
        """Do any preprocessing before running the job.
        Override this function for your own implementation.

        Args:
            job_class: Instance of job class
            job_id: Job id
            execution_id: Execution id
            *args: List of args
            **kwargs: Keyword Arguments
        """
        pass

    @classmethod
    def post_run(
        cls, job_class: JobBase, job_id: str, execution_id: str, result_json: str, *args, **kwargs
    ) -> None:
        """Do any postprocessing after running the job.
        Override this function for your own implementation.

        Args:
            job_class: Instance of job class
            job_id: Job id
            execution_id: Execution id
            result_json: JSON result from job run
            *args: List of args
            **kwargs: Keyword Arguments
        """
        pass

    @classmethod
    def run_scheduler_job(
        cls, job_class: JobBase, job_id: str, execution_id: str, datastore, *args, **kwargs
    ) -> None:
        """Run a job.

        Args:
            job_class: An instance of the job to run
            job_id: Job id
            execution_id: Execution id
            datastore: A datastore instance
            *args: List of args provided to the job class to be run
            **kwargs: Keyword arguments
        """
        cls.pre_run(job_class, job_id, execution_id, *args, **kwargs)

        try:
            # Update execution status to running
            datastore.update_execution(
                execution_id,
                state=constants.EXECUTION_STATUS_RUNNING,
                hostname=utils.get_hostname(),
                pid=utils.get_pid(),
                description=job_class.get_running_description(),
            )

            # Run the job
            result = job_class.run_job(job_id, execution_id, *args, **kwargs)
            result_json = json.dumps(result, indent=4, sort_keys=True)

            # Update execution status to succeeded
            datastore.update_execution(
                execution_id,
                state=constants.EXECUTION_STATUS_SUCCEEDED,
                description=job_class.get_succeeded_description(result),
                result=result_json,
            )

            cls.post_run(job_class, job_id, execution_id, result_json, *args, **kwargs)

        except Exception as e:
            logging.exception(f"Error executing job {job_id}: {str(e)}")
            datastore.update_execution(
                execution_id,
                state=constants.EXECUTION_STATUS_FAILED,
                description=job_class.get_failed_description(),
                result=job_class.get_failed_result(),
            )

    def add_scheduler_job(
        self,
        job_class_string: str,
        name: str,
        pub_args: Optional[List[Any]] = None,
        month: Optional[str] = None,
        day_of_week: Optional[str] = None,
        day: Optional[str] = None,
        hour: Optional[str] = None,
        minute: Optional[str] = None,
        **kwargs,
    ) -> str:
        """新增一個任務。任務資訊會被持久化到資料庫中。

        Args:
            job_class_string: 任務類別字串，例如：myscheduler.jobs.a_job.NiceJob
            name: 任務名稱，例如：檢查任務
            pub_args: 傳遞給任務發布方法的參數列表
            month: 月份的 cron 字串，例如：*/10
            day_of_week: 星期的 cron 字串，例如：1-6
            day: 日期的 cron 字串，例如：*/1
            hour: 小時的 cron 字串，例如：*/2
            minute: 分鐘的 cron 字串，例如：*/3
            **kwargs: 其他傳遞給 run_job 函數的關鍵字參數

        Returns:
            str: 任務 ID
        """
        if not pub_args:
            pub_args = []

        job_id = utils.generate_uuid()

        # 建立 CronTrigger
        trigger = CronTrigger(
            month=month,
            day=day,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.timezone,
        )

        # 獲取資料庫配置
        datastore = self._lookup_jobstore("default")
        db_config = datastore.db_config
        db_tablenames = datastore.table_names

        # 新增任務到排程器
        self.add_job(
            func=self.run_job,
            args=[job_class_string, job_id, self.datastore_class_path],
            kwargs={
                "db_config": db_config,
                "db_tablenames": db_tablenames,
                "pub_args": pub_args,
                **kwargs,
            },
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True,
            misfire_grace_time=constants.DEFAULT_JOB_MISFIRE_GRACE_SEC,
        )

        # 新增稽核日誌
        datastore.add_audit_log(
            job_id=job_id,
            job_name=name,
            event=constants.AUDIT_LOG_ADDED,
            user=kwargs.get("user", ""),
            description=json.dumps(pub_args),
        )

        return job_id

    def modify_scheduler_job(self, job_id: str, **kwargs) -> None:
        """Modify a job.

        Args:
            job_id: String for job id to be modified.
            **kwargs: Keyword arguments, including:
                - name: String for job name
                - job_class_string: String for job class string
                - pub_args: List of arguments passed to the task
                - month: String for month cron string
                - day_of_week: String for day of week cron string
                - day: String for day cron string
                - hour: String for hour cron string
                - minute: String for minute cron string
        """
        job = self.get_job(job_id)
        if not job:
            return

        # Create new trigger if cron strings are modified
        if any(key in kwargs for key in ["month", "day", "day_of_week", "hour", "minute"]):
            trigger = CronTrigger(
                month=kwargs.pop("month", None),
                day=kwargs.pop("day", None),
                day_of_week=kwargs.pop("day_of_week", None),
                hour=kwargs.pop("hour", None),
                minute=kwargs.pop("minute", None),
                timezone=self.timezone,
            )
            self.reschedule_job(job_id, trigger=trigger)

        # Modify other job attributes
        self.modify_job(job_id, **kwargs)

        # Add audit log
        datastore = self._lookup_jobstore("default")
        datastore.add_audit_log(
            job_id=job_id,
            job_name=kwargs.get("name", job.name),
            event=constants.AUDIT_LOG_MODIFIED,
            user=kwargs.get("user", ""),
            description=json.dumps(kwargs.get("pub_args", [])),
        )

    def _process_jobs(self):
        """Process due jobs.

        :return: Seconds to wait before next processing cycle
        :rtype: int
        """
        if self.is_okay_to_run(self._lookup_jobstore("default")):
            return super(apscheduler_tornado.TornadoScheduler, self)._process_jobs()
        else:
            return self.DEFAULT_WAIT_SECONDS
