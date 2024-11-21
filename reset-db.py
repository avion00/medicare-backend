import psycopg2
from config import Config
from utils.db import get_db_connection
def reset_database():
    try:
        # Connect to PostgreSQL server
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()

        # Drop the existing database
        cursor.execute(f"DROP DATABASE IF EXISTS {Config.DB_NAME};")
        print(f"Database {Config.DB_NAME} dropped successfully.")

        # Recreate the database
        cursor.execute(f"CREATE DATABASE {Config.DB_NAME};")
        print(f"Database {Config.DB_NAME} created successfully.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error resetting the database: {e}")

if __name__ == '__main__':
    reset_database()
