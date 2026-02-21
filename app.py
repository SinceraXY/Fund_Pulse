# -*- coding: utf-8 -*-
"""
基金实盘波动监控 - Web应用入口
"""

import os
from flask import Flask, render_template
from config import config
from database import init_db
from routes import api_bp


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 确保数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 初始化数据库
    init_db(app)
    
    # 注册路由
    app.register_blueprint(api_bp)
    
    # 主页路由
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app


if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)
