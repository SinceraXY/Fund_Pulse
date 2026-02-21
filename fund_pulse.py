#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金实盘波动监控工具
功能：实时获取基金估值变动，计算持仓盈亏，美化终端展示
"""

import urllib.request
import json
import time
import os
import concurrent.futures
from datetime import datetime
from typing import Dict, Optional, List, Any

# ================= 你的持仓配置 (2026/02/04) =================
MY_HOLDINGS: Dict[str, float] = {
    "016533": 100,   # 嘉实纳斯达克100ETF联接(QDII)C
    "021458": 200,   # 易方达恒生红利低波联接C
    "022365": 300,   # 永赢科技智选混合C
    "019305": 400    # 摩根标普500指数(QDII)C
}
# ==========================================================

# ================= 终端颜色配置 =================
class Colors:
    """终端颜色常量"""
    RED = '\033[91m'       # 涨/盈利
    GREEN = '\033[92m'     # 跌/亏损
    YELLOW = '\033[93m'    # 警告
    BLUE = '\033[94m'      # 信息
    MAGENTA = '\033[95m'   # 强调
    CYAN = '\033[96m'      # 标题
    WHITE = '\033[97m'     # 普通
    RESET = '\033[0m'      # 重置
    BOLD = '\033[1m'       # 加粗
    DIM = '\033[2m'        # 暗淡


class FundAPI:
    """基金数据获取接口"""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://fund.eastmoney.com/"
    }
    TIMEOUT = 5
    
    @staticmethod
    def fetch_from_eastmoney(code: str) -> Optional[Dict]:
        """从天天基金网获取数据"""
        try:
            timestamp = int(time.time() * 1000)
            url = f"http://fundgz.1234567.com.cn/js/{code}.js?rt={timestamp}"
            req = urllib.request.Request(url, headers=FundAPI.HEADERS)
            with urllib.request.urlopen(req, timeout=FundAPI.TIMEOUT) as response:
                content = response.read().decode('utf-8')
                start, end = content.find('{'), content.find('}') + 1
                if start == -1:
                    return None
                return json.loads(content[start:end])
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
            return None


def get_fund_data(code: str) -> Optional[Dict]:
    """获取基金数据"""
    data = FundAPI.fetch_from_eastmoney(code)
    if data and 'gszzl' in data:
        return data
    return None


def process_one_fund(code: str, amount: float) -> Dict[str, Any]:
    """处理单个基金数据"""
    data = get_fund_data(code)
    
    if data:
        try:
            rate = float(data.get('gszzl', 0))
            profit = amount * (rate / 100)
            name = data.get('name', '未知基金')
            return {
                "code": code,
                "name": name,
                "rate": rate,
                "profit": profit,
                "amount": amount,
                "success": True
            }
        except (ValueError, TypeError):
            pass
    
    return {
        "code": code,
        "name": "获取失败",
        "amount": amount,
        "success": False,
        "profit": 0,
        "rate": 0
    }


def get_display_len(s: str) -> int:
    """计算字符串显示长度（中文算2格，英文算1格）"""
    length = 0
    for char in s:
        if '\u4e00' <= char <= '\u9fff':
            length += 2
        elif char in '（）【】《》、，。！？；：':
            length += 2
        else:
            length += 1
    return length


def pad_string(s: str, width: int) -> str:
    """智能填充空格以对齐中英文混合字符串"""
    display_len = get_display_len(s)
    padding = width - display_len
    return s + " " * max(0, padding)


def draw_bar(rate: float, max_blocks: int = 20) -> str:
    """绘制涨跌柱状图"""
    blocks = int(abs(rate) / 0.25)
    blocks = min(blocks, max_blocks)
    
    if blocks == 0:
        return f"{Colors.DIM}{'─' * 3}{Colors.RESET}"
    
    if rate > 0:
        return f"{Colors.RED}{'▲' * blocks}{Colors.RESET}"
    else:
        return f"{Colors.GREEN}{'▼' * blocks}{Colors.RESET}"


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """打印标题头"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"{Colors.CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{' ' * 20}基金实盘波动监控中心{' ' * 20}║{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.DIM}  更新时间: {now}{Colors.RESET}")
    print()
    
    print(f"{Colors.BOLD}{'代码':<8} {'基金名称':<30} {'持仓金额':>10} {'预估盈亏':>10} {'涨跌幅':>8}  {'波动图'}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 90}{Colors.RESET}")


def print_fund_row(item: Dict[str, Any]):
    """打印单行基金数据"""
    if not item['success']:
        print(f"{Colors.YELLOW}{item['code']:<8}{Colors.RESET} "
              f"{pad_string('⚠ 数据获取失败', 30)} "
              f"{item['amount']:>10.2f} "
              f"{'--':>10} "
              f"{'--':>8}")
        return
    
    if item['profit'] > 0:
        profit_color = Colors.RED
        rate_color = Colors.RED
    elif item['profit'] < 0:
        profit_color = Colors.GREEN
        rate_color = Colors.GREEN
    else:
        profit_color = Colors.WHITE
        rate_color = Colors.WHITE
    
    name_str = pad_string(item['name'][:16], 30)
    profit_str = f"{item['profit']:+.2f}"
    rate_str = f"{item['rate']:+.2f}%"
    bar_chart = draw_bar(item['rate'])
    
    print(f"{item['code']:<8} "
          f"{name_str} "
          f"{item['amount']:>10.2f} "
          f"{profit_color}{profit_str:>10}{Colors.RESET} "
          f"{rate_color}{rate_str:>8}{Colors.RESET}  "
          f"{bar_chart}")


def print_summary(total_profit: float, total_amount: float, success_count: int, total_count: int):
    """打印汇总信息"""
    print(f"{Colors.DIM}{'─' * 90}{Colors.RESET}")
    
    if total_profit > 0:
        summary_color = Colors.RED
        status = "盈利"
    elif total_profit < 0:
        summary_color = Colors.GREEN
        status = "亏损"
    else:
        summary_color = Colors.WHITE
        status = "持平"
    
    total_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0
    
    print(f"\n{Colors.BOLD}【持仓汇总】{Colors.RESET}")
    print(f"  总持仓金额: {Colors.CYAN}{total_amount:.2f}{Colors.RESET} 元")
    print(f"  预估{status}: {summary_color}{total_profit:+.2f}{Colors.RESET} 元 "
          f"({summary_color}{total_rate:+.2f}%{Colors.RESET})")
    print(f"  数据状态: {success_count}/{total_count} 只基金获取成功")
    
    # 盈亏条形图
    bar_width = 40
    if total_amount > 0:
        profit_ratio = min(abs(total_profit) / (total_amount * 0.05), 1.0)
        filled = int(bar_width * profit_ratio)
        if total_profit >= 0:
            bar = f"{Colors.RED}{'█' * filled}{Colors.DIM}{'░' * (bar_width - filled)}{Colors.RESET}"
        else:
            bar = f"{Colors.GREEN}{'█' * filled}{Colors.DIM}{'░' * (bar_width - filled)}{Colors.RESET}"
        print(f"\n  盈亏可视化: {bar}")


def print_footer(refresh_seconds: int):
    """打印底部信息"""
    print(f"\n{Colors.DIM}{'─' * 90}{Colors.RESET}")
    print(f"{Colors.DIM}  自动刷新倒计时: {refresh_seconds}秒 | 按 Ctrl+C 退出{Colors.RESET}")


def main():
    """主函数"""
    os.system('')
    
    REFRESH_INTERVAL = 60
    
    print(f"\n{Colors.CYAN}正在初始化基金监控系统...{Colors.RESET}")
    time.sleep(1)
    
    try:
        while True:
            start_time = time.time()
            results: List[Dict] = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(process_one_fund, code, amount): code 
                    for code, amount in MY_HOLDINGS.items()
                }
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
            
            results.sort(key=lambda x: x.get("profit", 0), reverse=True)
            
            clear_screen()
            print_header()
            
            total_profit = 0.0
            total_amount = 0.0
            success_count = 0
            
            for item in results:
                print_fund_row(item)
                if item['success']:
                    total_profit += item['profit']
                    total_amount += item['amount']
                    success_count += 1
            
            print_summary(total_profit, total_amount, success_count, len(results))
            
            elapsed = time.time() - start_time
            remaining = max(1, REFRESH_INTERVAL - int(elapsed))
            print_footer(remaining)
            
            for i in range(remaining, 0, -1):
                print(f"\r{Colors.DIM}  下次刷新: {i}秒后...{Colors.RESET}", end="", flush=True)
                time.sleep(1)
                
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}感谢使用，再见！{Colors.RESET}")


if __name__ == "__main__":
    main()
