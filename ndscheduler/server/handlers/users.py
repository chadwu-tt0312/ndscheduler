"""Handler for users endpoint."""

import json
import logging
import tornado.concurrent
import tornado.gen
import tornado.web
import bcrypt

from sqlalchemy import MetaData, text

from ndscheduler.server.handlers import base
from ndscheduler.corescheduler.datastore import tables

logger = logging.getLogger(__name__)


class Handler(base.BaseHandler):
    """Handler for users endpoint."""

    def _format_datetime(self, dt_value):
        """格式化日期時間值，適應不同類型

        Args:
            dt_value: 日期時間值，可能是字串或日期時間物件

        Returns:
            str or None: 格式化後的日期時間字串或 None
        """
        if isinstance(dt_value, str):
            return dt_value
        return dt_value.isoformat() if dt_value else None

    def _get_users_table(self):
        """獲取 users 資料表和 session

        Returns:
            tuple: (session, users_table, engine) 元組
        """
        session = self.get_session()
        metadata = MetaData()
        users_table = tables.get_users_table(
            metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
        )

        # 檢查表是否存在
        engine = session.get_bind()
        if not engine.dialect.has_table(engine.connect(), users_table.name):
            self.set_status(400)
            return session, users_table, engine, True

        return session, users_table, engine, False

    def _format_user(self, user_dict):
        """格式化用戶字典數據

        Args:
            user_dict (dict): 用戶數據字典

        Returns:
            dict: 格式化後的用戶數據
        """
        return {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "category_id": user_dict["category_id"],
            "is_admin": user_dict["is_admin"],
            "is_permission": user_dict["is_permission"],
            "created_at": self._format_datetime(user_dict["created_at"]),
            "updated_at": self._format_datetime(user_dict["updated_at"]),
        }

    def _get_user(self, user_id):
        """返回用戶信息字典。

        這是一個阻塞操作。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 如果成功，返回用戶信息字典；否則返回錯誤信息字典
        """
        session, users_table, engine, error = self._get_users_table()
        if error:
            return {"error": "Users table does not exist"}

        # 查詢特定用戶
        result = session.execute(text(f"SELECT * FROM {users_table.name} WHERE id = :user_id"), {"user_id": user_id})
        user = result.fetchone()

        if not user:
            self.set_status(400)
            return {"error": f"User not found: {user_id}"}

        # 將結果轉換為字典
        columns = result.keys()
        user_dict = dict(zip(columns, user))

        return self._format_user(user_dict)

    @tornado.concurrent.run_on_executor
    def get_user(self, user_id):
        """_get_user() 的包裝器，在線程執行器上運行。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 用戶信息
        """
        return self._get_user(user_id)

    @tornado.gen.coroutine
    def get_user_yield(self, user_id):
        """get_user 的包裝器，在異步模式下運行。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 用戶信息
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        current_username = self.current_user.get("username", "")

        return_json = yield self.get_user(user_id)

        # 如果有錯誤或用戶不是管理員且不是查詢自己的信息，則返回錯誤
        if "error" in return_json:
            self.finish(return_json)
            return

        if not is_admin and return_json["username"] != current_username:
            self.set_status(403)
            self.finish({"error": "Permission denied"})
            return

        self.finish(return_json)

    def _get_users(self):
        """返回所有用戶的信息字典。

        這是一個阻塞操作。

        Returns:
            dict: 所有用戶信息，按用戶名排序
        """
        session, users_table, engine, error = self._get_users_table()
        if error:
            return {"error": "Users table does not exist"}

        try:
            # 使用 datastore 的 get_users 方法，該方法會按用戶名排序
            users = self.datastore.get_users()
            # logger.info(f"Found {len(users)} users")
            return {"users": users}
        except Exception as e:
            logger.error(f"獲取用戶列表時發生錯誤: {e}", exc_info=True)
            return {"error": f"Failed to get users: {str(e)}"}

    @tornado.concurrent.run_on_executor
    def get_users(self):
        """_get_users() 的包裝器，在線程執行器上運行。

        Returns:
            dict: 所有用戶信息
        """
        return self._get_users()

    @tornado.gen.coroutine
    def get_users_yield(self):
        """get_users 的包裝器，在異步模式下運行。

        Returns:
            dict: 所有用戶信息
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        if not is_admin:
            self.set_status(403)
            self.finish({"error": "Permission denied"})
            return

        return_json = yield self.get_users()
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def get(self, user_id=None):
        """返回一個用戶或多個用戶信息。

        處理兩個端點：
            GET /api/v1/users                  (當 user_id == None)
            GET /api/v1/users/{user_id}        (當 user_id != None)

        Args:
            user_id (str, optional): 用戶 ID
        """
        if user_id is None:
            yield self.get_users_yield()
        else:
            yield self.get_user_yield(user_id)

    def _add_user(self):
        """新增用戶。

        Returns:
            dict: 成功時返回新增用戶信息，失敗時返回錯誤信息
        """
        try:
            data = json.loads(self.request.body.decode())
            username = data.get("username")
            password = data.get("password")
            is_admin = data.get("is_admin", False)
            # category_id 可能是 None 或 int
            category_id_str = data.get("category_id")
            category_id = None
            if category_id_str is not None and category_id_str != "":
                try:
                    category_id = int(category_id_str)
                except ValueError:
                    self.set_status(400)
                    return {"error": "Category ID must be an integer or empty"}

            is_permission = data.get("is_permission", False)

            if not username or not password:
                self.set_status(400)
                return {"error": "Username and password are required"}

            # 檢查用戶名是否已存在 (此檢查應由 datastore.add_user 處理或在之前進行)
            # 我們假設 datastore.add_user 會處理重複用戶名的情況 (如果需要的話)
            # 或者可以在 datastore.add_user 內部添加此檢查
            existing_user = self.datastore.get_user(username)
            if existing_user:
                self.set_status(400)
                return {"error": "Username already exists"}

            # 呼叫 datastore 新增用戶，捕捉 category_id 錯誤
            self.datastore.add_user(username, password, category_id, is_admin, is_permission)

            # 新增成功後，獲取用戶信息並返回
            new_user_info = self.datastore.get_user(username)
            if new_user_info:
                self.set_status(201)  # Created
                # 移除密碼資訊再回傳
                new_user_info.pop("password", None)  # 假設 get_user 不回傳密碼
                return self._format_user(new_user_info)
            else:
                # 雖然 add_user 成功，但 get_user 失敗？理論上不應發生
                self.set_status(500)
                return {"error": "User created but failed to retrieve information"}

        except ValueError as e:
            # 捕獲來自 datastore.add_user 的 category_id 驗證錯誤
            self.set_status(400)
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            logger.error("無效的 JSON 格式")
            self.set_status(400)
            return {"error": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            logger.exception("新增用戶失敗")
            self.set_status(500)
            return {"error": f"Failed to add user: {str(e)}"}

    @tornado.concurrent.run_on_executor
    def add_user(self):
        """_add_user() 的包裝器，在線程執行器上運行。

        Returns:
            dict: 包含用戶 ID 的字典
        """
        return self._add_user()

    @tornado.gen.coroutine
    def add_user_yield(self):
        """add_user 的包裝器，在異步模式下運行。

        Returns:
            dict: 包含用戶 ID 的字典或錯誤訊息
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        if not is_admin:
            self.set_status(403)
            self.finish({"error": "Permission denied"})
            return

        return_json = yield self.add_user()

        # 檢查 _add_user 的回傳結果
        if isinstance(return_json, dict) and "error" in return_json:
            # 如果有錯誤，_add_user 已經設定了狀態碼 (通常是 400 或 500)
            # 直接結束請求，回傳錯誤訊息
            self.finish(return_json)
        else:
            # 如果沒有錯誤，設定成功狀態碼 201 並結束請求
            self.set_status(201)
            self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def post(self):
        """新增用戶。

        處理端點：
            POST /api/v1/users
        """
        yield self.add_user_yield()

    def _modify_user(self, user_id):
        """修改用戶信息。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 包含用戶 ID 的字典
        """
        try:
            data = json.loads(self.request.body.decode())
            username = data.get("username")
            password = data.get("password")
            category_id = data.get("category_id")
            is_admin = data.get("is_admin")
            is_permission = data.get("is_permission")

            if not any([username, password, category_id, is_admin is not None, is_permission is not None]):
                self.set_status(400)
                return {"error": "At least one field must be provided"}

            session, users_table, engine, error = self._get_users_table()
            if error:
                return {"error": "Users table does not exist"}

            # 檢查用戶是否存在
            result = session.execute(
                text(f"SELECT COUNT(*) FROM {users_table.name} WHERE id = :user_id"), {"user_id": user_id}
            )
            if result.scalar() == 0:
                self.set_status(400)
                return {"error": f"User not found: {user_id}"}

            # 檢查用戶名是否與其他用戶衝突
            if username:
                result = session.execute(
                    text(f"SELECT COUNT(*) FROM {users_table.name} WHERE username = :username AND id != :user_id"),
                    {"username": username, "user_id": user_id},
                )
                if result.scalar() > 0:
                    self.set_status(400)
                    return {"error": "Username already exists"}

            # 構建更新值
            update_fields = []
            params = {"user_id": user_id}

            if username:
                update_fields.append("username = :username")
                params["username"] = username

            if password:
                hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                update_fields.append("password = :password")
                params["password"] = hashed_password

            if category_id is not None:
                update_fields.append("category_id = :category_id")
                params["category_id"] = category_id

            if is_admin is not None:
                update_fields.append("is_admin = :is_admin")
                params["is_admin"] = is_admin

            if is_permission is not None:
                update_fields.append("is_permission = :is_permission")
                params["is_permission"] = is_permission

            # 添加更新時間
            update_fields.append("updated_at = CURRENT_TIMESTAMP")

            # 執行更新
            session.execute(
                text(
                    f"""
                    UPDATE {users_table.name} 
                    SET {", ".join(update_fields)}
                    WHERE id = :user_id
                """
                ),
                params,
            )

            session.commit()
            logger.info(f"Updated user {user_id}")

            return {"id": user_id}
        except json.JSONDecodeError as e:
            logger.error("無效的 JSON 格式")
            self.set_status(400)
            return {"error": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            logger.exception(f"修改用戶失敗: {e}")
            self.set_status(500)
            return {"error": f"Failed to modify user: {str(e)}"}

    @tornado.concurrent.run_on_executor
    def modify_user(self, user_id):
        """_modify_user() 的包裝器，在線程執行器上運行。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 包含用戶 ID 的字典
        """
        return self._modify_user(user_id)

    @tornado.gen.coroutine
    def modify_user_yield(self, user_id):
        """modify_user 的包裝器，在異步模式下運行。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 包含用戶 ID 的字典
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        if not is_admin:
            self.set_status(403)
            self.finish({"error": "Permission denied"})
            return

        return_json = yield self.modify_user(user_id)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def put(self, user_id):
        """修改用戶信息。

        處理端點：
            PUT /api/v1/users/{user_id}

        Args:
            user_id (str): 用戶 ID
        """
        yield self.modify_user_yield(user_id)

    def _delete_user(self, user_id):
        """刪除用戶。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 包含用戶 ID 的字典
        """
        session, users_table, engine, error = self._get_users_table()
        if error:
            return {"error": "Users table does not exist"}

        # 檢查用戶是否存在
        result = session.execute(
            text(f"SELECT COUNT(*) FROM {users_table.name} WHERE id = :user_id"), {"user_id": user_id}
        )
        if result.scalar() == 0:
            self.set_status(400)
            return {"error": f"User not found: {user_id}"}

        # 刪除用戶
        session.execute(text(f"DELETE FROM {users_table.name} WHERE id = :user_id"), {"user_id": user_id})

        session.commit()
        logger.info(f"Deleted user {user_id}")

        return {"id": user_id}

    @tornado.concurrent.run_on_executor
    def delete_user(self, user_id):
        """_delete_user() 的包裝器，在線程執行器上運行。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 包含用戶 ID 的字典
        """
        return self._delete_user(user_id)

    @tornado.gen.coroutine
    def delete_user_yield(self, user_id):
        """delete_user 的包裝器，在異步模式下運行。

        Args:
            user_id (str): 用戶 ID

        Returns:
            dict: 包含用戶 ID 的字典
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        if not is_admin:
            self.set_status(403)
            self.finish({"error": "Permission denied"})
            return

        return_json = yield self.delete_user(user_id)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def delete(self, user_id):
        """刪除用戶。

        處理端點：
            DELETE /api/v1/users/{user_id}

        Args:
            user_id (str): 用戶 ID
        """
        yield self.delete_user_yield(user_id)


class CurrentUserHandler(base.BaseHandler):
    """處理當前登錄用戶的信息查詢。"""

    def _format_datetime(self, dt_value):
        """格式化日期時間值，適應不同類型

        Args:
            dt_value: 日期時間值，可能是字串或日期時間物件

        Returns:
            str or None: 格式化後的日期時間字串或 None
        """
        if isinstance(dt_value, str):
            return dt_value
        return dt_value.isoformat() if dt_value else None

    def _get_current_user_info(self):
        """獲取當前登錄用戶的信息。

        Returns:
            dict: 用戶信息
        """
        username = self.current_user.get("username", "")

        session = self.get_session()
        metadata = MetaData()
        users_table = tables.get_users_table(
            metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
        )

        # 檢查表是否存在
        engine = session.get_bind()
        if not engine.dialect.has_table(engine.connect(), users_table.name):
            self.set_status(400)
            return {"error": "Users table does not exist"}

        # 查詢用戶
        result = session.execute(
            text(f"SELECT * FROM {users_table.name} WHERE username = :username"), {"username": username}
        )
        user = result.fetchone()

        if not user:
            self.set_status(400)
            return {"error": f"User not found: {username}"}

        # 將結果轉換為字典
        columns = result.keys()
        user_dict = dict(zip(columns, user))

        logger.info(f"Retrieved current user: {user_dict['username']}")
        return {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "category_id": user_dict["category_id"],
            "is_admin": user_dict["is_admin"],
            "is_permission": user_dict["is_permission"],
            "created_at": self._format_datetime(user_dict["created_at"]),
            "updated_at": self._format_datetime(user_dict["updated_at"]),
        }

    @tornado.concurrent.run_on_executor
    def get_current_user_info(self):
        """_get_current_user_info() 的包裝器，在線程執行器上運行。

        Returns:
            dict: 用戶信息
        """
        return self._get_current_user_info()

    @tornado.gen.coroutine
    def get_current_user_info_yield(self):
        """get_current_user_info 的包裝器，在異步模式下運行。

        Returns:
            dict: 用戶信息
        """
        return_json = yield self.get_current_user_info()
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def get(self):
        """獲取當前登錄用戶的信息。

        處理端點：
            GET /api/v1/users/current
        """
        yield self.get_current_user_info_yield()
