from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, inspect, insert
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.engine.reflection import Inspector
from typing import cast
from config.database import Config
import logging
import datetime

logger = logging.getLogger(__name__)

def create_threshold_table():
    """创建阈值设置表并初始化默认阈值"""
    try:
        # 创建数据库引擎
        engine = cast(Engine, create_engine(Config.SQLALCHEMY_DATABASE_URI))
        metadata = MetaData()
        
        # 检查表是否存在
        inspector = cast(Inspector, inspect(engine))
        table_exists = inspector.has_table('threshold_settings')
        
        # 定义阈值设置表
        threshold_settings: Table = Table(
            'threshold_settings', 
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', String(50), nullable=False, comment='规则名称'),
            Column('type', String(20), nullable=False, comment='监测类型'),
            Column('operator', String(5), nullable=False, comment='触发条件操作符'),
            Column('threshold', Float, nullable=False, comment='阈值'),
            Column('enabled', Boolean, default=True, comment='是否启用'),
            Column('create_time', DateTime, default=datetime.datetime.utcnow, comment='创建时间'),
            Column('update_time', DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, comment='更新时间'),
            Column('user_id', Integer, nullable=True, comment='创建者ID'),
        )

        # 如果表不存在，创建表
        if not table_exists:
            metadata.create_all(engine, tables=[threshold_settings])
            logger.info("阈值设置表创建成功")
            
            # 插入默认数据
            default_thresholds = [
                {
                    'name': '高温警报',
                    'type': 'temperature',
                    'operator': '>',
                    'threshold': 30.0,
                    'enabled': True,
                    'create_time': datetime.datetime.utcnow(),
                    'update_time': datetime.datetime.utcnow()
                },
                {
                    'name': '低温警报',
                    'type': 'temperature',
                    'operator': '<',
                    'threshold': 15.0,
                    'enabled': True,
                    'create_time': datetime.datetime.utcnow(),
                    'update_time': datetime.datetime.utcnow()
                },
                {
                    'name': '湿度过高警报',
                    'type': 'humidity',
                    'operator': '>',
                    'threshold': 80.0,
                    'enabled': True,
                    'create_time': datetime.datetime.utcnow(),
                    'update_time': datetime.datetime.utcnow()
                },
                {
                    'name': '湿度过低警报',
                    'type': 'humidity',
                    'operator': '<',
                    'threshold': 40.0,
                    'enabled': True,
                    'create_time': datetime.datetime.utcnow(),
                    'update_time': datetime.datetime.utcnow()
                },
                {
                    'name': '土壤湿度过高警报',
                    'type': 'soil_moisture',
                    'operator': '>',
                    'threshold': 90.0,
                    'enabled': True,
                    'create_time': datetime.datetime.utcnow(),
                    'update_time': datetime.datetime.utcnow()
                }
            ]
            
            connection: Connection = engine.connect()
            for threshold in default_thresholds:
                stmt = insert(threshold_settings).values(**threshold)
                connection.execute(stmt)
            connection.close()
            
            logger.info("阈值设置表初始化数据完成")
        else:
            logger.info("阈值设置表已存在，无需重复创建")
        
        return True
    except Exception as e:
        logger.error(f"创建阈值设置表时出错: {str(e)}")
        return False

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 执行创建表操作
    result = create_threshold_table()
    print(f"创建阈值设置表: {'成功' if result else '失败'}") 