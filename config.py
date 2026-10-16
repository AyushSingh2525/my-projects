import os

# Module level variables
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'Ayush2525'
DB_NAME = 'queue_db_pro'
SECRET_KEY = 'super_secret_key'

class Config:
    SECRET_KEY = SECRET_KEY
    DB_HOST = DB_HOST
    DB_PORT = DB_PORT
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    DB_NAME = DB_NAME