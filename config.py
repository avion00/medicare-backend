import os

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'postgres')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '123')
    JWT_EXPIRATION_SECONDS = 180000
    