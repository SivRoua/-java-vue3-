from functools import wraps
from flask import request, make_response

# 这个中间件已不再使用，由全局after_request处理器替代
# 保留此文件以兼容旧代码，但不再添加CORS头

def cors_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = make_response()
            return response
            
        response = make_response(f(*args, **kwargs))
        return response
        
    return decorated_function