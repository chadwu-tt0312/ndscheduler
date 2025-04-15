"""Define database schemas."""

from sqlalchemy import Table, Column, Integer, Text, DateTime, Unicode, Boolean, ForeignKey

from ndscheduler.corescheduler import utils


#
# Jobs
# It's defined by apscheduler library.
#


def get_job_categories_table(metadata, tablename="scheduler_job_categories"):
    """取得任務分類關聯表格的結構。

    :param metadata: SQLAlchemy MetaData instance
    :param tablename: 表格名稱
    :return: SQLAlchemy Table instance
    """
    return Table(
        tablename,
        metadata,
        Column("job_id", Unicode(191), nullable=False),
        Column("category_id", Integer, ForeignKey("scheduler_categories.id"), nullable=False),
        Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
            default=utils.get_current_datetime,
        ),
    )


def get_execution_table(metadata, tablename):
    """Get the execution table schema.

    :param metadata: SQLAlchemy MetaData instance
    :param tablename: Name of the table
    :return: SQLAlchemy Table instance
    """
    return Table(
        tablename,
        metadata,
        Column("eid", Unicode(191), primary_key=True),
        Column("hostname", Text, nullable=True),
        Column("pid", Integer, nullable=True),
        Column("state", Integer, nullable=False),
        Column("category_id", Integer, ForeignKey("scheduler_categories.id"), nullable=True),
        Column(
            "scheduled_time",
            DateTime(timezone=True),
            nullable=False,
            default=utils.get_current_datetime,
        ),
        Column(
            "updated_time",
            DateTime(timezone=True),
            default=utils.get_current_datetime,
            onupdate=utils.get_current_datetime,
        ),
        Column("description", Text, nullable=True),
        Column("result", Text, nullable=True),
        Column("job_id", Text, nullable=False),
        Column("task_id", Text, nullable=True),
    )


def get_auditlogs_table(metadata, tablename):
    """Get the audit logs table schema.

    :param metadata: SQLAlchemy MetaData instance
    :param tablename: Name of the table
    :return: SQLAlchemy Table instance
    """
    return Table(
        tablename,
        metadata,
        Column("job_id", Text, nullable=False),
        Column("job_name", Text, nullable=False),
        Column("event", Integer, nullable=False),
        Column("user", Text, nullable=True),
        Column("category_id", Integer, ForeignKey("scheduler_categories.id"), nullable=True),
        Column(
            "created_time",
            DateTime(timezone=True),
            nullable=False,
            default=utils.get_current_datetime,
        ),
        Column("description", Text, nullable=True),
    )


def get_users_table(metadata, tablename="users"):
    """Get the users table schema.

    :param metadata: SQLAlchemy MetaData instance
    :param tablename: Name of the table
    :return: SQLAlchemy Table instance
    """
    return Table(
        tablename,
        metadata,
        Column("id", Integer, primary_key=True),
        Column("username", Unicode(50), unique=True, nullable=False),
        Column("password", Unicode(255), nullable=False),
        Column("is_admin", Boolean, default=False),
        Column("category_id", Integer, ForeignKey("scheduler_categories.id"), nullable=True),
        Column("permission", Boolean, default=False),
        Column("created_at", DateTime(timezone=True), nullable=False, default=utils.get_current_datetime),
        Column(
            "updated_at",
            DateTime(timezone=True),
            default=utils.get_current_datetime,
            onupdate=utils.get_current_datetime,
        ),
    )


def get_categories_table(metadata, tablename="categories"):
    """Get the categories table schema.

    :param metadata: SQLAlchemy MetaData instance
    :param tablename: Name of the table
    :return: SQLAlchemy Table instance
    """
    return Table(
        tablename,
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", Unicode(50), unique=True, nullable=False),
        Column("description", Text, nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False, default=utils.get_current_datetime),
        Column(
            "updated_at",
            DateTime(timezone=True),
            default=utils.get_current_datetime,
            onupdate=utils.get_current_datetime,
        ),
    )
