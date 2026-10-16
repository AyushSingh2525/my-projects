import pymysql
from dbutils.pooled_db import PooledDB
import config

try:
    pool = PooledDB(
        creator=pymysql,
        maxconnections=10,
        mincached=2,
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    print("✅ Database connection pool created successfully!")
except Exception as e:
    print(f"❌ Database Connection Error: {e}")

def get_db():
    conn = pool.connection()
    conn.ping(reconnect=True)
    return conn