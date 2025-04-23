"""Represents the core scheduler instance that actually schedules jobs."""

from apscheduler.executors import pool
import json  # noqa: F401
import logging

from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler import utils

logger = logging.getLogger(__name__)


class SchedulerManager:

    def __init__(
        self,
        scheduler_class_path,
        datastore_class_path,
        db_config=None,
        db_tablenames=None,
        job_coalesce=constants.DEFAULT_JOB_COALESCE,
        job_misfire_grace_sec=constants.DEFAULT_JOB_MISFIRE_GRACE_SEC,
        job_max_instances=constants.DEFAULT_JOB_MAX_INSTANCES,
        thread_pool_size=constants.DEFAULT_THREAD_POOL_SIZE,
        timezone=constants.DEFAULT_TIMEZONE,
    ):
        """
        :param str scheduler_class_path: string path for scheduler, e.g. 'mysched.FancyScheduler'
        :param str datastore_class_path: string path for datastore, e.g. 'datastore.SQLDatastore'
        :param dict db_config: dictionary containing values for db connection
        :param dict db_tablenames: dictionary containing the names for the jobs,
        executions, or audit logs table, e.g. {
            'executions_tablename': 'scheduler_executions',
            'jobs_tablename': 'scheduler_jobs',
            'auditlogs_tablename': 'scheduler_auditlogs',
            'users_tablename': 'scheduler_users',
            'categories_tablename': 'scheduler_categories'
            'job_categories_tablename': 'scheduler_job_categories'
        }
        If any of these keys is not provided, the default table name is selected from constants.py
        :param bool job_coalesce: True by default
        :param int job_misfire_grace_sec: Integer number of seconds
        :param int job_max_instances: Int number of instances
        :param int thread_pool_size: Int thread pool size
        :param str timezone: str timezone to schedule jobs in, e.g. 'UTC'
        """
        datastore = utils.get_datastore_instance(datastore_class_path, db_config, db_tablenames)
        job_stores = {"default": datastore}

        job_default = {
            "coalesce": job_coalesce,
            "misfire_grace_time": job_misfire_grace_sec,
            "max_instances": job_max_instances,
        }

        executors = {"default": pool.ThreadPoolExecutor(thread_pool_size)}

        scheduler_class = utils.import_from_path(scheduler_class_path)
        self.sched = scheduler_class(
            datastore_class_path, jobstores=job_stores, executors=executors, job_defaults=job_default, timezone=timezone
        )

    def get_datastore(self):
        return self.sched._lookup_jobstore("default")

    #
    # Manage the entire scheduler
    #
    def start(self):
        """Start scheduler daemon.
        This is a BLOCKING operation, as internally, apscheduler doesn't
        call wakeup() that is async.
        """
        self.sched.start()

    def stop(self):
        """Stop scheduler daemon.
        This is a BLOCKING operation, as internally, apscheduler doesn't
        call wakeup() that is async.
        """
        self.sched.shutdown()
        self.get_datastore().destroy_instance()

    #
    # Manage jobs
    #
    def add_job(
        self,
        job_class_string,
        name,
        pub_args=None,
        month=None,
        day_of_week=None,
        day=None,
        hour=None,
        minute=None,
        **kwargs,
    ):
        """Add a job. Job infomation will be persistent in the datastore.
        This is a NON-BLOCKING operation, as internally, apscheduler calls wakeup()
        that is async.
        :param str job_class_string: String for job class, e.g., myscheduler.jobs.a_job.NiceJob
        :param str name: String for job name, e.g., Check Melissa job.
        :param pub_args: List for arguments passed to publish method of a task.
        :param str month: String for month cron string, e.g., */10
        :param str day_of_week: String for day of week cron string, e.g., 1-6
        :param str day: String for day cron string, e.g., */1
        :param str hour: String for hour cron string, e.g., */2
        :param str minute: String for minute cron string, e.g., */3
        :param kwargs: Other keyword arguments passed to run_job function.
        :return: String of job id, e.g., 6bca19736d374ef2b3df23eb278b512e
        :rtype: str
        """
        logger.info(f"scheduler_manager.add_job() 收到參數: {kwargs}, {pub_args}")

        # 檢查 category_id 是否在 kwargs 中
        if "category_id" not in kwargs:
            logger.warning("add_job() 未收到 category_id 參數")
        # else:
        #     logger.info(f"add_job() 收到 category_id={kwargs['category_id']}")

        # 處理 pub_args 格式
        if "pub_args" in kwargs and isinstance(kwargs["pub_args"], str):
            kwargs["pub_args"] = None

        return self.sched.add_scheduler_job(
            job_class_string, name, pub_args, month, day_of_week, day, hour, minute, **kwargs
        )

    def pause_job(self, job_id):
        """Pauses the schedule of a job.
        This is a NON-BLOCKING operation, as internally, apscheduler calls wakeup()
        that is async.
        :param str job_id: String for job id to be paused.
        """
        self.sched.pause_job(job_id)

    def get_job(self, job_id):
        """Returns an apscheduler.job.Job instance with category_id attached.
        This is a BLOCKING operation, as internally, apscheduler doesn't
        call wakeup() that is async.
        :param str job_id: String for job id to be returned.
        :return: An apscheduler.job.Job instance with category_id attribute.
        :rtype: apscheduler.job.Job
        """
        return self.sched.get_job(job_id)

    def get_jobs(self, category_id: int | None = None):
        """Returns a list of apscheduler.job.Job instances, optionally filtered by category_id.
        Each Job instance will have the category_id attribute attached.
        This is a BLOCKING operation.
        :param int | None category_id: Optional category ID to filter jobs. If None or 0, returns all jobs.
        :return: A list of apscheduler.job.Job instances with category_id attribute.
        :rtype: list[apscheduler.job.Job]
        """
        datastore = self.get_datastore()
        return datastore.get_jobs(category_id=category_id)

    def get_job_task_class(self, job):
        """Shortcut to get task class.
        :param Job job: Instance of apscheduler.job.Job.
        :return: String for task class of this job.
        :rtype: str
        """
        return job.args[0]

    def remove_job(self, job_id):
        """Removes a job.
        This is a BLOCKING operation, as internally, apscheduler doesn't
        call wakeup() that is async.
        :param str job_id: String for job id to be removed.
        """
        self.sched.remove_job(job_id)

    def resume_job(self, job_id):
        """Removes a job.
        This is a NON-BLOCKING operation, as internally, apscheduler calls wakeup()
        that is async.
        :param str job_id: String for job id to be removed.
        """
        self.sched.resume_job(job_id)

    def modify_job(self, job_id, **kwargs):
        """Modifies a job.
        This is a BLOCKING operation, because it calls get_job() that is blocking, even though
        reschedule() and modify() are both non-blocking.
        :param str job_id: String for job id to be modified.
        :param kwargs: keyword arguments, including:
            - name: String for job name
            - job_class_string: String for job class string, e.g.,
                myscheduler.jobs.a_job.NiceJob
            - pub_args: List of arguments passed to the task.
            - month: String for month cron string, e.g., */10
            - day_of_week: String for day of week cron string, e.g., 1-6
            - day: String for day cron string, e.g., */1
            - hour: String for hour cron string, e.g., */2
            - minute: String for minute cron string, e.g., */3
        """
        self.sched.modify_scheduler_job(job_id, **kwargs)
