# -*- coding: utf-8 -*-
"""
数据库初始化模块
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text

db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        db.create_all()

        # 轻量 schema 修复：历史数据库可能缺少新增字段（如 sort_order）
        try:
            engine_name = db.engine.name
            if engine_name == 'sqlite':
                cols = db.session.execute(text("PRAGMA table_info(holdings)"))
                col_names = {row[1] for row in cols}
                if 'sort_order' not in col_names:
                    db.session.execute(text("ALTER TABLE holdings ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"))
                    db.session.commit()
        except Exception:
            # schema 修复失败时不阻断启动（但可能影响排序功能）
            db.session.rollback()
