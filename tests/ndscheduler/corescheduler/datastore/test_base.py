"""Unit tests for DatastoreBase."""

import datetime
import unittest

from apscheduler.schedulers.blocking import BlockingScheduler

from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler.datastore.providers.sqlite import DatastoreSqlite


class DatastoreBaseTest(unittest.TestCase):

    def setUp(self):
        fake_scheduler = BlockingScheduler()
        self.store = DatastoreSqlite.get_instance()
        self.store.start(fake_scheduler, None)

    def tearDown(self):
        """清理測試資料"""
        self.store.destroy_instance()

    def test_add_execution_get_execution(self):
        """測試新增和獲取執行記錄"""
        eid = "12345"
        job_id = "321"
        self.store.add_execution(eid, job_id, state=constants.EXECUTION_STATUS_SCHEDULED)
        execution = self.store.get_execution(eid)
        self.assertEqual(execution["execution_id"], eid)
        self.assertEqual(
            execution["state"],
            constants.EXECUTION_STATUS_DICT[constants.EXECUTION_STATUS_SCHEDULED],
        )

    def test_get_non_existent_execution(self):
        """測試獲取不存在的執行記錄"""
        execution = self.store.get_execution("non_existent_id")
        self.assertIsNone(execution)

    def test_update_execution_get_execution(self):
        """測試更新執行記錄"""
        eid = "12346"
        job_id = "321"
        self.store.add_execution(eid, job_id, state=constants.EXECUTION_STATUS_SCHEDULED)
        self.store.update_execution(eid, state=constants.EXECUTION_STATUS_RUNNING)
        execution = self.store.get_execution(eid)
        self.assertEqual(execution["execution_id"], eid)
        self.assertEqual(
            execution["state"], constants.EXECUTION_STATUS_DICT[constants.EXECUTION_STATUS_RUNNING]
        )

    def test_update_execution_with_description(self):
        """測試更新執行記錄的描述"""
        eid = "12347"
        job_id = "321"
        description = "Test Description"
        self.store.add_execution(eid, job_id, state=constants.EXECUTION_STATUS_SCHEDULED)
        self.store.update_execution(eid, description=description)
        execution = self.store.get_execution(eid)
        self.assertEqual(execution["description"], description)

    def test_get_executions_by_time_interval(self):
        """測試根據時間區間獲取執行記錄"""
        now = datetime.datetime.now()
        start_time = (now + datetime.timedelta(minutes=20)).isoformat()
        end_time = (now + datetime.timedelta(minutes=100)).isoformat()

        # 新增測試資料
        self.store.add_execution(
            "12",
            "34",
            state=constants.EXECUTION_STATUS_SCHEDULED,
            scheduled_time=now + datetime.timedelta(minutes=5),
        )
        self.store.add_execution(
            "13",
            "34",
            state=constants.EXECUTION_STATUS_SCHEDULED,
            scheduled_time=now + datetime.timedelta(minutes=50),
        )
        self.store.add_execution(
            "14",
            "34",
            state=constants.EXECUTION_STATUS_SCHEDULED,
            scheduled_time=now + datetime.timedelta(minutes=70),
        )
        self.store.add_execution(
            "15",
            "34",
            state=constants.EXECUTION_STATUS_SCHEDULED,
            scheduled_time=now + datetime.timedelta(minutes=120),
        )

        # 測試時間區間查詢
        executions = self.store.get_executions(start_time, end_time)
        self.assertEqual(len(executions["executions"]), 2)

        # 測試結果排序
        self.assertGreater(
            executions["executions"][0]["scheduled_time"],
            executions["executions"][1]["scheduled_time"],
        )

    def test_add_audit_log_get_audit_logs(self):
        """測試新增和獲取審計日誌"""
        job_id = "234"
        job_name = "test_job"
        event = constants.AUDIT_LOG_ADDED
        user = "test_user"
        description = "Test audit log"

        self.store.add_audit_log(job_id, job_name, event, user=user, description=description)

        now = datetime.datetime.utcnow()
        five_min_ago = now - datetime.timedelta(minutes=5)

        logs = self.store.get_audit_logs(five_min_ago.isoformat(), now.isoformat())
        self.assertEqual(len(logs["logs"]), 1)

        log = logs["logs"][0]
        self.assertEqual(log["job_id"], job_id)
        self.assertEqual(log["job_name"], job_name)
        self.assertEqual(log["event"], constants.AUDIT_LOG_DICT[event])
        self.assertEqual(log["user"], user)
        self.assertEqual(log["description"], description)

    def test_get_audit_logs_empty_result(self):
        """測試獲取空的審計日誌"""
        now = datetime.datetime.utcnow()
        future_time = now + datetime.timedelta(hours=1)

        logs = self.store.get_audit_logs(now.isoformat(), future_time.isoformat())
        self.assertEqual(len(logs["logs"]), 0)
