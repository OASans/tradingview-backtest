# TradingView 指标自动回测系统 — 实施方案

## Context

复刻 Moon Dev 视频中的流程：让 OpenClaw agent 全自动浏览 TradingView 社区指标，提取 Pine Script 源码，转换为 Python 回测，跑 SPY/QQQ 美股数据，找出有 alpha 的策略。结果推送 GitHub，好策略通过 Discord webhook 通知。

## 技术栈

- **backtesting.py** — 回测框架
- **ta** — 技术指标库（替代 pandas_ta，因 Python 3.10 兼容性）
- **yfinance** — 美股数据下载
- **discord-webhook** — Discord 通知

## 回测参数

- 初始资金: $100,000
- 手续费: 0.1%
- 数据: SPY / QQQ 2年日线
- 数据来源: yfinance（本地 CSV 缓存 24 小时）

## 质量阈值（触发 Discord 通知）

| 指标 | 阈值 |
|------|------|
| Return | > 20% |
| Max Drawdown | > -30% |
| 交易次数 | >= 20 |
| Win Rate | > 45% |
| Profit Factor | > 1.3 |

## 工作流程

1. 浏览 TradingView Editor's Picks / 社区指标
2. 提取开源 Pine Script 源码 → `pine_scripts/`
3. 转换为 Python 回测 → `backtests/`
4. 运行回测 → 结果写入 `results/master_results.csv`
5. 好策略 → Discord webhook 通知
6. 每 5 个指标 → git commit + push

## 待用户完成

1. Discord webhook URL（设置 `DISCORD_WEBHOOK_URL` 环境变量）
2. GitHub 认证（`gh auth login`）
3. TradingView 登录（手动一次，cookie 保存）
