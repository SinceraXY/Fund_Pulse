# Fund_Pulse - 基金实盘波动可视化监控

一个轻量的基金持仓监控工具：

- Web 可视化仪表盘（实时估值、盈亏、持仓分布、趋势图）
- 支持持仓新增/编辑/删除
- 支持一键加仓/减仓（快捷 +100 / -100，可自行改前端）
- SQLite 持久化保存快照，用于历史趋势分析

> 说明：本项目数据来源于公开网络接口，仅用于学习与个人研究，不构成投资建议。

---

## 预览

启动后访问：

- http://localhost:5000

---

## 目录结构

```
fund_pulse/
├── app.py                # Flask 应用工厂
├── run.py                # 启动入口（初始化 DB + 默认持仓）
├── config.py             # 配置
├── database.py           # SQLAlchemy 初始化
├── models.py             # 数据模型（持仓/快照）
├── services.py           # 业务服务（抓取/快照/统计）
├── routes.py             # REST API
├── templates/
│   └── index.html        # 前端页面（Bootstrap + Chart.js）
├── data/
│   └── fund.db           # 运行时生成（建议不提交 Git）
└── fund_pulse.py          # 早期终端版本（保留）
```

---

## 环境要求

- Python 3.9+（建议）

---

## 安装与运行

### 1) 安装依赖

```bash
pip install -r requirements.txt
```

### 2) 启动

```bash
python run.py
```

如需初始化内置“示例默认持仓”（仅首次、且当前持仓为空时生效），启动前设置：

```bash
set INIT_DEFAULT_HOLDINGS=1
python run.py
```

然后打开浏览器访问：`http://localhost:5000`

### 3) 停止

在启动服务的终端里按 `Ctrl + C`。

---

## API 简表

- `POST /api/refresh` 刷新全部基金快照并返回列表+汇总
- `GET /api/trend?days=7` 查询近 N 天盈亏趋势
- `GET /api/holdings` 查询持仓
- `POST /api/holdings` 新增/覆盖持仓（传 `code/name/amount`）
- `POST /api/holdings/<code>/adjust` 加减仓（传 `delta_amount`）
- `DELETE /api/holdings/<code>` 删除持仓

---

## 常见问题

### Q1: 为什么我停掉服务后 `netstat` 还能看到 UDP 5000？
Web 服务使用的是 **TCP 5000**。UDP 5000 的占用通常来自其他软件，不影响本项目是否停止。

### Q2: 数据偶尔获取失败？
网络接口可能会波动，失败时页面会显示“失败”状态；可以稍后再刷新。

---

## 开源协议

Apache License 2.0，详见 [LICENSE](./LICENSE)。