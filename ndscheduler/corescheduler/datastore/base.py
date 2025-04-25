"""Base class to represent datastore."""

import logging
import dateutil.tz
import dateutil.parser
import bcrypt
from apscheduler.jobstores import sqlalchemy as sched_sqlalchemy
from sqlalchemy import desc, select, MetaData, and_
from sqlalchemy.orm import Session
from datetime import datetime
from apscheduler.job import Job
import pytz

from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler import utils
from ndscheduler.corescheduler.datastore import tables
from ndscheduler import default_settings

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
                'auditlogs_tablename': 'scheduler_auditlogs',
                'users_tablename': 'scheduler_users',
                'categories_tablename': 'scheduler_categories',
                'job_categories_tablename': 'scheduler_job_categories'
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
        users_tablename = constants.DEFAULT_USERS_TABLENAME
        categories_tablename = constants.DEFAULT_CATEGORIES_TABLENAME
        job_categories_tablename = "scheduler_job_categories"

        if table_names:
            if "executions_tablename" in table_names:
                executions_tablename = table_names["executions_tablename"]

            if "jobs_tablename" in table_names:
                jobs_tablename = table_names["jobs_tablename"]

            if "auditlogs_tablename" in table_names:
                auditlogs_tablename = table_names["auditlogs_tablename"]

            if "users_tablename" in table_names:
                users_tablename = table_names["users_tablename"]

            if "categories_tablename" in table_names:
                categories_tablename = table_names["categories_tablename"]

            if "job_categories_tablename" in table_names:
                job_categories_tablename = table_names["job_categories_tablename"]

        # 初始化 SQLAlchemy 基類
        super(DatastoreBase, self).__init__(url=self.get_db_url(), tablename=jobs_tablename)

        try:
            # 先建立沒有外鍵依賴的資料表
            self.categories_table = tables.get_categories_table(self.metadata, categories_tablename)
            self.users_table = tables.get_users_table(self.metadata, users_tablename)

            # 再建立有外鍵依賴的資料表
            self.executions_table = tables.get_execution_table(self.metadata, executions_tablename)
            self.auditlogs_table = tables.get_auditlogs_table(self.metadata, auditlogs_tablename)
            self.job_categories_table = tables.get_job_categories_table(self.metadata, job_categories_tablename)

            # 創建所有表格
            self.metadata.create_all(self.engine)

            # 初始化使用者資料
            self.init_users()
            # 初始化分類資料
            self.init_categories()

            logger.debug("資料庫初始化成功")
        except Exception as e:
            logger.error("資料庫初始化失敗: %s", str(e))
            raise

    def init_users(self):
        """初始化使用者資料。

        如果使用者表格為空，則從 default_settings.py 中讀取預設使用者資料並創建。
        """
        try:
            # 檢查是否有使用者資料
            with Session(self.engine) as session:
                stmt = select(self.users_table)
                result = session.execute(stmt)
                if not result.first():  # 如果沒有任何使用者資料
                    # 從 default_settings.py 讀取預設使用者資料
                    default_users = default_settings.AUTH_CREDENTIALS
                    for username, hashed_password in default_users.items():
                        # 新增使用者
                        stmt = self.users_table.insert().values(
                            username=username,
                            password=hashed_password,  # 密碼已經是 bcrypt 雜湊值
                            category_id=0,  # 預設分類 ID=0=all
                            is_admin=True,  # 預設使用者設為管理員
                            is_permission=True,
                            created_at=utils.get_current_datetime(),
                        )
                        session.execute(stmt)
                    session.commit()
                    logger.info("已創建預設使用者")
        except Exception as e:
            logger.error("初始化使用者資料失敗: %s", str(e))

    def init_categories(self):
        """初始化分類資料。

        如果分類表格為空，則創建。
        """
        try:
            # 檢查是否有分類資料
            with Session(self.engine) as session:
                stmt = select(self.categories_table)
                result = session.execute(stmt)
                if not result.first():  # 如果沒有任何分類資料
                    # 新增分類資料
                    stmt = self.categories_table.insert().values(
                        id=0,
                        name="all",
                        description="all description",
                        created_at=utils.get_current_datetime(),
                    )
                    session.execute(stmt)
                    stmt = self.categories_table.insert().values(
                        id=1,
                        name="dev",
                        description="dev description",
                        created_at=utils.get_current_datetime(),
                    )
                    session.execute(stmt)
                    session.commit()
                    logger.info("已創建預設分類")
        except Exception as e:
            logger.error("初始化分類資料失敗: %s", str(e))

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
            stmt = self.executions_table.update().where(self.executions_table.c.eid == execution_id).values(**kwargs)
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
        if time_object is None:
            return None

        try:
            if isinstance(time_object, str):
                # 嘗試解析常見的資料庫時間格式
                try:
                    date = datetime.datetime.strptime(time_object, "%Y/%m/%d %H:%M:%S.%f")
                except ValueError:
                    date = dateutil.parser.isoparse(time_object)
            else:
                date = time_object

            if not isinstance(date, datetime.datetime):
                raise ValueError("無法辨識的時間物件類型")

            # Assume UTC if no timezone info
            if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
                # logger.warning(f"時間物件 {date} 缺少時區資訊，假設為 UTC")
                date = pytz.utc.localize(date)
            else:
                # Convert to UTC
                date = date.astimezone(pytz.utc)
            return date.isoformat()
        except Exception as e:
            logger.error(f"轉換資料庫時間 '{time_object}' 失敗: {e}")
            return str(time_object)  # Fallback to string representation if conversion fails

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
                "category_id": kwargs.get("category_id", 0),
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

    def add_user(self, username, password, category_id, is_admin=False, is_permission=False):
        """新增使用者。

        Args:
            username (str): 使用者名稱
            password (str): 使用者密碼（將被加密儲存）
            category_id (int): 分類 ID。
            is_admin (bool): 是否為管理員
            is_permission (bool): 是否有修改權限

        Raises:
            ValueError: 如果提供的 category_id 無效。
        """
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        with Session(self.engine) as session:
            # --- 驗證 category_id ---
            if category_id is None:  # 輸入的 category_id 不存在，也是出現此錯誤，而不是執行 else 的程式 # TODO: ???
                # 如果 category_id 是 None，直接報錯
                logger.error("Category ID is required.")
                raise ValueError("Category ID is required.")
            else:
                # 檢查它是否存在於 categories 表中
                category_exists_stmt = select(self.categories_table.c.id).where(
                    self.categories_table.c.id == category_id
                )
                category_result = session.execute(category_exists_stmt).first()
                if not category_result:
                    raise ValueError(f"Invalid category ID: {category_id}")
            # --- 結束驗證 ---

            stmt = self.users_table.insert().values(
                username=username,
                password=hashed.decode("utf-8"),
                category_id=category_id,
                is_admin=is_admin,
                is_permission=is_permission,
            )
            session.execute(stmt)
            session.commit()

    def get_user(self, username):
        """取得使用者資訊。

        Args:
            username (str): 使用者名稱

        Returns:
            dict: 使用者資訊
        """
        with Session(self.engine) as session:
            stmt = select(self.users_table).where(self.users_table.c.username == username)
            result = session.execute(stmt)
            row = result.first()
            if row:
                return {
                    "id": row.id,
                    "username": row.username,
                    "category_id": row.category_id,
                    "is_admin": row.is_admin,
                    "is_permission": row.is_permission,
                    "created_at": self.get_time_isoformat_from_db(row.created_at),
                    "updated_at": self.get_time_isoformat_from_db(row.updated_at),
                }
            return None

    def check_user_exists(self, username, session=None):
        """檢查使用者是否存在。

        這是一個更輕量的方法，只檢查使用者是否存在，不返回完整的使用者資料。
        如果提供了 session 參數，將使用該 session 而不是建立新的 session。

        Args:
            username (str): 使用者名稱
            session (Session, optional): SQLAlchemy Session 物件. Defaults to None.

        Returns:
            bool: 使用者是否存在
        """
        # 使用傳入的 session 或建立新的 session
        if session:
            # 使用傳入的 session
            stmt = select(self.users_table.c.id).where(self.users_table.c.username == username)
            result = session.execute(stmt)
            return result.first() is not None
        else:
            # 建立新的 session
            with Session(self.engine) as session:
                stmt = select(self.users_table.c.id).where(self.users_table.c.username == username)
                result = session.execute(stmt)
                return result.first() is not None

    def get_users(self):
        """取得所有使用者，依使用者名稱排序。

        Returns:
            list: 以使用者名稱排序的使用者列表
        """
        with Session(self.engine) as session:
            # 使用排序子句來按使用者名稱排序
            stmt = select(self.users_table).order_by(self.users_table.c.username)
            result = session.execute(stmt)
            return [
                {
                    "id": row.id,
                    "username": row.username,
                    "category_id": row.category_id,
                    "is_admin": row.is_admin,
                    "is_permission": row.is_permission,
                    "created_at": self.get_time_isoformat_from_db(row.created_at),
                    "updated_at": self.get_time_isoformat_from_db(row.updated_at),
                }
                for row in result
            ]

    def verify_user(self, username, password):
        """驗證使用者密碼。

        Args:
            username (str): 使用者名稱
            password (str): 使用者密碼

        Returns:
            bool: 驗證是否成功
        """
        with Session(self.engine) as session:
            stmt = select(self.users_table).where(self.users_table.c.username == username)
            result = session.execute(stmt)
            row = result.first()
            if row:
                return bcrypt.checkpw(password.encode("utf-8"), row.password.encode("utf-8"))
            return False

    def add_category(self, name, description=None):
        """新增分類。

        Args:
            name (str): 分類名稱
            description (str): 分類描述
        """
        with Session(self.engine) as session:
            stmt = self.categories_table.insert().values(name=name, description=description)
            session.execute(stmt)
            session.commit()

    def get_category(self, category_id):
        """取得分類資訊。

        Args:
            category_id (int): 分類 ID

        Returns:
            dict: 分類資訊
        """
        with Session(self.engine) as session:
            stmt = select(self.categories_table).where(self.categories_table.c.id == category_id)
            result = session.execute(stmt)
            row = result.first()
            if row:
                return {
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "created_at": self.get_time_isoformat_from_db(row.created_at),
                    "updated_at": self.get_time_isoformat_from_db(row.updated_at),
                }
            return None

    def get_categories(self):
        """取得所有分類，依名稱排序。

        Returns:
            list: 以分類名稱排序的分類列表
        """
        with Session(self.engine) as session:
            # 使用排序子句來按名稱排序
            stmt = select(self.categories_table).order_by(self.categories_table.c.name)
            result = session.execute(stmt)
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "created_at": self.get_time_isoformat_from_db(row.created_at),
                    "updated_at": self.get_time_isoformat_from_db(row.updated_at),
                }
                for row in result
            ]

    def get_executions_by_category(self, category_id, time_range_start, time_range_end):
        """取得特定分類的執行記錄。

        Args:
            category_id (int): 分類 ID
            time_range_start (str): 開始時間（ISO 格式）
            time_range_end (str): 結束時間（ISO 格式）

        Returns:
            dict: 執行記錄列表
        """
        utc = dateutil.tz.gettz("UTC")
        start_time = dateutil.parser.parse(time_range_start).replace(tzinfo=utc)
        end_time = dateutil.parser.parse(time_range_end).replace(tzinfo=utc)

        with Session(self.engine) as session:
            stmt = (
                select(self.executions_table)
                .where(
                    and_(
                        self.executions_table.c.category_id == category_id,
                        self.executions_table.c.scheduled_time.between(start_time, end_time),
                    )
                )
                .order_by(desc(self.executions_table.c.updated_time))
            )
            result = session.execute(stmt)
            return {"executions": [self._build_execution(row) for row in result]}

    def get_audit_logs_by_category(self, category_id, time_range_start, time_range_end):
        """取得特定分類的稽核日誌。

        Args:
            category_id (int): 分類 ID
            time_range_start (str): 開始時間（ISO 格式）
            time_range_end (str): 結束時間（ISO 格式）

        Returns:
            dict: 稽核日誌列表
        """
        utc = dateutil.tz.gettz("UTC")
        start_time = dateutil.parser.parse(time_range_start).replace(tzinfo=utc)
        end_time = dateutil.parser.parse(time_range_end).replace(tzinfo=utc)

        with Session(self.engine) as session:
            stmt = (
                select(self.auditlogs_table)
                .where(
                    and_(
                        self.auditlogs_table.c.category_id == category_id,
                        self.auditlogs_table.c.created_time.between(start_time, end_time),
                    )
                )
                .order_by(desc(self.auditlogs_table.c.created_time))
            )
            result = session.execute(stmt)
            return {"audit_logs": [self._build_audit_log(row) for row in result]}

    def set_job_category(self, job_id, category_id):
        """設定任務的分類。

        Args:
            job_id (str): 任務 ID
            category_id (int): 分類 ID
        """
        try:
            # 首先驗證 category_id 是否有效
            if category_id is None:
                logger.warning(f"設定任務 {job_id} 的分類時收到無效的 category_id: {category_id}")
                return

            # logger.info(f"開始設定任務 {job_id} 的分類為 {category_id}")

            with Session(self.engine) as session:
                # 先檢查是否已存在關聯
                check_stmt = select(self.job_categories_table).where(self.job_categories_table.c.job_id == job_id)
                existing = session.execute(check_stmt).first()
                if existing:
                    logger.info(f"任務 {job_id} 已存在分類關聯: {existing.category_id}，將更新為 {category_id}")

                # 先刪除現有的分類關聯
                delete_stmt = self.job_categories_table.delete().where(self.job_categories_table.c.job_id == job_id)
                delete_result = session.execute(delete_stmt)
                # logger.info(f"刪除任務 {job_id} 的現有分類關聯，影響 {delete_result.rowcount} 行")

                # 新增新的分類關聯
                insert_stmt = self.job_categories_table.insert().values(
                    job_id=job_id,
                    category_id=category_id,
                )
                insert_result = session.execute(insert_stmt)
                # logger.info(f"為任務 {job_id} 新增分類關聯 {category_id}，結果: {insert_result.rowcount} 行已插入")

                # 更新該任務的稽核日誌記錄，確保 category_id 一致
                # 只更新最近的 AUDIT_LOG_ADDED 事件記錄
                update_stmt = (
                    self.auditlogs_table.update()
                    .where(
                        and_(
                            self.auditlogs_table.c.job_id == job_id,
                            self.auditlogs_table.c.event == constants.AUDIT_LOG_ADDED,
                        )
                    )
                    .values(category_id=category_id)
                )
                update_result = session.execute(update_stmt)
                # logger.info(f"更新任務 {job_id} 的稽核日誌記錄的 category_id，影響 {update_result.rowcount} 行")

                session.commit()
                # logger.info(f"成功設定任務 {job_id} 的分類為 {category_id}")

                # 最後確認關聯是否已存在
                confirm_stmt = select(self.job_categories_table).where(self.job_categories_table.c.job_id == job_id)
                confirm_result = session.execute(confirm_stmt).first()
                if confirm_result:
                    logger.info(f"Updated job [{job_id}], category_id = {confirm_result.category_id}")
                else:
                    logger.warning(f"無法確認任務 {job_id} 的分類設定，未找到相關記錄")
        except Exception as e:
            logger.error(f"設定任務 {job_id} 的分類為 {category_id} 時發生錯誤: {e}", exc_info=True)
            raise

    def get_job_category(self, job_id):
        """取得任務的分類 ID。

        Args:
            job_id (str): 任務 ID

        Returns:
            int | None: 分類 ID，如果沒有則返回 None
        """
        with Session(self.engine) as session:
            stmt = select(self.job_categories_table.c.category_id).where(self.job_categories_table.c.job_id == job_id)
            result = session.execute(stmt)
            row = result.first()
            if row:
                return row.category_id  # 只回傳 ID
            return 0

    def get_jobs(self, category_id: int | None = None) -> list[Job]:
        """取得 Job 列表，可選擇性地根據 category_id 過濾。

        Args:
            category_id (int | None): 要過濾的分類 ID。若為 None 或 0，則回傳所有 Job。

        Returns:
            list[Job]: 以任務名稱排序的 Job 物件列表。
        """
        all_jobs = super().get_all_jobs()  # 從父類獲取原始 Job 列表

        if category_id is not None and category_id != 0:
            # 需要根據 category_id 過濾
            target_job_ids = set()
            try:
                stmt = select(self.job_categories_table.c.job_id).where(
                    self.job_categories_table.c.category_id == category_id
                )
                with self.engine.connect() as connection:
                    result = connection.execute(stmt)
                    for row in result:
                        target_job_ids.add(row.job_id)

                # 過濾 Job 列表
                filtered_jobs = [job for job in all_jobs if job.id in target_job_ids]
                # 根據任務名稱排序
                return sorted(filtered_jobs, key=lambda job: job.name.lower())
            except Exception as e:
                logger.error(f"根據 category_id {category_id} 過濾 Job 時發生錯誤: {e}")
                return []  # 出錯時回傳空列表
        else:
            # 不需要過濾，回傳所有 Job，但根據名稱排序
            return sorted(all_jobs, key=lambda job: job.name.lower())

    def lookup_job(self, job_id) -> Job | None:
        """覆寫 SQLAlchemyJobStore.lookup_job 方法。
        直接回傳父類別的結果。
        """
        # 還原：直接回傳原始 Job 物件，不附加 category_id
        return super().lookup_job(job_id)

    def get_all_jobs(self) -> list[Job]:
        """覆寫 SQLAlchemyJobStore.get_all_jobs 方法。
        直接回傳父類別的結果。
        """
        # 還原：直接回傳原始 Job 列表，不附加 category_id
        return super().get_all_jobs()
