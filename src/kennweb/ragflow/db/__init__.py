from kennweb.core.db_tasks import DatabaseConnTasks
from kennweb.core.configs.ragflow import DATABASE_URL

database_conn = DatabaseConnTasks(
    service_name="ragflow",
    db_url=DATABASE_URL
)