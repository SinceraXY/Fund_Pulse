# -*- coding: utf-8 -*-
"""
API路由模块
"""

from flask import Blueprint, jsonify, request
from services import HoldingService, FundSnapshotService

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/holdings', methods=['GET'])
def get_holdings():
    """获取所有持仓"""
    holdings = HoldingService.get_all_holdings()
    return jsonify({'success': True, 'data': holdings})


@api_bp.route('/holdings/reorder', methods=['POST'])
def reorder_holdings():
    """更新持仓展示顺序"""
    data = request.get_json() or {}
    codes = data.get('codes')
    if not isinstance(codes, list) or not all(isinstance(c, str) and c for c in codes):
        return jsonify({'success': False, 'message': 'codes 必须为非空字符串数组'}), 400

    HoldingService.update_sort_order(codes)
    return jsonify({'success': True})


@api_bp.route('/holdings/clear', methods=['POST'])
def clear_holdings():
    """一键清空持仓（可选清空快照）"""
    data = request.get_json() or {}
    clear_snapshots = bool(data.get('clear_snapshots', False))
    HoldingService.clear_all_holdings(clear_snapshots=clear_snapshots)
    return jsonify({'success': True})


@api_bp.route('/holdings/import', methods=['POST'])
def import_holdings():
    """一键导入持仓"""
    data = request.get_json() or {}
    items = data.get('items')
    replace = bool(data.get('replace', True))
    if not isinstance(items, list):
        return jsonify({'success': False, 'message': 'items 必须为数组'}), 400

    HoldingService.import_holdings(items, replace=replace)
    return jsonify({'success': True})


@api_bp.route('/holdings/export', methods=['GET'])
def export_holdings():
    """导出持仓（用于备份/迁移）"""
    holdings = HoldingService.get_all_holdings()
    return jsonify({'success': True, 'data': holdings})


@api_bp.route('/holdings', methods=['POST'])
def add_holding():
    """添加持仓"""
    data = request.get_json() or {}
    code = data.get('code')
    amount = data.get('amount', 0)
    name = data.get('name', '')
    
    if not isinstance(code, str) or not code.strip():
        return jsonify({'success': False, 'message': '基金代码不能为空'}), 400

    code = code.strip()
    if not code.isdigit() or len(code) not in (6, 7, 8, 9, 10):
        return jsonify({'success': False, 'message': '基金代码格式不正确'}), 400

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'amount 必须为数字'}), 400

    if amount < 0:
        return jsonify({'success': False, 'message': 'amount 不能为负数'}), 400
    
    holding = HoldingService.add_holding(code, amount, name)
    return jsonify({'success': True, 'data': holding.to_dict()})


@api_bp.route('/holdings/<code>', methods=['DELETE'])
def delete_holding(code):
    """删除持仓"""
    success = HoldingService.delete_holding(code)
    if success:
        return jsonify({'success': True, 'message': '删除成功'})
    return jsonify({'success': False, 'message': '持仓不存在'}), 404


@api_bp.route('/holdings/<code>/adjust', methods=['POST'])
def adjust_holding(code):
    """加减仓（按 delta_amount 增减）"""
    data = request.get_json() or {}
    delta_amount = data.get('delta_amount')
    name = data.get('name', None)

    if delta_amount is None:
        return jsonify({'success': False, 'message': 'delta_amount 不能为空'}), 400

    holding = HoldingService.adjust_holding(code, delta_amount, name)
    if not holding:
        return jsonify({'success': False, 'message': '持仓不存在或参数不合法'}), 400

    return jsonify({'success': True, 'data': holding.to_dict()})


@api_bp.route('/refresh', methods=['POST'])
def refresh_funds():
    """刷新基金数据"""
    results = FundSnapshotService.refresh_all_funds()
    summary = FundSnapshotService.get_today_summary()
    return jsonify({
        'success': True,
        'data': {
            'funds': results,
            'summary': summary
        }
    })


@api_bp.route('/summary', methods=['GET'])
def get_summary():
    """获取汇总数据"""
    summary = FundSnapshotService.get_today_summary()
    return jsonify({'success': True, 'data': summary})


@api_bp.route('/history/<code>', methods=['GET'])
def get_history(code):
    """获取基金历史数据"""
    days = request.args.get('days', 7, type=int)
    history = FundSnapshotService.get_history(code, days)
    return jsonify({'success': True, 'data': history})


@api_bp.route('/trend', methods=['GET'])
def get_trend():
    """获取盈亏趋势"""
    days = request.args.get('days', 7, type=int)
    trend = FundSnapshotService.get_profit_trend(days)
    return jsonify({'success': True, 'data': trend})
