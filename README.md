# AI Tool Weekly Review

对 Claude Code、Cursor、Codex 的使用情况进行结构化周度复盘。分析会话文件中的任务分布、效率问题、提示词质量，给出可执行的优化建议。

**核心功能：**
- 自动扫描 Claude Code `.jsonl` 会话文件
- 按项目聚类分析任务量和效率
- 检测会话碎片化、上下文丢失、中断频率等常见问题
- 识别"同任务重复开新会话"等协作陷阱
- 输出结构化报告，支持飞书 Webhook 推送

---

## 安装

```bash
# 克隆仓库
git clone https://github.com/FavorPan/ai-tool-weekly-review.git
cd ai-tool-weekly-review

# 安装依赖
pip install -e .
```

## 使用

### 基础分析（最近7天）

```bash
python -m ai_tool_weekly_review
```

### 指定日期范围

```bash
python -m ai_tool_weekly_review --days 14
python -m ai_tool_weekly_review --start 2026-06-01 --end 2026-06-14
```

### 输出到文件

```bash
python -m ai_tool_weekly_review --output /tmp/report.txt
```

### 发送到飞书（需要 Webhook URL）

```bash
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
python -m ai_tool_weekly_review --feishu
```

---

## 数据来源

| 工具 | 数据路径 |
|------|---------|
| Claude Code | `~/.claude/projects/` |
| Cursor | `~/Library/Application Support/Cursor/` |
| Codex | `~/.claude/` |

> 注意：数据来源为 `.jsonl` 会话文件，无法精确还原使用时长，本工具以**会话数量 + 文件大小**作为代理指标。

---

## 报告结构

```
一、总览
  - 各工具活跃情况（会话数 / 总容量）
  - 估算口径说明

二、按项目分析（按会话量排序）
  - 任务摘要
  - 效率问题（打断频率、重复读取、上下文丢失）
  - 提示词质量审查

三、思维问题与优化建议
  - 最常见的思维陷阱
  - 最常见的协作问题
  - 可执行的改进建议
```

---

## 思维问题四模式

本工具在报告中重点分析以下系统性思维陷阱：

| 模式 | 表现 | 高效路径 |
|------|------|---------|
| 先查代码、后建假设 | 发现现象 → 直接读代码 → 在代码里找原因 | 发现现象 → 描述路径 → 提出假设 → 反推验证 |
| 对问题只定性不定量 | 说"偶尔"、"有时候"，不给概率 | 给出"偶发约 1/N，连续操作 X 次以上" |
| 把技术问题和业务问题混在一起问 | 问"debounce 能否实现" | 先说业务问题 + 约束，让 AI 推荐方案 |
| 验证 vs 实现边界模糊 | 验证阶段问"怎么改"，实现阶段还在问"是不是这里有问题" | 明确说"帮我验证假设（不改代码）"或"现在帮我改" |

---

## 协作问题五模式

| 模式 | 表现 | 检测信号 |
|------|------|---------|
| 大任务一次性塞入一个会话 | 把完整任务当一个会话，打断后全部重来 | `Request interrupted` 频率 ≥ 50% |
| 不记录中间状态，打断后无法续上 | 新会话从头读代码，没有交接信息 | 同一文件被重复读取 2+ 次 |
| 会话之间没有上下文传递 | 会话 A 确认了排除方案，会话 B 又从头描述 | 同项目多会话问题描述重复率 > 70% |
| 工具没有分流 | 所有任务都往 Claude Code 塞 | Cursor/Codex 缓存目录空置 |
| 没有验收标准 | 改完代码后，AI 交付即结束 | 用户提示词中无"怎样算改好了"定义 |

---

## 提示词质量四要素框架

分析用户提示词时使用：

```
问题：[现象描述，1-2句]
触发：[操作步骤 + 频率]
期望：[正常应该怎样]
已试：[已排除的或已知信息]
猜测：[可选，让AI直接验证]
```

---

## 项目结构

```
ai-tool-weekly-review/
├── src/
│   ├── __init__.py
│   ├── cli.py           # 命令行入口
│   ├── scanner.py       # .jsonl 扫描器
│   ├── analyzer.py      # 效率问题分析
│   └── reporter.py      # 报告生成 + 飞书推送
├── README.md
├── LICENSE
└── pyproject.toml
```

---

## License

MIT
