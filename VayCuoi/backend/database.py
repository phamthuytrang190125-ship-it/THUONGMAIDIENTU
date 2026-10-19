import psycopg2

DB_HOST = "localhost"
DB_NAME = "wedding_dress_rental"
DB_USER = "postgres" 
DB_PASS = "123456" 

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)