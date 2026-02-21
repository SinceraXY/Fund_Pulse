# -*- coding: utf-8 -*-
"""
项目配置文件
"""

import os

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fund-pulse-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'fund.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 基金数据刷新间隔（秒）
    REFRESH_INTERVAL = 60
    
    # 数据获取超时时间（秒）
    REQUEST_TIMEOUT = 5
    
    # 并发线程数
    MAX_WORKERS = 10


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
