"""Ensure there's only one scheduler instancing running."""

import json
import logging
from typing import Optional, Any, List
from uuid import uuid4

from apscheduler.schedulers import tornado as apscheduler_tornado
from apscheduler.triggers.cron import CronTrigger

from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler import utils
from ndscheduler.corescheduler.job import JobBase

logger = logging.getLogger(__name__)


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
        executors.setdefault("default", {"type": "threadpool", "max_workers": constants.DEFAULT_THREAD_POOL_SIZE})
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
        *args,
        **kwargs,
    ) -> Optional[str]:
        """Run a job.

        Args:
            job_class_path: String for job class, e.g., 'myscheduler.jobs.a_job.NiceJob'
            job_id: Job id
            db_class_path: String for datstore class, e.g. 'datastores.DatastoreSqlite'
            *args: List of args (pub_args) provided to the job class to be run
            **kwargs: Keyword arguments (including db_config, db_tablenames, user, etc.)

        Returns:
            str: Execution id if successful, None otherwise
        """
        execution_id = utils.generate_uuid()

        # --- 從 kwargs 獲取 db_config 和 db_tablenames ---
        db_config = kwargs.get("db_config")
        db_tablenames = kwargs.get("db_tablenames")
        kwargs.pop("db_config", None)
        kwargs.pop("db_tablenames", None)

        datastore = utils.get_datastore_instance(db_class_path, db_config, db_tablenames)

        # 獲取 Job 的 category_id
        job_category_id = 0  # 預設值
        try:
            category_info = datastore.get_job_category(job_id)
            if category_info and isinstance(category_info, dict) and "id" in category_info:
                job_category_id = category_info["id"]
            elif isinstance(category_info, int):  # 相容舊版可能直接回傳 ID 的情況
                job_category_id = category_info
        except Exception as cat_err:
            logger.warning(f"為 job {job_id} 獲取 category_id 失敗: {cat_err}")

        try:
            job_class = utils.import_from_path(job_class_path)

            # Add execution record
            datastore.add_execution(
                execution_id,
                job_id,
                constants.EXECUTION_STATUS_SCHEDULED,
                description=job_class.get_scheduled_description(),
                category_id=job_category_id,  # 使用獲取的 category_id
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
    def post_run(cls, job_class: JobBase, job_id: str, execution_id: str, result_json: str, *args, **kwargs) -> None:
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
    def run_scheduler_job(cls, job_class: JobBase, job_id: str, execution_id: str, datastore, *args, **kwargs) -> None:
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

        # --- 確定要使用的 Job ID ---
        # 如果 kwargs 中提供了 job_id (例如重建時)，則使用它，否則生成新的 UUID
        job_id_to_use = kwargs.get("job_id", uuid4().hex)
        # logger.info(f"確定使用的 Job ID: {job_id_to_use}, (是否由外部提供: {'job_id' in kwargs})")

        # 建立 CronTrigger
        trigger = CronTrigger(
            month=month,
            day=day,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.timezone,
        )

        # 獲取資料庫配置 (這些不應傳入最終的 kwargs)
        datastore = self._lookup_jobstore("default")
        db_config = datastore.db_config
        db_tablenames = datastore.table_names

        # --- 準備傳遞給 APScheduler add_job 的 kwargs ---
        # 這個 kwargs 是給 job 執行函數 (BaseScheduler.run_job) 使用的
        job_func_kwargs = {
            "db_config": db_config,  # 內部參數
            "db_tablenames": db_tablenames,  # 內部參數
        }
        # 添加其他從上層傳遞下來的 kwargs (例如 'user')，但要排除 'job_id' 和 'pub_args'
        scheduler_params_to_exclude = {"job_id", "pub_args"}
        for key, value in kwargs.items():
            if key not in scheduler_params_to_exclude:
                job_func_kwargs[key] = value

        # --- 準備傳遞給 APScheduler add_job 的 args ---
        job_func_args = [job_class_string, job_id_to_use, self.datastore_class_path]
        # 將 pub_args (它本身是個 list) 的元素添加到 args 列表中
        if pub_args:
            job_func_args.extend(pub_args)

        # logger.info(f"準備調用 APScheduler add_job: id={job_id_to_use}, name={name}")
        logger.debug(f"APScheduler add_job - args: {job_func_args}")  # 使用新的 args
        logger.debug(f"APScheduler add_job - kwargs: {job_func_kwargs}")

        # 新增任務到排程器 (調用 APScheduler 的 add_job)
        try:
            # 注意：APScheduler 的 add_job 會將 job_id_to_use 添加到傳遞給 func 的 args[1]
            self.add_job(
                func=self.run_job,
                args=job_func_args,  # 使用包含 pub_args 的新 args 列表
                kwargs=job_func_kwargs,  # 傳遞過濾後的 kwargs
                trigger=trigger,
                id=job_id_to_use,  # 明確設定 APScheduler job 的 ID
                name=name,
                replace_existing=True,  # 確保重建時能替換
                misfire_grace_time=constants.DEFAULT_JOB_MISFIRE_GRACE_SEC,
            )
            # logger.info(f"APScheduler add_job 調用成功 for job_id: {job_id_to_use}")
        except Exception as add_job_error:
            logger.error(f"調用 APScheduler add_job 失敗 for job_id: {job_id_to_use}: {add_job_error}", exc_info=True)
            raise  # 將異常重新拋出，讓上層處理

        # 新增稽核日誌 (使用我們決定的 job_id)
        try:
            datastore.add_audit_log(
                job_id=job_id_to_use,  # 使用最終確定的 ID 記錄日誌
                job_name=name,
                event=constants.AUDIT_LOG_ADDED,
                user=kwargs.get("user", ""),  # 從原始 kwargs 中獲取 user
                category_id=kwargs.get("category_id", 0),  # 從原始 kwargs 中獲取 category_id
                description=json.dumps(pub_args),
            )
        except Exception as audit_log_error:
            logger.error(f"添加稽核日誌失敗 for job_id: {job_id_to_use}: {audit_log_error}", exc_info=True)
            # 即使日誌失敗，任務可能已成功添加，所以不在此處拋出異常

        return job_id_to_use  # 返回實際使用的 job ID

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

        # --- 處理觸發器修改 ---
        trigger_keys = {"month", "day", "day_of_week", "hour", "minute"}
        if any(key in kwargs for key in trigger_keys):
            trigger = CronTrigger(
                month=kwargs.pop("month", None),
                day=kwargs.pop("day", None),
                day_of_week=kwargs.pop("day_of_week", None),
                hour=kwargs.pop("hour", None),
                minute=kwargs.pop("minute", None),
                timezone=self.timezone,
            )
            # 使用 reschedule_job 修改觸發器，它不會引發 AttributeError
            self.reschedule_job(job_id, trigger=trigger)

        # --- 過濾可修改的 Job 屬性 ---
        # 常見的可直接修改屬性 (參考 APScheduler Job 類別)
        # MODIFIABLE_JOB_ATTRS = {"name", "max_instances", "misfire_grace_time", "coalesce"}
        MODIFIABLE_JOB_ATTRS = {"name"}
        filtered_kwargs = {}
        for key, value in kwargs.items():
            # 只保留允許修改的屬性，並且排除已處理的觸發器鍵
            if key in MODIFIABLE_JOB_ATTRS and key not in trigger_keys:
                filtered_kwargs[key] = value

        # --- 修改其他 Job 屬性 (只傳遞過濾後的屬性) ---
        if filtered_kwargs:
            self.modify_job(job_id, **filtered_kwargs)

        # --- 新增稽核日誌 (記錄原始意圖修改的內容) ---
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
