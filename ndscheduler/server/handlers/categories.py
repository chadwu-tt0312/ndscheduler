"""Handler for categories endpoint."""

import json
import logging
import tornado.concurrent
import tornado.gen
import tornado.web

from sqlalchemy import MetaData, text

from ndscheduler.server.handlers import base
from ndscheduler.corescheduler.datastore import tables

logger = logging.getLogger(__name__)


class Handler(base.BaseHandler):
    """Handler for categories endpoint."""

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

    def _get_categories_table(self):
        """獲取 categories 資料表和 session

        Returns:
            tuple: (session, categories_table, engine, error) 元組
        """
        session = self.get_session()
        metadata = MetaData()
        categories_table = tables.get_categories_table(
            metadata,
            self.datastore.table_names.get("categories_tablename", "scheduler_categories"),
        )

        # 檢查表是否存在
        engine = session.get_bind()
        if not engine.dialect.has_table(engine.connect(), categories_table.name):
            self.set_status(400)
            return session, categories_table, engine, True

        return session, categories_table, engine, False

    def _format_category(self, category):
        """格式化分類數據

        Args:
            category (dict): 分類數據字典

        Returns:
            dict: 格式化後的分類數據
        """
        return {
            "id": category["id"],
            "name": category["name"],
            "description": category["description"],
            "created_at": self._format_datetime(category["created_at"]),
            "updated_at": self._format_datetime(category["updated_at"]),
        }

    def _get_category(self, category_id):
        """返回特定分類的信息。

        這是一個阻塞操作。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 分類信息
        """
        session, categories_table, engine, error = self._get_categories_table()
        if error:
            return {"error": "Categories table does not exist"}

        # 使用 text 查詢特定分類
        result = session.execute(text(f"SELECT * FROM {categories_table.name} WHERE id = :id"), {"id": category_id})
        category = result.fetchone()

        if not category:
            self.set_status(404)
            return {"error": "Category not found"}

        columns = result.keys()
        category_dict = dict(zip(columns, category))

        logger.info(f"Found category with id {category_id}")

        return self._format_category(category_dict)

    @tornado.concurrent.run_on_executor
    def get_category(self, category_id):
        """_get_category() 的包裝器，在線程執行器上運行。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 分類信息
        """
        return self._get_category(category_id)

    @tornado.gen.coroutine
    def get_category_yield(self, category_id):
        """get_category 的包裝器，在異步模式下運行。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 分類信息
        """
        return_json = yield self.get_category(category_id)
        self.finish(return_json)

    def _get_categories(self):
        """返回所有分類的信息字典。

        這是一個阻塞操作。

        Returns:
            dict: 所有分類信息
        """
        session, categories_table, engine, error = self._get_categories_table()
        if error:
            return {"error": "Categories table does not exist"}

        # 使用 text 查詢所有分類
        result = session.execute(text(f"SELECT * FROM {categories_table.name}"))
        columns = result.keys()
        categories = [dict(zip(columns, row)) for row in result.fetchall()]

        logger.info(f"Found {len(categories)} categories")

        return {"categories": [self._format_category(category) for category in categories]}

    @tornado.concurrent.run_on_executor
    def get_categories(self):
        """_get_categories() 的包裝器，在線程執行器上運行。

        Returns:
            dict: 所有分類信息
        """
        return self._get_categories()

    @tornado.gen.coroutine
    def get_categories_yield(self):
        """get_categories 的包裝器，在異步模式下運行。

        Returns:
            dict: 所有分類信息
        """
        return_json = yield self.get_categories()
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def get(self, category_id=None):
        """返回一個分類或多個分類信息。

        處理兩個端點：
            GET /api/v1/categories                     (當 category_id == None)
            GET /api/v1/categories/{category_id}       (當 category_id != None)

        Args:
            category_id (str, optional): 分類 ID
        """
        if category_id is None:
            yield self.get_categories_yield()
        else:
            yield self.get_category_yield(category_id)

    def _add_category(self):
        """新增分類。

        Returns:
            dict: 包含分類 ID 的字典
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        if not is_admin:
            self.set_status(403)
            return {"error": "Permission denied"}

        try:
            data = json.loads(self.request.body.decode())
            name = data.get("name")
            description = data.get("description")

            if not name:
                self.set_status(400)
                return {"error": "Name is required"}

            session, categories_table, engine, error = self._get_categories_table()
            if error:
                return {"error": "Categories table does not exist"}

            # 檢查名稱是否已存在
            result = session.execute(
                text(f"SELECT COUNT(*) FROM {categories_table.name} WHERE name = :name"), {"name": name}
            )
            if result.scalar() > 0:
                self.set_status(400)
                return {"error": "Category name already exists"}

            # 新增分類
            result = session.execute(
                text(
                    f"""
                    INSERT INTO {categories_table.name} 
                    (name, description, created_at, updated_at) 
                    VALUES (:name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """
                ),
                {"name": name, "description": description},
            )

            # 獲取插入的 ID
            inserted_id = result.scalar()

            session.commit()
            logger.info(f"Created new category: {name}")

            return {"id": inserted_id}
        except json.JSONDecodeError as e:
            logger.error("無效的 JSON 格式")
            self.set_status(400)
            return {"error": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            logger.exception(f"新增分類失敗: {e}")
            self.set_status(500)
            return {"error": f"Failed to add category: {str(e)}"}

    @tornado.concurrent.run_on_executor
    def add_category(self):
        """_add_category() 的包裝器，在線程執行器上運行。

        Returns:
            dict: 包含分類 ID 的字典
        """
        return self._add_category()

    @tornado.gen.coroutine
    def add_category_yield(self):
        """add_category 的包裝器，在異步模式下運行。

        Returns:
            dict: 包含分類 ID 的字典
        """
        return_json = yield self.add_category()
        if "error" in return_json and return_json["error"] == "Permission denied":
            self.set_status(403)
        else:
            self.set_status(201)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def post(self):
        """新增分類。

        處理端點：
            POST /api/v1/categories
        """
        yield self.add_category_yield()

    def _modify_category(self, category_id):
        """修改分類。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 操作結果
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        if not is_admin:
            self.set_status(403)
            return {"error": "Permission denied"}

        try:
            data = json.loads(self.request.body.decode())
            name = data.get("name")
            description = data.get("description")

            if not name:
                self.set_status(400)
                return {"error": "Name is required"}

            session, categories_table, engine, error = self._get_categories_table()
            if error:
                return {"error": "Categories table does not exist"}

            # 檢查分類是否存在
            result = session.execute(
                text(f"SELECT id FROM {categories_table.name} WHERE id = :id"), {"id": category_id}
            )
            if not result.fetchone():
                self.set_status(404)
                return {"error": "Category not found"}

            # 檢查名稱是否已被其他分類使用
            result = session.execute(
                text(f"SELECT id FROM {categories_table.name} WHERE name = :name AND id != :id"),
                {"name": name, "id": category_id},
            )
            if result.fetchone():
                self.set_status(400)
                return {"error": "Category name already exists"}

            # 更新分類
            session.execute(
                text(
                    f"""
                    UPDATE {categories_table.name} 
                    SET name = :name, description = :description, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """
                ),
                {"name": name, "description": description, "id": category_id},
            )

            session.commit()
            logger.info(f"Updated category with id {category_id}")

            return {"id": category_id}
        except json.JSONDecodeError as e:
            logger.error("無效的 JSON 格式")
            self.set_status(400)
            return {"error": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            logger.exception(f"修改分類失敗: {e}")
            self.set_status(500)
            return {"error": f"Failed to modify category: {str(e)}"}

    @tornado.concurrent.run_on_executor
    def modify_category(self, category_id):
        """_modify_category() 的包裝器，在線程執行器上運行。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 操作結果
        """
        return self._modify_category(category_id)

    @tornado.gen.coroutine
    def modify_category_yield(self, category_id):
        """modify_category 的包裝器，在異步模式下運行。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 操作結果
        """
        return_json = yield self.modify_category(category_id)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def put(self, category_id):
        """修改分類。

        處理端點：
            PUT /api/v1/categories/{category_id}

        Args:
            category_id (str): 分類 ID
        """
        yield self.modify_category_yield(category_id)

    def _delete_category(self, category_id):
        """刪除分類。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 操作結果
        """
        # 檢查權限
        is_admin = self.current_user.get("is_admin", False)
        if not is_admin:
            self.set_status(403)
            return {"error": "Permission denied"}

        session, categories_table, engine, error = self._get_categories_table()
        if error:
            return {"error": "Categories table does not exist"}

        # 檢查分類是否存在
        result = session.execute(text(f"SELECT id FROM {categories_table.name} WHERE id = :id"), {"id": category_id})
        if not result.fetchone():
            self.set_status(404)
            return {"error": "Category not found"}

        # 刪除分類
        session.execute(text(f"DELETE FROM {categories_table.name} WHERE id = :id"), {"id": category_id})

        session.commit()
        logger.info(f"Deleted category with id {category_id}")

        return {"id": category_id}

    @tornado.concurrent.run_on_executor
    def delete_category(self, category_id):
        """_delete_category() 的包裝器，在線程執行器上運行。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 操作結果
        """
        return self._delete_category(category_id)

    @tornado.gen.coroutine
    def delete_category_yield(self, category_id):
        """delete_category 的包裝器，在異步模式下運行。

        Args:
            category_id (str): 分類 ID

        Returns:
            dict: 操作結果
        """
        return_json = yield self.delete_category(category_id)
        self.finish(return_json)

    @tornado.web.removeslash
    @tornado.gen.coroutine
    def delete(self, category_id):
        """刪除分類。

        處理端點：
            DELETE /api/v1/categories/{category_id}

        Args:
            category_id (str): 分類 ID
        """
        yield self.delete_category_yield(category_id)
