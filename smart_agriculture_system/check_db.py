import traceback
from sqlalchemy import create_engine

try:
    # 从后端配置中导入数据库连接字符串
    from backend.config.settings import SQLALCHEMY_DATABASE_URI
except Exception as e:
    print("无法导入数据库配置:", e)
    traceback.print_exc()
    raise SystemExit(1)


def main():
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        conn = engine.connect()
        print("数据库连接成功")
        conn.close()
    except Exception as e:
        print("数据库连接失败:")
        traceback.print_exc()


if __name__ == '__main__':
    main()
