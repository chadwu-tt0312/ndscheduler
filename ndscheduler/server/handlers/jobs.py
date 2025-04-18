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


class Handler(base.BaseHandler):

    def _get_jobs(self):
        """Returns a dictionary for all jobs info filtered by user's category_id.

        It's a blocking operation.
        """
        # 獲取當前登入使用者的 category_id
        user_info = self.get_current_user()
        user_category_id = user_info.get("category_id", 0) if user_info else 0

        # 根據 category_id 獲取 Jobs
        jobs = self.scheduler_manager.get_jobs(category_id=user_category_id)
        return_json = []
        for job in jobs:
            job_dict = self._build_job_dict(job)
            return_json.append(job_dict)
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

        # --- 在此處獲取 category_id ---
        category_id = 0  # 預設值
        try:
            retrieved_id = self.datastore.get_job_category(job.id)
            if retrieved_id is not None:
                category_id = retrieved_id
        except Exception as e:
            logger.warning(f"為 job {job.id} 查詢 category_id 時發生錯誤: {e}")
        # --- 結束獲取 category_id ---

        return_dict = {
            "job_id": job.id,
            "name": job.name,
            "next_run_time": next_run_time,
            "job_class_string": utils.get_job_name(job),
            "pub_args": utils.get_job_args(job),
            "category_id": category_id,  # 使用查詢到的 category_id
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

        # 確保 json_args 中包含當前用戶名稱
        if "user" not in self.json_args:
            self.json_args["user"] = self.username

        # 這是非阻塞函數
        # 它會立即返回 job_id
        job_id = self.scheduler_manager.add_job(**self.json_args)

        # --- 新增 Job 分類關聯邏輯 ---
        try:
            user_info = self.get_current_user()
            user_category_id = user_info.get("category_id") if user_info else None

            if user_category_id is not None and user_category_id != 0:
                # logger.info(f"為新任務 {job_id} 設定分類 ID: {user_category_id}")
                self.datastore.set_job_category(job_id, user_category_id)
        except Exception as e:
            # 記錄錯誤，但不影響 Job 的創建
            logger.error(f"為任務 {job_id} 設定分類時發生錯誤: {e}", exc_info=True)
        # --- 結束新增 Job 分類關聯邏輯 ---

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
                category_id=job_info.get("category_id", 0),  # 從 job_info 取得 category_id
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
        :param str item: The field name to compare.
        :return: String for description.
        :rtype: str
        """
        if item == "pub_args":
            if not utils.are_job_args_equal(old_job[item], new_job[item]):
                return ('<b>%s</b>: <font color="red">%s</font> =>' ' <font color="green">%s</font><br>') % (
                    item,
                    old_job[item],
                    new_job[item],
                )
            return ""

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
        """修改任務。

        如果 pub_args 未變更，則僅修改允許的屬性。
        如果 pub_args 已變更，則刪除並重新建立任務。

        :param str job_id: 任務 ID 字串。
        :return: 任務修改後的字典。
        :rtype: dict
        :raises: ValueError 如果任務不存在或修改失敗
        """
        # 先取得舊的任務資料
        old_job = self.scheduler_manager.get_job(job_id)
        if not old_job:
            self.set_status(404)
            raise ValueError(f"Job not found: {job_id}")

        old_job_info = self._build_job_dict(old_job)

        # 驗證輸入資料
        self._validate_post_data()
        new_data = self.json_args

        # --- 檢查 pub_args 是否變更 ---
        old_pub_args = old_job_info.get("pub_args")
        new_pub_args = new_data.get("pub_args")

        # 嘗試將請求中的 pub_args (可能是 JSON 字串) 解析為 Python list/dict
        parsed_new_pub_args = None
        if new_pub_args is not None:
            if isinstance(new_pub_args, (list, dict)):
                parsed_new_pub_args = new_pub_args
            elif isinstance(new_pub_args, str):
                try:
                    parsed_new_pub_args = json.loads(new_pub_args)
                except json.JSONDecodeError:
                    self.set_status(400)
                    raise ValueError("Invalid JSON format for Arguments")
            else:
                # 如果格式不對，也視為未提供或無效
                pass

        # 使用 utils.are_job_args_equal 進行比較 (處理 list/tuple 差異)
        args_changed = not utils.are_job_args_equal(old_pub_args, parsed_new_pub_args)

        # --- 根據 pub_args 是否變更，執行不同流程 ---
        if args_changed:
            # --- 重建 Job 流程 ---
            logger.info(f"Job {job_id} arguments changed. Recreating job.")
            try:
                # 1. 收集合併後的參數
                recreate_params = old_job_info.copy()  # 從舊資訊開始
                recreate_params.update(new_data)  # 用新資料覆蓋
                recreate_params["pub_args"] = parsed_new_pub_args  # 使用解析後的新參數
                recreate_params["job_id"] = job_id  # 強制使用原 ID
                if "user" not in recreate_params:
                    recreate_params["user"] = self.username

                # 移除不適用於 add_job 的鍵 (例如 next_run_time)
                params_for_add_job = {
                    k: v
                    for k, v in recreate_params.items()
                    if k
                    in [
                        "job_class_string",
                        "name",
                        "pub_args",
                        "month",
                        "day_of_week",
                        "day",
                        "hour",
                        "minute",
                        "user",
                        "category_id",
                        "job_id",
                    ]
                }

                # 2. 刪除舊 Job
                self.scheduler_manager.remove_job(job_id)

                # 3. 新增 Job (使用相同 ID)
                # add_job 會處理 pub_args 格式
                new_job_id = self.scheduler_manager.add_job(**params_for_add_job)
                if new_job_id != job_id:
                    logger.warning(f"Recreated job {job_id} but received a different ID: {new_job_id}")

                # 4. 獲取重建後的 Job 資訊
                new_job = self.scheduler_manager.get_job(job_id)
                if not new_job:
                    raise ValueError("Failed to retrieve job after recreation.")
                new_job_info = self._build_job_dict(new_job)

            except Exception as e:
                logger.error(f"Failed to recreate job {job_id}: {e}", exc_info=True)
                # 嘗試恢復舊 Job？(可能很複雜，暫時報錯)
                self.set_status(500)
                raise ValueError(f"Failed to modify job arguments: {e}")
        else:
            # --- 標準修改流程 (只改 name, schedule 等) ---
            logger.info(f"Job {job_id} arguments unchanged. Modifying other attributes.")
            try:
                # 確保 user 在 kwargs 中傳遞給 modify_scheduler_job
                if "user" not in new_data:
                    new_data["user"] = self.username

                self.scheduler_manager.modify_job(job_id, **new_data)
                # 獲取修改後的任務資料
                new_job = self.scheduler_manager.get_job(job_id)
                new_job_info = self._build_job_dict(new_job)
            except Exception as e:
                logger.error(f"Failed to modify job {job_id} attributes: {e}", exc_info=True)
                self.set_status(500)
                raise ValueError(f"Failed to modify job attributes: {e}")

        # --- 記錄稽核日誌 --- (無論哪種流程，都比較 old 和 new)
        description = self._generate_description_for_modify(old_job_info, new_job_info)
        self.datastore.add_audit_log(
            job_id,
            new_job_info["name"],
            constants.AUDIT_LOG_MODIFIED,
            user=self.username,
            category_id=new_job_info.get("category_id", 0),
            description=description,
        )

        return new_job_info

    @tornado.concurrent.run_on_executor
    def modify_job(self, job_id):
        """包裝 _modify_job() 以在執行緒執行器上運行。"""
        return self._modify_job(job_id)

    @tornado.gen.coroutine
    def modify_job_yield(self, job_id):
        """非同步模式下修改任務的包裝器。

        :param str job_id: 任務 ID
        :return: 包含已修改任務資訊的字典
        :rtype: dict
        """
        return_json = yield self.modify_job(job_id)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def put(self, job_id):
        """修改一個任務。

        處理端點：
            PUT /api/v1/jobs/{job_id}

        :param str job_id: 任務 ID
        """
        yield self.modify_job_yield(job_id)

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
            self.datastore.add_audit_log(
                job_id,
                job["name"],
                constants.AUDIT_LOG_PAUSED,
                user=self.username,
                category_id=job.get("category_id", 0),  # 使用 .get 提供預設值
            )

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
            self.datastore.add_audit_log(
                job_id,
                job["name"],
                constants.AUDIT_LOG_RESUMED,
                user=self.username,
                category_id=job.get("category_id", 0),  # 使用 .get 提供預設值
            )

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
