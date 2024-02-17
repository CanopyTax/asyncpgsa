import os

PORT = os.getenv("DB_PORT", 5432)
HOST = os.getenv("DB_HOST", "localhost")
USER = os.getenv("DB_USER", "postgres")
PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "postgres")

URL = "postgres://{username}:{password}@{host}:{port}/{db_name}".format(
    port=PORT,
    host=HOST,
    username=USER,
    password=PASS,
    db_name=DB_NAME,
)
