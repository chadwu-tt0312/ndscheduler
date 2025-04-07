"""Represents Postgres datastore."""

from sqlalchemy.engine import URL

from ndscheduler.corescheduler.datastore import base


class DatastorePostgres(base.DatastoreBase):

    def get_db_url(self) -> str:
        """Returns the db url to establish a Postgres connection, where db_config is passed in
        on initialization as:
        {
            'user': 'my_user',
            'password': 'my_password',
            'hostname': 'db.hostname.com',
            'port': 8888,
            'database': 'my_db',
            'sslmode': 'disable'
        }

        Returns:
            str: SQLAlchemy 2.0 compatible database URL
        """
        return URL.create(
            drivername="postgresql",
            username=self.db_config["user"],
            password=self.db_config["password"],
            host=self.db_config["hostname"],
            port=self.db_config["port"],
            database=self.db_config["database"],
            query={"sslmode": self.db_config["sslmode"]},
        ).render_as_string(hide_password=False)
