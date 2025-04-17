"""Handler for jobs endpoint."""

import json
import logging
from datetime import datetime

import tornado.concurrent
import tornado.gen
import tornado.web

from ndscheduler.corescheduler import constants
from ndscheduler.corescheduler import utils
from ndscheduler.server.handlers import base

logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error_logger")


class Handler(base.BaseHandler):

    def _get_jobs(self):
        """Returns a dictionary for all jobs info.

        It's a blocking operation.
        """
        # logger.info("開始獲取任務...")
        jobs = self.scheduler_manager.get_jobs()
        # logger.info(f"從 scheduler_manager 獲取到的任務數量： {len(jobs)}")
        return_json = []
        for job in jobs:
            job_dict = self._build_job_dict(job)
            return_json.append(job_dict)
            # logger.info(f"任務詳情：{job_dict}")
        # logger.info(f"最終返回的任務數據：{return_json}")
        return {"jobs": return_json}

    def _build_job_dict(self, job):
        """Transforms apscheduler's job structure to a python dictionary.

        :param Job job: An apscheduler.job.Job instance.
        :return: dictionary for job info
        :rtype: dict
        """
        if job.next_run_time:
            next_run_time = job.next_run_time.isoformat()
        else:
            next_run_time = ""
        return_dict = {
            "job_id": job.id,
            "name": job.name,
            "next_run_time": next_run_time,
            "job_class_string": utils.get_job_name(job),
            "pub_args": utils.get_job_args(job),
        }

        return_dict.update(utils.get_cron_strings(job))
        return return_dict

    @tornado.concurrent.run_on_executor
    def get_jobs(self):
        """Wrapper to run _get_jobs() on a thread executor.

        :return: dictionary for jobs
            A dictionary of jobs, e.g., :
            {
                jobs: [...]
            }
        :rtype: dict
        """
        return self._get_jobs()

    @tornado.gen.coroutine
    def get_jobs_yield(self):
        """非同步模式下獲取所有任務的包裝器。

        :return: 包含所有任務資訊的字典
        :rtype: dict
        """
        return_json = yield self.get_jobs()
        self.finish(return_json)

    def _get_job(self, job_id):
        """Returns a dictionary for a job info.

        It's a blocking operation.

        :param str job_id: Job id.

        :return: dictionary for a job
        :rtype: dict
        """
        job = self.scheduler_manager.get_job(job_id)
        if not job:
            self.set_status(400)
            utils.log_error(f"找不到任務：{job_id}")
            raise ValueError(f"Job not found: {job_id}")
        return self._build_job_dict(job)

    @tornado.concurrent.run_on_executor
    def get_job(self, job_id):
        """Wrapper to run _get_jobs() on a thread executor.

        :param str job_id: Job id.
        :return: A dictionary of a job.
        :rtype: dict
        """
        return self._get_job(job_id)

    @tornado.gen.coroutine
    def get_job_yield(self, job_id):
        """非同步模式下獲取單個任務的包裝器。

        :param str job_id: 任務 ID
        :return: 包含任務資訊的字典
        :rtype: dict
        """
        return_json = yield self.get_job(job_id)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def get(self, job_id=None):
        """返回一個或多個任務。

        處理兩個端點：
            GET /api/v1/jobs           (當 job_id == None)
            GET /api/v1/jobs/{job_id}  (當 job_id != None)

        :param str job_id: 任務 ID
        """
        if job_id is None:
            yield self.get_jobs_yield()
        else:
            yield self.get_job_yield(job_id)

    @tornado.web.removeslash
    def post(self):
        """新增一個任務。

        add_job() 是非阻塞操作。

        處理端點：
            POST /api/v1/jobs
        """
        self._validate_post_data()

        # 這是非阻塞函數
        # 它會立即返回 job_id
        job_id = self.scheduler_manager.add_job(**self.json_args)

        response = {"job_id": job_id}
        self.set_status(201)
        self.write(response)

    def _delete_job(self, job_id):
        """刪除一個任務。

        這是一個阻塞操作。

        :param str job_id: 任務 ID 字串。
        :raises: JobNotFoundError 如果任務不存在
        """
        try:
            # 先檢查任務是否存在
            job = self.scheduler_manager.get_job(job_id)
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            job_info = self._build_job_dict(job)

            # 嘗試刪除任務
            self.scheduler_manager.remove_job(job_id)

            # 只有在成功刪除後才記錄稽核日誌
            self.datastore.add_audit_log(
                job_id,
                job_info["name"],
                constants.AUDIT_LOG_DELETED,
                user=self.username,
                description=json.dumps(job_info),
            )
        except Exception as e:
            self.set_status(400)
            raise ValueError(f"Failed to delete job {job_id}: {str(e)}")

    @tornado.concurrent.run_on_executor
    def delete_job(self, job_id):
        """Wrapper for _delete_job() to run on a threaded executor."""
        self._delete_job(job_id)

    @tornado.gen.coroutine
    def delete_job_yield(self, job_id):
        """非同步模式下刪除任務的包裝器。

        :param str job_id: 任務 ID
        """
        yield self.delete_job(job_id)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def delete(self, job_id):
        """刪除一個任務。

        處理端點：
            DELETE /api/v1/jobs/{job_id}

        :param str job_id: 任務 ID
        """
        yield self.delete_job_yield(job_id)
        response = {"job_id": job_id}
        self.set_status(200)
        self.finish(response)

    def _generate_description_for_item(self, old_job, new_job, item):
        """Returns a diff for one field of a job.


        :param dict old_job: Dict for old job.
        :param dict new_job: Dict for new job after modification.

        :return: String for description.
        :rtype: str
        """
        if old_job[item] != new_job[item]:
            return ('<b>%s</b>: <font color="red">%s</font> =>' ' <font color="green">%s</font><br>') % (
                item,
                old_job[item],
                new_job[item],
            )
        return ""

    def _generate_description_for_modify(self, old_job, new_job):
        """生成任務修改的描述。

        Args:
            old_job (dict): 修改前的任務資訊
            new_job (dict): 修改後的任務資訊

        Returns:
            str: JSON 格式的修改描述
        """
        try:
            changes = {}

            # 比較所有欄位
            all_keys = set(old_job.keys()) | set(new_job.keys())
            for key in all_keys:
                old_value = old_job.get(key)
                new_value = new_job.get(key)
                if old_value != new_value:
                    changes[key] = {"old": old_value, "new": new_value}

            description = {"changes": changes, "timestamp": datetime.utcnow().isoformat()}

            return json.dumps(description, ensure_ascii=False)

        except Exception as e:
            utils.log_error(f"生成修改描述時發生錯誤：{str(e)}", exc_info=True)
            return json.dumps({"error": "無法生成修改描述", "timestamp": datetime.utcnow().isoformat()})

    def _modify_job(self, job_id):
        """修改一個任務。

        這是一個阻塞操作。

        Args:
            job_id (str): 任務 ID

        Returns:
            dict: 修改後的任務資訊
        """
        try:
            # 取得原始任務資訊
            old_job = self.scheduler_manager.get_job(job_id)
            if not old_job:
                utils.log_error(f"找不到任務：{job_id}")
                self.set_status(404)
                return {"error": f"找不到任務：{job_id}"}

            old_job_dict = self._build_job_dict(old_job)
            logger.info(f"準備修改任務，原始資訊：{old_job_dict}")

            # 驗證修改參數
            try:
                # 檢查是否需要修改不可修改的屬性
                immutable_attrs = {"job_class_string", "pub_args"}
                has_immutable_changes = False

                # 只有當不可修改屬性的值真的改變時，才需要重新創建任務
                for attr in immutable_attrs:
                    if attr in self.json_args:
                        if str(self.json_args[attr]) != str(old_job_dict.get(attr)):
                            has_immutable_changes = True
                            break

                if has_immutable_changes:
                    # 如果需要修改不可修改的屬性，我們需要重新創建任務
                    logger.info("檢測到不可修改的屬性發生變更，將重新創建任務")

                    # 獲取當前任務的所有設置
                    current_settings = {
                        "name": old_job_dict["name"],
                        "job_class_string": old_job_dict["job_class_string"],
                        "pub_args": old_job_dict["pub_args"],
                        "month": old_job_dict.get("month", "*"),
                        "day": old_job_dict.get("day", "*"),
                        "day_of_week": old_job_dict.get("day_of_week", "*"),
                        "hour": old_job_dict.get("hour", "*"),
                        "minute": old_job_dict.get("minute", "*"),
                    }

                    # 更新設置
                    for key, value in self.json_args.items():
                        if key in current_settings:
                            current_settings[key] = value

                    # 驗證任務類別
                    if "job_class_string" in self.json_args:
                        job_class = utils.get_job_class(current_settings["job_class_string"])
                        if not job_class:
                            self.set_status(400)
                            return {"error": f"無效的任務類別：{current_settings['job_class_string']}"}

                    # 處理任務參數
                    if "pub_args" in self.json_args:
                        try:
                            args = current_settings["pub_args"]
                            if isinstance(args, str):
                                args = json.loads(args)
                            if not isinstance(args, (list, dict)):
                                args = [args]
                            current_settings["pub_args"] = json.dumps(args)
                        except json.JSONDecodeError:
                            self.set_status(400)
                            return {"error": "無效的任務參數格式"}

                    try:
                        # 先創建新任務，如果成功再刪除舊任務
                        temp_job_id = f"temp_{job_id}"
                        self.scheduler_manager.add_job(job_id=temp_job_id, **current_settings)

                        # 如果新任務創建成功，刪除舊任務
                        self.scheduler_manager.remove_job(job_id)

                        # 再次創建新任務，使用原始 job_id
                        self.scheduler_manager.add_job(job_id=job_id, **current_settings)

                        # 刪除臨時任務
                        self.scheduler_manager.remove_job(temp_job_id)

                        logger.info(f"成功重新創建任務：{current_settings}")
                    except Exception as e:
                        # 如果創建新任務失敗，確保刪除臨時任務（如果存在）
                        try:
                            self.scheduler_manager.remove_job(temp_job_id)
                        except Exception:
                            pass

                        # 如果舊任務還存在，保持不變
                        if self.scheduler_manager.get_job(job_id):
                            utils.log_error(f"創建新任務失敗，保持原任務不變：{str(e)}")
                            self.set_status(400)
                            return {"error": f"修改任務失敗：{str(e)}"}
                        else:
                            # 如果舊任務已被刪除，嘗試恢復
                            try:
                                self.scheduler_manager.add_job(job_id=job_id, **old_job_dict)
                                utils.log_error(f"創建新任務失敗，已恢復原任務：{str(e)}")
                                self.set_status(400)
                                return {"error": f"修改任務失敗，已恢復原任務：{str(e)}"}
                            except Exception as restore_error:
                                utils.log_error(f"恢復原任務失敗：{str(restore_error)}")
                                self.set_status(500)
                                return {"error": "修改任務失敗且無法恢復原任務"}

                else:
                    # 如果只修改可修改的屬性，使用 modify_job
                    logger.info("只修改可修改的屬性")
                    modifiable_args = {}

                    # 只包含可修改的屬性
                    for key, value in self.json_args.items():
                        if key not in immutable_attrs:
                            modifiable_args[key] = value

                    if modifiable_args:
                        self.scheduler_manager.modify_job(job_id, **modifiable_args)
                        logger.info(f"成功修改任務屬性：{modifiable_args}")
                    else:
                        logger.info("沒有需要修改的屬性")

                # 取得更新後的任務資訊
                new_job = self.scheduler_manager.get_job(job_id)
                if not new_job:
                    utils.log_error(f"任務修改後無法取得：{job_id}")
                    self.set_status(500)
                    return {"error": "任務修改失敗"}

                new_job_dict = self._build_job_dict(new_job)
                logger.info(f"任務修改成功，新資訊：{new_job_dict}")

                # 生成修改描述
                description = self._generate_description_for_modify(old_job_dict, new_job_dict)

                # 記錄稽核日誌
                self.datastore.add_audit_log(
                    job_id,
                    new_job_dict["name"],
                    constants.AUDIT_LOG_MODIFIED,
                    user=self.username,
                    description=description,
                )

                return new_job_dict

            except Exception as e:
                utils.log_error(f"修改任務時發生錯誤：{str(e)}", exc_info=True)
                self.set_status(400)
                return {"error": f"Failed to modify job {job_id}: {str(e)}"}

        except Exception as e:
            utils.log_error(f"修改任務時發生未預期的錯誤：{str(e)}", exc_info=True)
            self.set_status(500)
            return {"error": f"修改任務失敗：{str(e)}"}

    @tornado.concurrent.run_on_executor
    def modify_job(self, job_id):
        """在執行緒執行器上執行 _modify_job 的包裝器。

        Args:
            job_id (str): 任務 ID

        Returns:
            dict: 修改後的任務資訊
        """
        return self._modify_job(job_id)

    @tornado.gen.coroutine
    def modify_job_yield(self, job_id):
        """非同步模式下修改任務的包裝器。

        :param str job_id: 任務 ID
        """
        yield self.modify_job(job_id)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def put(self, job_id):
        """修改一個任務。

        處理端點：
            PUT /api/v1/jobs/{job_id}

        :param str job_id: 任務 ID
        """
        yield self.modify_job_yield(job_id)
        response = {"job_id": job_id}
        self.set_status(200)
        self.finish(response)

    @tornado.web.removeslash
    def patch(self, job_id):
        """暫停一個任務。

        pause_job() 是非阻塞操作，但稽核日誌是阻塞操作。

        處理端點：
            PATCH /api/v1/jobs/{job_id}

        :param str job_id: 任務 ID
        """
        try:
            # 檢查任務是否存在
            job = self._get_job(job_id)
            if isinstance(job, dict) and "error" in job:
                self.set_status(400)
                self.write(job)
                return

            # 嘗試暫停任務
            self.scheduler_manager.pause_job(job_id)

            # 記錄稽核日誌
            self.datastore.add_audit_log(job_id, job["name"], constants.AUDIT_LOG_PAUSED, user=self.username)

            response = {"job_id": job_id}
            self.set_status(200)
            self.write(response)

        except Exception as e:
            self.set_status(500)
            self.write({"error": f"暫停任務失敗：{str(e)}"})

    @tornado.web.removeslash
    def options(self, job_id):
        """恢復一個任務。

        resume_job() 是非阻塞操作，但稽核日誌是阻塞操作。

        處理端點：
            OPTIONS /api/v1/jobs/{job_id}

        :param str job_id: 任務 ID
        """
        try:
            # 檢查任務是否存在
            job = self._get_job(job_id)
            if isinstance(job, dict) and "error" in job:
                self.set_status(400)
                self.write(job)
                return

            # 嘗試恢復任務
            self.scheduler_manager.resume_job(job_id)

            # 記錄稽核日誌
            self.datastore.add_audit_log(job_id, job["name"], constants.AUDIT_LOG_RESUMED, user=self.username)

            response = {"job_id": job_id}
            self.set_status(200)
            self.write(response)

        except Exception as e:
            self.set_status(500)
            self.write({"error": f"恢復任務失敗：{str(e)}"})

    def _validate_post_data(self):
        """Validates POST data for adding a job.


        :return: a dictionary that serves as kwargs for Scheduler.add_job()
        :rtype: dict

        :raises: HTTPError(400: Bad arguments).
        """
        all_required_fields = ["name", "job_class_string"]
        for field in all_required_fields:
            if field not in self.json_args:
                raise tornado.web.HTTPError(400, reason="Require this parameter: %s" % field)

        at_least_one_required_fields = ["month", "day", "hour", "minute", "day_of_week"]
        valid_cron_string = False
        for field in at_least_one_required_fields:
            if field in self.json_args:
                valid_cron_string = True
                break

        if not valid_cron_string:
            raise tornado.web.HTTPError(
                400,
                reason=("Require at least one of following parameters:" " %s" % str(at_least_one_required_fields)),
            )
