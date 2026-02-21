#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 初始化数据库并启动Web服务
"""

import os
import sys

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models import Holding
from services import HoldingService


def main():
    """主函数"""
    # 创建应用
    app = create_app('development')
    
    with app.app_context():
        # 创建数据目录
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # 创建数据库表
        db.create_all()
        
        # 初始化默认持仓数据（可选）
        # 为避免“清空持仓后重启又自动出现默认持仓”，默认不初始化。
        # 需要初始化时设置环境变量：INIT_DEFAULT_HOLDINGS=1
        init_defaults = os.environ.get('INIT_DEFAULT_HOLDINGS', '').lower() in ('1', 'true', 'yes', 'y')
        if init_defaults and Holding.query.count() == 0:
            print("正在初始化默认持仓数据...")
            HoldingService.init_default_holdings()
            print("默认持仓数据初始化完成")
    
    print("\n" + "=" * 50)
    print("  基金实盘波动监控系统启动中...")
    print("  访问地址: http://localhost:5000")
    print("=" * 50 + "\n")
    
    # 启动服务
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes', 'y')
    # 默认关闭 debug & reloader，避免开源项目默认暴露调试器
    app.run(host='0.0.0.0', port=5000, debug=debug, use_reloader=debug)


if __name__ == '__main__':
    main()
