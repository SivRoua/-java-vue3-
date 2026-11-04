import os
import logging
from logging.handlers import RotatingFileHandler

# 确保日志目录存在
if not os.path.exists('logs'):
    os.makedirs('logs')

# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'standard',
            'level': 'INFO',
            'encoding': 'utf-8',
        }
    },
    'loggers': {
        '': {  # 根日志器
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}