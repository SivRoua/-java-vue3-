import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
import time
from config.settings import SQLALCHEMY_DATABASE_URI

# 配置日志
logger = logging.getLogger(__name__)

# 创建数据库引擎
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URI,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600
    )
    logger.info("数据库引擎创建成功")
except Exception as e:
    logger.error(f"创建数据库引擎失败: {str(e)}")
    raise

# 创建数据库会话工厂
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# 创建基本模型类
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """初始化数据库"""
    try:
        # 导入所有模型以确保它们已经注册
        import models.user
        import models.sensor_data
        import models.device_status
        import models.operation_log
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"初始化数据库失败: {str(e)}")
        raise

def shutdown_session(exception=None):
    """关闭数据库会话"""
    try:
        db_session.remove()
        logger.debug("数据库会话已关闭")
    except Exception as e:
        logger.error(f"关闭数据库会话失败: {str(e)}")

class Config:
    """Flask应用的数据库配置"""
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_MAX_OVERFLOW = 10

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
    
    # 其他配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

def get_db_session():
    """获取数据库会话"""
    try:
        session = db_session()
        return session
    except Exception as e:
        logger.error(f"获取数据库会话失败: {str(e)}")
        raise

def init_db(max_retries=3, retry_delay=5):
    """初始化数据库连接和表结构"""
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            # 验证数据库连接
            connection = engine.connect()
            connection.close()
            logger.info("数据库连接成功")
            
            # 创建所有表
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表结构创建/验证成功")
            
            # 确保阈值设置表存在
            try:
                # 导入需要在此处导入以避免循环导入
                from create_threshold_table import create_threshold_table
                if create_threshold_table():
                    logger.info("阈值设置表创建和初始化成功")
                else:
                    logger.warning("阈值设置表创建或初始化出现问题")
            except Exception as table_err:
                logger.warning(f"创建阈值设置表时出错: {str(table_err)}")
                
            return True
            
        except Exception as e:
            last_error = e
            retry_count += 1
            logger.error(f"数据库初始化失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            
            if retry_count < max_retries:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            
    logger.error(f"数据库初始化失败，已达到最大重试次数: {str(last_error)}")
    raise last_error 