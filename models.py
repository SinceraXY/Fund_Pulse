# -*- coding: utf-8 -*-
"""
数据模型定义
"""

from datetime import datetime
from database import db


class Holding(db.Model):
    """持仓配置模型"""
    __tablename__ = 'holdings'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False, default=0)
    sort_order = db.Column(db.Integer, nullable=False, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'amount': self.amount,
            'sort_order': self.sort_order,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FundSnapshot(db.Model):
    """基金快照记录（用于历史趋势）"""
    __tablename__ = 'fund_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False, index=True)
    name = db.Column(db.String(100))
    rate = db.Column(db.Float)  # 涨跌幅
    profit = db.Column(db.Float)  # 盈亏金额
    amount = db.Column(db.Float)  # 持仓金额
    snapshot_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        db.Index('idx_code_time', 'code', 'snapshot_time'),
    )
    
    def to_dict(self):
        return {
            'code': self.code,
            'name': self.name,
            'rate': self.rate,
            'profit': self.profit,
            'amount': self.amount,
            'snapshot_time': self.snapshot_time.isoformat() if self.snapshot_time else None
        }
