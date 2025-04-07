"""Base class to represent datastore."""

import logging
import dateutil.tz
import dateutil.parser
from apscheduler.jobstores import sqlalchemy as sched_sqlalchemy
from sqlalchemy import desc, select, MetaData
from sqlalchemy.orm import Session
from datetime import datetime

from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler import utils
from ndscheduler.corescheduler.datastore import tables

logger = logging.getLogger(__name__)


class DatastoreBase(sched_sqlalchemy.SQLAlchemyJobStore):

    instance = None

    @classmethod
    def get_instance(cls, db_config=None, table_names=None):
        if not cls.instance:
            cls.instance = cls(db_config, table_names)
        return cls.instance

    @classmethod
    def destroy_instance(cls):
        cls.instance = None

    def __init__(self, db_config, table_names):
        """Initialize the datastore.

        Args:
            db_config (dict): dictionary containing values for db connection
            table_names (dict): dictionary containing the names for the jobs,
                executions, or audit logs table, e.g. {
                'executions_tablename': 'scheduler_executions',
                'jobs_tablename': 'scheduler_jobs',
                'auditlogs_tablename': 'scheduler_auditlogs'
            }
            If any of these keys is not provided, the default table name is
            selected from constants.py
        """
        self.metadata = MetaData()
        self.table_names = table_names
        self.db_config = db_config

        executions_tablename = constants.DEFAULT_EXECUTIONS_TABLENAME
        jobs_tablename = constants.DEFAULT_JOBS_TABLENAME
        auditlogs_tablename = constants.DEFAULT_AUDIT_LOGS_TABLENAME
        if table_names:
            if "executions_tablename" in table_names:
                executions_tablename = table_names["executions_tablename"]

            if "jobs_tablename" in table_names:
                jobs_tablename = table_names["jobs_tablename"]

            if "auditlogs_tablename" in table_names:
                auditlogs_tablename = table_names["auditlogs_tablename"]

        self.executions_table = tables.get_execution_table(self.metadata, executions_tablename)
        self.auditlogs_table = tables.get_auditlogs_table(self.metadata, auditlogs_tablename)

        super(DatastoreBase, self).__init__(url=self.get_db_url(), tablename=jobs_tablename)

        self.metadata.create_all(self.engine)

    def get_db_url(self):
        """Get the database URL.

        Returns:
            str: Database url. See: http://docs.sqlalchemy.org/en/latest/core/engines.html
        """
        raise NotImplementedError("Please implement this function.")

    def add_execution(self, execution_id, job_id, state, **kwargs):
        """Insert a record of execution to database.

        Args:
            execution_id (str): Execution id.
            job_id (str): Job id.
            state (int): Execution state. See ndscheduler.constants.EXECUTION_*
            **kwargs: Additional execution parameters.
        """
        execution = {"eid": execution_id, "job_id": job_id, "state": state}
        execution.update(kwargs)
        with Session(self.engine) as session:
            stmt = self.executions_table.insert().values(**execution)
            session.execute(stmt)
            session.commit()

    def get_execution(self, execution_id):
        """Returns execution dict.

        Args:
            execution_id (str): Execution id.

        Returns:
            dict: Dictionary containing execution info.
        """
        with Session(self.engine) as session:
            stmt = select(self.executions_table).where(self.executions_table.c.eid == execution_id)
            result = session.execute(stmt)
            row = result.first()
            if row:
                return self._build_execution(row)
            return None

    def update_execution(self, execution_id, **kwargs):
        """Update execution in database.

        Args:
            execution_id (str): Execution id.
            **kwargs: Fields to update.
        """
        with Session(self.engine) as session:
            stmt = (
                self.executions_table.update()
                .where(self.executions_table.c.eid == execution_id)
                .values(**kwargs)
            )
            session.execute(stmt)
            session.commit()

    def _build_execution(self, row):
        """Return job execution info from a row of scheduler_execution table.

        Args:
            row: A row instance of scheduler_execution table.

        Returns:
            dict: A dictionary of job execution info.
        """
        return_json = {
            "execution_id": row.eid,
            "state": constants.EXECUTION_STATUS_DICT[row.state],
            "hostname": row.hostname,
            "pid": row.pid,
            "task_id": row.task_id,
            "description": row.description,
            "result": row.result,
            "scheduled_time": self.get_time_isoformat_from_db(row.scheduled_time),
            "updated_time": self.get_time_isoformat_from_db(row.updated_time),
        }
        job = self.lookup_job(row.job_id)
        if job:
            return_json["job"] = {
                "job_id": job.id,
                "name": job.name,
                "task_name": utils.get_job_name(job),
                "pub_args": utils.get_job_args(job),
            }
            return_json["job"].update(utils.get_cron_strings(job))
        return return_json

    def get_time_isoformat_from_db(self, time_object):
        """Convert time object from database to iso 8601 format.

        Args:
            time_object: A time object from database, which is different on different
                databases. Subclass of this class for specific database has to override
                this function.

        Returns:
            str: ISO 8601 format string
        """
        return time_object.isoformat()

    def get_executions(self, time_range_start, time_range_end):
        """Returns info for multiple job executions.

        Args:
            time_range_start (str): ISO format for time range starting point.
            time_range_end (str): ISO format for time range ending point.

        Returns:
            dict: A dictionary of multiple execution info, e.g.,
                {
                    'executions': [...]
                }
                Sorted by updated_time.
        """
        utc = dateutil.tz.gettz("UTC")
        start_time = dateutil.parser.parse(time_range_start).replace(tzinfo=utc)
        end_time = dateutil.parser.parse(time_range_end).replace(tzinfo=utc)

        with Session(self.engine) as session:
            stmt = (
                select(self.executions_table)
                .where(self.executions_table.c.scheduled_time.between(start_time, end_time))
                .order_by(desc(self.executions_table.c.updated_time))
            )
            result = session.execute(stmt)
            return {"executions": [self._build_execution(row) for row in result]}

    def add_audit_log(self, job_id, job_name, event, **kwargs):
        """新增一筆稽核日誌。

        Args:
            job_id (str): 任務 ID 字串。
            job_name (str): 任務名稱字串。
            event (int): 事件整數值。
            **kwargs: 額外的稽核日誌參數。

        Raises:
            ValueError: 如果參數無效。
            SQLAlchemyError: 如果資料庫操作失敗。
        """
        try:
            if not job_id or not job_name:
                raise ValueError("job_id and job_name are required")

            audit_log = {
                "job_id": job_id,
                "job_name": job_name,
                "event": event,
                "user": kwargs.get("user", ""),
                "description": kwargs.get("description", ""),
            }

            with Session(self.engine) as session:
                stmt = self.auditlogs_table.insert().values(**audit_log)
                session.execute(stmt)
                session.commit()
        except Exception as e:
            raise ValueError(f"Failed to add audit log: {str(e)}")

    def get_audit_logs(self, time_range_start, time_range_end):
        """取得指定時間範圍內的稽核日誌。

        Args:
            time_range_start (str): 時間範圍起點的 ISO 格式。
            time_range_end (str): 時間範圍終點的 ISO 格式。

        Returns:
            dict: 包含多筆稽核日誌資訊的字典，例如：
                {
                    'audit_logs': [...]
                }
                依照更新時間排序。

        Raises:
            ValueError: 如果時間格式無效。
            SQLAlchemyError: 如果資料庫操作失敗。
        """
        try:
            utc = dateutil.tz.gettz("UTC")
            start_time = dateutil.parser.parse(time_range_start).replace(tzinfo=utc)
            end_time = dateutil.parser.parse(time_range_end).replace(tzinfo=utc)

            with Session(self.engine) as session:
                stmt = (
                    select(self.auditlogs_table)
                    .where(self.auditlogs_table.c.created_time.between(start_time, end_time))
                    .order_by(desc(self.auditlogs_table.c.created_time))
                )
                result = session.execute(stmt)
                return {"audit_logs": [self._build_audit_log(row) for row in result]}
        except Exception as e:
            raise ValueError(f"Failed to get audit logs: {str(e)}")

    def _build_audit_log(self, row):
        """從稽核日誌資料表的一行建立稽核日誌資訊。

        Args:
            row: 稽核日誌資料表的一行實例。

        Returns:
            dict: 稽核日誌資訊的字典。
        """
        try:
            # 確保時間欄位有值
            created_time = row.created_time
            if not created_time:
                created_time = datetime.utcnow()

            # 確保時間有時區資訊
            if not created_time.tzinfo:
                created_time = created_time.replace(tzinfo=dateutil.tz.gettz("UTC"))

            # 處理 description 欄位
            description = row.description
            if description:
                try:
                    # 如果是 JSON 字串，保持原樣
                    if description.startswith("{") and description.endswith("}"):
                        description = description
                    # 如果不是 JSON，確保是字串格式
                    else:
                        description = str(description)
                except Exception:
                    description = str(description)
            else:
                description = ""

            return {
                "job_id": row.job_id or "",
                "job_name": row.job_name or "",
                "event": constants.AUDIT_LOG_DICT.get(row.event, "UNKNOWN"),
                "user": row.user or "",
                "description": description,
                "created_time": self.get_time_isoformat_from_db(created_time),
            }
        except Exception as e:
            logger.error(f"建立稽核日誌資訊失敗：{str(e)}", exc_info=True)
            # 發生錯誤時返回基本資訊
            return {
                "job_id": getattr(row, "job_id", "") or "",
                "job_name": getattr(row, "job_name", "") or "",
                "event": constants.AUDIT_LOG_DICT.get(getattr(row, "event", None), "UNKNOWN"),
                "user": getattr(row, "user", "") or "",
                "description": getattr(row, "description", "") or "",
                "created_time": self.get_time_isoformat_from_db(datetime.utcnow()),
            }
