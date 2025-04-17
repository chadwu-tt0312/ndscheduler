"""Utils for scheduler package."""

import datetime
import os
import socket
import sys
import traceback
import uuid
import logging

import pytz

from ndscheduler.corescheduler import constants

logger = logging.getLogger(__name__)
# 添加一個專門記錄錯誤的 logger
error_logger = logging.getLogger("error_logger")


def import_from_path(path):
    """Import a module / class from a path string.
    :param str path: class path, e.g., ndscheduler.corescheduler.job
    :return: class object
    :rtype: class
    """

    components = path.split(".")
    module = __import__(".".join(components[:-1]))
    for comp in components[1:-1]:
        module = getattr(module, comp)
    return getattr(module, components[-1])


def get_current_datetime():
    """Retrieves the current datetime.
    :return: A datetime representing the current time.
    :rtype: datetime
    """
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def get_job_name(job):
    """Returns job name.
    :param Job job: An apscheduler.job.Job instance.
    :return: task name
    :rtype: str
    """
    return job.args[0]


def get_job_args(job):
    """Returns arguments of a job.
    :param Job job: An apscheduler.job.Job instance.
    :return: task arguments
    :rtype: list of str
    """
    return job.args[constants.JOB_ARGS :]


def get_job_kwargs(job):
    """Returns keyword arguments of a job.
    :param Job job: An apscheduler.job.Job instance.
    :return: keyword arguments
    :rtype: dict
    """
    return job.kwargs

def are_job_args_equal(args1, args2):
    """比較兩個 job args 是否相等，會考慮到 tuple 和 list 的等價性。

    :param args1: 第一個 job args
    :param args2: 第二個 job args
    :return: 如果兩個 args 在功能上相等則返回 True
    :rtype: bool
    """
    if args1 == args2:
        return True

    # 如果其中一個是 tuple 另一個是 list，將它們轉換成相同類型再比較
    if isinstance(args1, (tuple, list)) and isinstance(args2, (tuple, list)):
        return list(args1) == list(args2)

    return False

def get_cron_strings(job):
    """Returns cron strings.
    :param Job job: An apscheduler.job.Job instance.
    :return: cron strings
    :rtype: dict
    """
    return {
        "month": str(job.trigger.fields[1]),
        "day": str(job.trigger.fields[2]),
        "week": str(job.trigger.fields[3]),
        "day_of_week": str(job.trigger.fields[4]),
        "hour": str(job.trigger.fields[5]),
        "minute": str(job.trigger.fields[6]),
    }


def generate_uuid():
    """Generates 32-digit hex uuid.
    Example: d8f376e858a411e4b6ae22001ac68d05
    :return: uuid hex string
    :rtype: str
    """
    return uuid.uuid4().hex


def get_stacktrace():
    """Returns the full stack trace."""

    type_, value_, traceback_ = sys.exc_info()
    return "".join(traceback.format_exception(type_, value_, traceback_))


def get_hostname():
    """Returns the host name."""
    return socket.gethostname()


def get_pid():
    """Returns the process ID"""
    return os.getpid()


def log_error(message, exc_info=False):
    """使用錯誤日誌記錄器記錄錯誤訊息。

    Args:
        message (str): 錯誤訊息
        exc_info (bool, optional): 是否包含異常詳細信息。預設為 False。
    """
    error_logger.error(message, exc_info=exc_info)


def get_datastore_instance(datastore_class_path, db_config=None, db_tablenames=None):
    datastore_class = import_from_path(datastore_class_path)
    return datastore_class.get_instance(db_config, db_tablenames)


def get_job_class(job_class_string):
    """從字串路徑導入任務類別。

    Args:
        job_class_string (str): 任務類別的完整路徑，例如：'simple_scheduler.jobs.sample_job.AwesomeJob'

    Returns:
        class: 任務類別
        None: 如果導入失敗
    """
    try:
        return import_from_path(job_class_string)
    except (ImportError, AttributeError) as e:
        log_error(f"導入任務類別失敗 {job_class_string}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        log_error(f"導入任務類別時發生未預期的錯誤 {job_class_string}: {str(e)}", exc_info=True)
        return None
