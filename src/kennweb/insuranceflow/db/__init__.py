from kennweb.core.db_tasks import DatabaseConnTasks
from kennweb.core.configs.insuranceflow import DATABASE_URL

database_conn = DatabaseConnTasks(
    service_name="insuranceflow",
    db_url=DATABASE_URL
)