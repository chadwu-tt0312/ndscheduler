"""Represents SQLite datastore."""

import datetime

import pytz
from sqlalchemy.engine import URL

from ndscheduler.corescheduler.datastore import base


class DatastoreSqlite(base.DatastoreBase):

    def get_db_url(self) -> str:
        """Returns the db url to establish a SQLite connection, where db_config is passed in
        on initialization as:
        {
            'file_path': 'an_absolute_file_path'
        }
        If 'file_path' is not passed in, an in-memory SQLite db is created.

        Returns:
            str: SQLAlchemy 2.0 compatible database URL
        """
        file_path = ""
        if self.db_config and "file_path" in self.db_config:
            file_path = self.db_config["file_path"]

        return URL.create(
            drivername="sqlite", database=file_path or None  # None for in-memory database
        ).render_as_string(hide_password=False)

    def get_time_isoformat_from_db(self, time_object) -> str:
        """將資料庫時間轉換為帶 UTC 時區的 ISO 格式。

        Args:
            time_object: 可以是 datetime 物件或格式為 '%Y-%m-%d %H:%M:%S.%f' 的時間字串

        Returns:
            str: 帶 UTC 時區的 ISO 格式時間字串
        """
        if isinstance(time_object, str):
            date = datetime.datetime.strptime(time_object, "%Y-%m-%d %H:%M:%S.%f")
        else:
            date = time_object

        if date.tzinfo is None:
            date = pytz.utc.localize(date)
        return date.isoformat()
