"""Category management handlers."""

import json
import logging
import tornado.web

from ndscheduler.server.handlers import base
from ndscheduler.corescheduler.datastore import tables

logger = logging.getLogger(__name__)


def check_table_exists(session, table):
    """檢查表格是否存在，如果不存在則拋出異常。"""
    if not table.exists():
        logger.error("Categories table does not exist")
        raise tornado.web.HTTPError(500, "Database table not initialized")


class CategoriesHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        """獲取所有 categories。

        Returns:
            Response in JSON format.
        """
        try:
            session = self.get_session()
            categories_table = tables.get_categories_table(session.get_bind().metadata)
            check_table_exists(session, categories_table)

            categories = session.query(categories_table).all()
            logger.info(f"Found {len(categories)} categories")

            self.write_json(
                {
                    "categories": [
                        {
                            "id": category.id,
                            "name": category.name,
                            "description": category.description,
                            "created_at": category.created_at.isoformat() if category.created_at else None,
                            "updated_at": category.updated_at.isoformat() if category.updated_at else None,
                        }
                        for category in categories
                    ]
                }
            )
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write_json({"error": str(e)})
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write_json({"error": "Internal server error"})

    @tornado.web.authenticated
    def post(self):
        """新增 category。

        Body:
            name: Category 名稱
            description: Category 描述（可選）

        Returns:
            Response in JSON format.
        """
        try:
            if not self.current_user.get("is_admin", False):
                raise tornado.web.HTTPError(403, "Permission denied")

            data = json.loads(self.request.body.decode())
            name = data.get("name")
            description = data.get("description")

            if not name:
                raise tornado.web.HTTPError(400, "Name is required")

            session = self.get_session()
            categories_table = tables.get_categories_table(session.get_bind().metadata)
            check_table_exists(session, categories_table)

            # 檢查名稱是否已存在
            existing = session.query(categories_table).filter(categories_table.c.name == name).first()
            if existing:
                raise tornado.web.HTTPError(400, "Category name already exists")

            # 新增 category
            result = session.execute(categories_table.insert().values(name=name, description=description))
            session.commit()
            logger.info(f"Created new category: {name}")

            self.write_json({"id": result.inserted_primary_key[0]})
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write_json({"error": str(e)})
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write_json({"error": "Internal server error"})


class CategoryHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self, category_id):
        """獲取特定 category。

        Args:
            category_id: Category ID

        Returns:
            Response in JSON format.
        """
        try:
            session = self.get_session()
            categories_table = tables.get_categories_table(session.get_bind().metadata)
            check_table_exists(session, categories_table)

            category = session.query(categories_table).filter(categories_table.c.id == category_id).first()
            if not category:
                raise tornado.web.HTTPError(404, "Category not found")

            logger.info(f"Retrieved category: {category.name}")
            self.write_json(
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "created_at": category.created_at.isoformat() if category.created_at else None,
                    "updated_at": category.updated_at.isoformat() if category.updated_at else None,
                }
            )
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write_json({"error": str(e)})
        except Exception as e:
            logger.error(f"Error getting category {category_id}: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write_json({"error": "Internal server error"})

    @tornado.web.authenticated
    def put(self, category_id):
        """更新特定 category。

        Args:
            category_id: Category ID

        Body:
            name: Category 名稱
            description: Category 描述（可選）

        Returns:
            Response in JSON format.
        """
        try:
            if not self.current_user.get("is_admin", False):
                raise tornado.web.HTTPError(403, "Permission denied")

            data = json.loads(self.request.body.decode())
            name = data.get("name")
            description = data.get("description")

            if not name:
                raise tornado.web.HTTPError(400, "Name is required")

            session = self.get_session()
            categories_table = tables.get_categories_table(session.get_bind().metadata)
            check_table_exists(session, categories_table)

            # 檢查 category 是否存在
            category = session.query(categories_table).filter(categories_table.c.id == category_id).first()
            if not category:
                raise tornado.web.HTTPError(404, "Category not found")

            # 檢查名稱是否與其他 category 衝突
            existing = (
                session.query(categories_table)
                .filter(categories_table.c.name == name, categories_table.c.id != category_id)
                .first()
            )
            if existing:
                raise tornado.web.HTTPError(400, "Category name already exists")

            # 更新 category
            session.execute(
                categories_table.update()
                .where(categories_table.c.id == category_id)
                .values(name=name, description=description)
            )
            session.commit()
            logger.info(f"Updated category {category_id}: {name}")

            self.write_json({"id": category_id})
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write_json({"error": str(e)})
        except Exception as e:
            logger.error(f"Error updating category {category_id}: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write_json({"error": "Internal server error"})

    @tornado.web.authenticated
    def delete(self, category_id):
        """刪除特定 category。

        Args:
            category_id: Category ID

        Returns:
            Response in JSON format.
        """
        try:
            if not self.current_user.get("is_admin", False):
                raise tornado.web.HTTPError(403, "Permission denied")

            session = self.get_session()
            categories_table = tables.get_categories_table(session.get_bind().metadata)
            check_table_exists(session, categories_table)

            # 檢查 category 是否存在
            category = session.query(categories_table).filter(categories_table.c.id == category_id).first()
            if not category:
                raise tornado.web.HTTPError(404, "Category not found")

            # 刪除 category
            session.execute(categories_table.delete().where(categories_table.c.id == category_id))
            session.commit()
            logger.info(f"Deleted category {category_id}")

            self.write_json({"id": category_id})
        except tornado.web.HTTPError as e:
            self.set_status(e.status_code)
            self.write_json({"error": str(e)})
        except Exception as e:
            logger.error(f"Error deleting category {category_id}: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write_json({"error": "Internal server error"})
