# -*- coding: utf-8 -*-
"""
业务服务层
"""

import urllib.request
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from database import db
from models import Holding, FundSnapshot


class FundAPIService:
    """基金数据获取服务"""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://fund.eastmoney.com/"
    }
    TIMEOUT = 5
    
    @staticmethod
    def fetch_fund_data(code: str) -> Optional[Dict]:
        """从天天基金网获取基金数据"""
        try:
            timestamp = int(time.time() * 1000)
            url = f"http://fundgz.1234567.com.cn/js/{code}.js?rt={timestamp}"
            req = urllib.request.Request(url, headers=FundAPIService.HEADERS)
            with urllib.request.urlopen(req, timeout=FundAPIService.TIMEOUT) as response:
                content = response.read().decode('utf-8')
                start, end = content.find('{'), content.find('}') + 1
                if start == -1:
                    return None
                data = json.loads(content[start:end])
                return {
                    'code': code,
                    'name': data.get('name', ''),
                    'rate': float(data.get('gszzl', 0)),
                    'value': float(data.get('gsz', 0)),  # 估值
                    'time': data.get('gztime', '')
                }
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, 
                TimeoutError, ValueError, TypeError):
            return None
    
class HoldingService:
    """持仓管理服务"""
    
    @staticmethod
    def get_all_holdings() -> List[Dict]:
        """获取所有持仓"""
        holdings = Holding.query.order_by(Holding.sort_order.asc(), Holding.id.asc()).all()
        return [h.to_dict() for h in holdings]
    
    @staticmethod
    def get_holdings_dict() -> Dict[str, float]:
        """获取持仓字典 {code: amount}"""
        holdings = Holding.query.all()
        return {h.code: h.amount for h in holdings}
    
    @staticmethod
    def add_holding(code: str, amount: float, name: str = None) -> Holding:
        """添加或更新持仓"""
        holding = Holding.query.filter_by(code=code).first()
        if holding:
            # 更新持仓金额
            holding.amount = amount
            # 如果提供了名称则更新
            if name:
                holding.name = name
        else:
            # 新增持仓
            # 新增时默认排在最后
            max_sort = db.session.query(db.func.max(Holding.sort_order)).scalar() or 0
            holding = Holding(code=code, amount=amount, name=name, sort_order=max_sort + 1)
            db.session.add(holding)
        db.session.commit()
        return holding

    @staticmethod
    def update_sort_order(order_list: List[str]) -> None:
        """批量更新排序：order_list 为 code 按从上到下的顺序排列"""
        if not order_list:
            return

        code_to_order = {code: idx for idx, code in enumerate(order_list)}
        holdings = Holding.query.filter(Holding.code.in_(order_list)).all()
        for h in holdings:
            if h.code in code_to_order:
                h.sort_order = code_to_order[h.code]
        db.session.commit()

    @staticmethod
    def clear_all_holdings(clear_snapshots: bool = False) -> None:
        """清空持仓；可选同时清空快照数据"""
        from models import FundSnapshot

        Holding.query.delete()
        if clear_snapshots:
            FundSnapshot.query.delete()
        db.session.commit()

    @staticmethod
    def import_holdings(items: List[Dict[str, Any]], replace: bool = True) -> None:
        """批量导入持仓。

        items: [{code, amount, name?}]，顺序即 sort_order。
        replace: True 时先清空再导入；False 时做 upsert（按 code 更新/新增）。
        """
        if replace:
            Holding.query.delete()
            db.session.flush()

        for idx, it in enumerate(items):
            code = str(it.get('code', '')).strip()
            if not code or not code.isdigit():
                continue

            try:
                amount = float(it.get('amount', 0))
            except (TypeError, ValueError):
                continue

            if amount < 0:
                continue

            name = it.get('name', None)
            holding = Holding.query.filter_by(code=code).first()
            if holding:
                holding.amount = amount
                if isinstance(name, str) and name.strip():
                    holding.name = name.strip()
                holding.sort_order = idx
            else:
                holding = Holding(code=code, amount=amount, name=(name.strip() if isinstance(name, str) else None), sort_order=idx)
                db.session.add(holding)

        db.session.commit()
    
    @staticmethod
    def delete_holding(code: str) -> bool:
        """删除持仓"""
        holding = Holding.query.filter_by(code=code).first()
        if holding:
            db.session.delete(holding)
            db.session.commit()
            return True
        return False

    @staticmethod
    def adjust_holding(code: str, delta_amount: float, name: str = None) -> Optional[Holding]:
        """加减仓：在原有 amount 基础上增减（delta_amount 可正可负）"""
        holding = Holding.query.filter_by(code=code).first()
        if not holding:
            return None

        try:
            new_amount = float(holding.amount or 0) + float(delta_amount)
        except (TypeError, ValueError):
            return None

        holding.amount = max(0.0, new_amount)
        if name:
            holding.name = name
        db.session.commit()
        return holding
    
    @staticmethod
    def init_default_holdings():
        """初始化默认持仓数据"""
        default_holdings = {
            "016533": {"amount": 100, "name": "嘉实纳斯达克100ETF联接(QDII)C"},
            "021458": {"amount": 200, "name": "易方达恒生红利低波联接C"},
            "022365": {"amount": 300, "name": "永赢科技智选混合C"},
            "019305": {"amount": 400, "name": "摩根标普500指数(QDII)C"}
        }
        
        for code, data in default_holdings.items():
            if not Holding.query.filter_by(code=code).first():
                holding = Holding(code=code, amount=data['amount'], name=data['name'])
                db.session.add(holding)
        db.session.commit()


class FundSnapshotService:
    """基金快照服务"""
    
    @staticmethod
    def refresh_all_funds() -> List[Dict]:
        """刷新所有基金数据"""
        holdings = HoldingService.get_holdings_dict()
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(FundAPIService.fetch_fund_data, code): code 
                for code in holdings.keys()
            }
            for future in concurrent.futures.as_completed(futures):
                code = futures[future]
                data = future.result()
                amount = holdings.get(code, 0)
                
                if data:
                    profit = amount * (data['rate'] / 100)
                    result = {
                        'code': code,
                        'name': data['name'],
                        'rate': data['rate'],
                        'profit': profit,
                        'amount': amount,
                        'success': True
                    }
                    
                    # 保存快照
                    snapshot = FundSnapshot(
                        code=code,
                        name=data['name'],
                        rate=data['rate'],
                        profit=profit,
                        amount=amount
                    )
                    db.session.add(snapshot)
                else:
                    result = {
                        'code': code,
                        'name': '获取失败',
                        'rate': 0,
                        'profit': 0,
                        'amount': amount,
                        'success': False
                    }
                
                results.append(result)
        
        db.session.commit()
        
        # 按盈亏排序
        results.sort(key=lambda x: x.get('profit', 0), reverse=True)
        return results
    
    @staticmethod
    def get_history(code: str, days: int = 7) -> List[Dict]:
        """获取基金历史数据"""
        start_time = datetime.utcnow() - timedelta(days=days)
        snapshots = FundSnapshot.query.filter(
            FundSnapshot.code == code,
            FundSnapshot.snapshot_time >= start_time
        ).order_by(FundSnapshot.snapshot_time).all()
        return [s.to_dict() for s in snapshots]
    
    @staticmethod
    def get_today_summary() -> Dict:
        """获取今日汇总数据"""
        # 从持仓表获取总金额
        holdings = Holding.query.all()
        holding_codes = [h.code for h in holdings]
        total_amount = sum(h.amount for h in holdings)

        # 没有任何持仓时，汇总直接归零，避免被历史快照影响
        if not holding_codes:
            return {
                'total_amount': 0,
                'total_profit': 0,
                'total_rate': 0,
                'success_count': 0,
                'total_count': 0,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 获取今日最新快照数据
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        latest_snapshots = db.session.query(FundSnapshot).filter(
            FundSnapshot.snapshot_time >= today_start,
            FundSnapshot.code.in_(holding_codes)
        ).order_by(FundSnapshot.snapshot_time.desc()).all()
        
        # 按code去重，取最新
        seen = set()
        unique_snapshots = []
        for s in latest_snapshots:
            if s.code not in seen:
                seen.add(s.code)
                unique_snapshots.append(s)
        
        # 计算盈亏
        total_profit = sum(s.profit for s in unique_snapshots)
        # 说明：涨跌幅为 0 也属于成功获取（例如盘中刚好 0.00%）。
        # refresh_all_funds 只有在成功获取数据时才写入快照，因此“有快照”即可视为成功。
        success_count = len(unique_snapshots)
        
        return {
            'total_amount': total_amount,
            'total_profit': total_profit,
            'total_rate': (total_profit / total_amount * 100) if total_amount > 0 else 0,
            'success_count': success_count,
            'total_count': len(holdings),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def get_profit_trend(days: int = 7) -> List[Dict]:
        """获取盈亏趋势数据"""
        holdings = Holding.query.all()
        holding_codes = [h.code for h in holdings]
        if not holding_codes:
            return []

        start_time = datetime.utcnow() - timedelta(days=days)
        
        # 按日期分组统计
        from sqlalchemy import func
        
        daily_stats = db.session.query(
            func.date(FundSnapshot.snapshot_time).label('date'),
            func.sum(FundSnapshot.profit).label('total_profit'),
            func.sum(FundSnapshot.amount).label('total_amount')
        ).filter(
            FundSnapshot.snapshot_time >= start_time,
            FundSnapshot.code.in_(holding_codes)
        ).group_by(
            func.date(FundSnapshot.snapshot_time)
        ).order_by(
            func.date(FundSnapshot.snapshot_time)
        ).all()
        
        return [{
            'date': str(stat.date),
            'profit': stat.total_profit,
            'amount': stat.total_amount
        } for stat in daily_stats]
