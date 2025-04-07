"""Define database schemas."""

from sqlalchemy import Table, Column, Integer, Text, DateTime, Unicode

from ndscheduler.corescheduler import utils


#
# Jobs
# It's defined by apscheduler library.
#


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
        Column(
            "created_time",
            DateTime(timezone=True),
            nullable=False,
            default=utils.get_current_datetime,
        ),
        Column("description", Text, nullable=True),
    )
