"""User management handlers."""

import json
import logging
import tornado.web

from ndscheduler.server.handlers import base
from ndscheduler.corescheduler.datastore import tables

logger = logging.getLogger(__name__)


def check_table_exists(session, table):
    """檢查表格是否存在，如果不存在則拋出異常。"""
    if not table.__table__.exists(session.get_bind()):
        logger.error("Users table does not exist")
        raise tornado.web.HTTPError(500, "Database table not initialized")


class UsersHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        """獲取所有用戶。

        Returns:
            Response in JSON format.
        """
        try:
            # 只有管理員可以查看所有用戶
            if not self.current_user.get("is_admin", False):
                raise tornado.web.HTTPError(403, "Permission denied")

            session = self.get_session()
            users_table = tables.get_users_table(
                session.get_bind().metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
            )

            try:
                if not users_table.exists(session.get_bind()):
                    raise tornado.web.HTTPError(500, "Users table does not exist")
            except Exception as e:
                logger.error(f"Error checking users table: {str(e)}", exc_info=True)
                raise tornado.web.HTTPError(500, "Database error")

            users = session.query(users_table).all()
            logger.info(f"Found {len(users)} users")

            self.write(
                {
                    "users": [
                        {
                            "id": user.id,
                            "username": user.username,
                            "is_admin": user.is_admin,
                            "category_id": user.category_id,
                            "permission": user.permission,
                            "created_at": user.created_at.isoformat() if user.created_at else None,
                            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                        }
                        for user in users
                    ]
                }
            )
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write({"error": str(e)})
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})

    @tornado.web.authenticated
    def post(self):
        """新增用戶。

        Body:
            username: 用戶名
            password: 密碼
            is_admin: 是否為管理員（可選，默認為 False）
            category_id: 分類 ID（可選）
            permission: 權限（可選，默認為 False）

        Returns:
            Response in JSON format.
        """
        try:
            # 只有管理員可以創建用戶
            if not self.current_user.get("is_admin", False):
                raise tornado.web.HTTPError(403, "Permission denied")

            data = json.loads(self.request.body.decode())
            username = data.get("username")
            password = data.get("password")
            is_admin = data.get("is_admin", False)
            category_id = data.get("category_id")
            permission = data.get("permission", False)

            if not username or not password:
                raise tornado.web.HTTPError(400, "Username and password are required")

            session = self.get_session()
            users_table = tables.get_users_table(
                session.get_bind().metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
            )

            try:
                if not users_table.exists(session.get_bind()):
                    raise tornado.web.HTTPError(500, "Users table does not exist")
            except Exception as e:
                logger.error(f"Error checking users table: {str(e)}", exc_info=True)
                raise tornado.web.HTTPError(500, "Database error")

            # 檢查用戶名是否已存在
            existing = session.query(users_table).filter(users_table.c.username == username).first()
            if existing:
                raise tornado.web.HTTPError(400, "Username already exists")

            # 對密碼進行哈希處理
            import bcrypt

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # 新增用戶
            result = session.execute(
                users_table.insert().values(
                    username=username,
                    password=hashed_password,
                    is_admin=is_admin,
                    category_id=category_id,
                    permission=permission,
                )
            )
            session.commit()
            logger.info(f"Created new user: {username}")

            self.set_status(201)
            self.write({"id": result.inserted_primary_key[0]})
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write({"error": str(e)})
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})


class UserHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self, user_id):
        """獲取特定用戶。

        Args:
            user_id: 用戶 ID

        Returns:
            Response in JSON format.
        """
        try:
            # 只有管理員或用戶本人可以查看用戶信息
            is_admin = self.current_user.get("is_admin", False)
            current_username = self.current_user.get("username", "")

            session = self.get_session()
            users_table = tables.get_users_table(
                session.get_bind().metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
            )

            try:
                if not users_table.exists(session.get_bind()):
                    raise tornado.web.HTTPError(500, "Users table does not exist")
            except Exception as e:
                logger.error(f"Error checking users table: {str(e)}", exc_info=True)
                raise tornado.web.HTTPError(500, "Database error")

            user = session.query(users_table).filter(users_table.c.id == user_id).first()
            if not user:
                raise tornado.web.HTTPError(404, "User not found")

            # 檢查權限
            if not is_admin and user.username != current_username:
                raise tornado.web.HTTPError(403, "Permission denied")

            logger.info(f"Retrieved user: {user.username}")
            self.write(
                {
                    "id": user.id,
                    "username": user.username,
                    "is_admin": user.is_admin,
                    "category_id": user.category_id,
                    "permission": user.permission,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
            )
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write({"error": str(e)})
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})

    @tornado.web.authenticated
    def put(self, user_id):
        """更新特定用戶。

        Args:
            user_id: 用戶 ID

        Body:
            username: 用戶名（可選）
            password: 密碼（可選）
            is_admin: 是否為管理員（可選）
            category_id: 分類 ID（可選）
            permission: 權限（可選）

        Returns:
            Response in JSON format.
        """
        try:
            # 只有管理員可以更新用戶信息
            if not self.current_user.get("is_admin", False):
                raise tornado.web.HTTPError(403, "Permission denied")

            data = json.loads(self.request.body.decode())
            username = data.get("username")
            password = data.get("password")
            is_admin = data.get("is_admin")
            category_id = data.get("category_id")
            permission = data.get("permission")

            if not any([username, password, is_admin is not None, category_id is not None, permission is not None]):
                raise tornado.web.HTTPError(400, "At least one field must be provided")

            session = self.get_session()
            users_table = tables.get_users_table(
                session.get_bind().metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
            )

            try:
                if not users_table.exists(session.get_bind()):
                    raise tornado.web.HTTPError(500, "Users table does not exist")
            except Exception as e:
                logger.error(f"Error checking users table: {str(e)}", exc_info=True)
                raise tornado.web.HTTPError(500, "Database error")

            # 檢查用戶是否存在
            user = session.query(users_table).filter(users_table.c.id == user_id).first()
            if not user:
                raise tornado.web.HTTPError(404, "User not found")

            # 檢查用戶名是否與其他用戶衝突
            if username:
                existing = (
                    session.query(users_table)
                    .filter(users_table.c.username == username, users_table.c.id != user_id)
                    .first()
                )
                if existing:
                    raise tornado.web.HTTPError(400, "Username already exists")

            # 構建更新值
            update_values = {}
            if username:
                update_values["username"] = username
            if password:
                import bcrypt

                hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                update_values["password"] = hashed_password
            if is_admin is not None:
                update_values["is_admin"] = is_admin
            if category_id is not None:
                update_values["category_id"] = category_id
            if permission is not None:
                update_values["permission"] = permission

            # 更新用戶
            session.execute(users_table.update().where(users_table.c.id == user_id).values(**update_values))
            session.commit()
            logger.info(f"Updated user {user_id}")

            self.write({"id": user_id})
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write({"error": str(e)})
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})

    @tornado.web.authenticated
    def delete(self, user_id):
        """刪除特定用戶。

        Args:
            user_id: 用戶 ID

        Returns:
            Response in JSON format.
        """
        try:
            # 只有管理員可以刪除用戶
            if not self.current_user.get("is_admin", False):
                raise tornado.web.HTTPError(403, "Permission denied")

            session = self.get_session()
            users_table = tables.get_users_table(
                session.get_bind().metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
            )

            try:
                if not users_table.exists(session.get_bind()):
                    raise tornado.web.HTTPError(500, "Users table does not exist")
            except Exception as e:
                logger.error(f"Error checking users table: {str(e)}", exc_info=True)
                raise tornado.web.HTTPError(500, "Database error")

            # 檢查用戶是否存在
            user = session.query(users_table).filter(users_table.c.id == user_id).first()
            if not user:
                raise tornado.web.HTTPError(404, "User not found")

            # 刪除用戶
            session.execute(users_table.delete().where(users_table.c.id == user_id))
            session.commit()
            logger.info(f"Deleted user {user_id}")

            self.write({"id": user_id})
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write({"error": str(e)})
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})


class CurrentUserHandler(base.BaseHandler):
    """處理當前登錄用戶的信息查詢。"""

    @tornado.web.authenticated
    def get(self):
        """獲取當前登錄用戶的信息。

        Returns:
            Response in JSON format.
        """
        try:
            username = self.current_user.get("username", "")

            session = self.get_session()
            users_table = tables.get_users_table(
                session.get_bind().metadata, self.datastore.table_names.get("users_tablename", "scheduler_users")
            )

            try:
                if not users_table.exists(session.get_bind()):
                    raise tornado.web.HTTPError(500, "Users table does not exist")
            except Exception as e:
                logger.error(f"Error checking users table: {str(e)}", exc_info=True)
                raise tornado.web.HTTPError(500, "Database error")

            user = session.query(users_table).filter(users_table.c.username == username).first()
            if not user:
                raise tornado.web.HTTPError(404, "User not found")

            logger.info(f"Retrieved current user: {user.username}")
            self.write(
                {
                    "id": user.id,
                    "username": user.username,
                    "is_admin": user.is_admin,
                    "category_id": user.category_id,
                    "permission": user.permission,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
            )
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write({"error": str(e)})
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})
