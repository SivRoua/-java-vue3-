import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载 backend/.env（与 settings.py 同级的上一级目录）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# JWT配置
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')  # 在生产环境中应该使用环境变量
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# 数据库配置
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://root:123456@localhost/smart_agriculture?charset=utf8mb4'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 3600
SQLALCHEMY_MAX_OVERFLOW = 10

# 应用配置
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')  # Flask密钥

# 跨域配置
CORS_HEADERS = 'Content-Type' 