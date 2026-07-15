---
name: ai-tool-weekly-review
description: |
  对 Claude Code、Cursor、Codex 的使用情况进行结构化周度复盘。分析会话文件中的任务分布、效率问题、提示词质量，给出可执行的优化建议。
  触发词："复盘"、"周度报告"、"使用分析"、"weekly review"、"AI工具使用审查"
category: autonomous-ai-agents
tags: [claude-code, cursor, codex, review, analysis, weekly]
---

## 何时使用

- 用户要求对 Claude Code/Cursor/Codex 的使用情况做周度复盘
- 用户问"这一周我做了哪些事"、"用了多久"、"哪里效率低"
- 用户想了解自己在 AI 协作中的常见问题

## 数据源路径

**主数据源（Hermes 会话记录）** — 当 Claude Code/Cursor/Codex 不活跃时，Hermes 自身的会话记录是唯一可靠的数据源：

```
session_search(sort="newest")  ← Hermes 会话数据库（FTS5 全文检索）
session_search(query="关键词", sort="newest")  ← 按项目关键词搜索
```

**Claude Code .jsonl 消息结构（实测 2026-07）**

用户消息的正确提取路径（重要：旧版代码用 `obj['content']` 是错的）：

```python
# 正确：content 在 obj['message']['content'] 里，不是 obj['content']
for line in open('session.jsonl'):
    obj = json.loads(line.strip())
    if obj.get('type') == 'user':
        msg = obj.get('message', {})
        role = msg.get('role', '?')
        content = msg.get('content', [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '')
                    if text and 'Base directory for this skill' not in text:
                        print(text[:300])
        elif isinstance(content, str):
            print(content[:300])
```

注意：`obj['content']` 是 None，不要用。要用 `obj['message']['content']`。

**辅助数据源（AI 编程工具）**：

```
~/.claude/projects/           ← Claude Code 会话文件（.jsonl）
~/Library/Application Support/Cursor/  ← Cursor 缓存
~/.claude/                    ← Codex（如果有）
```

### 数据源优先级

1. **先用 `session_search` 浏览 Hermes 会话** — 获取本周所有人工会话
2. **再扫描 Claude Code .jsonl** — 仅扫描修改时间在范围内的文件，提取项目名和任务摘要
3. **最后检查 Cursor/Codex** — 确认是否完全空置

**当 Claude Code/Cursor/Codex 全部空置时**：报告仍然正常生成，以 Hermes 会话为唯一数据源。

## 数据收集流程

### Step 1: 浏览 Hermes 会话（主数据源）

```python
session_search(sort="newest", limit=30)
session_search(query="项目关键词", sort="newest")
```

从结果中筛选：
- `source: "tui"` → 人工会话，计入统计
- `source: "cron"` → 自动化任务，不计入人工统计，单独注明
- `source: "feishu"` → 飞书触发的简短问答，计入统计但标注

### Step 2: 扫描 Claude Code .jsonl（辅助数据源）

```python
import os
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=7)
claude_projects = os.path.expanduser("~/.claude/projects/")

for item in os.listdir(claude_projects):
    item_path = os.path.join(claude_projects, item)
    if os.path.isdir(item_path):
        for f in os.listdir(item_path):
            if f.endswith('.jsonl'):
                fstat = os.stat(os.path.join(item_path, f))
                if datetime.fromtimestamp(fstat.st_mtime) >= start_date:
                    # 在范围内，深入分析
```

### 估算口径

> "数据来源为 .jsonl 会话文件，无法精确还原使用时长，本报告以会话数量+文件大小作为代理指标。"

## 报告结构

```
一、总览
  - 估算口径说明
  - 活跃工具 + 项目分布表（会话数 / 总容量 / 日期范围）
  - 缓存和产物概况

二、按项目分析（按会话量排序）
  - 做了什么（从 user message 提取任务）
  - 花了多久（文件大小代理指标 + 会话数量）
  - 效率问题（打断频率、重复读取、上下文丢失）
  - 提示词质量审查

三、思维问题与优化建议
  - 最常见的思维问题（归因到具体模式）
  - 最常见的协作问题
  - 可执行的改进建议
```

## 思维问题四模式（报告重点分析项）

① **先查代码、后建假设**
现状：发现现象 → 直接读代码 → 在代码里找原因 → 陷入"读了很多代码但找不到问题"
高效路径：发现现象 → 描述用户路径 → 提出假设 → 用假设反推验证方向

② **对问题只定性不定量**
现状：说"偶尔"、"偶然"、"有时候"，不给概率和触发条件
高效路径：给出"偶发约 1/N，连续操作 X 次以上时出现"

③ **把技术问题和业务问题混在一起问**
现状：问"debounce 能否实现"（技术方案），而非"如何防止重复点击重复请求"（业务问题）
高效路径：先说业务问题 + 约束，让 AI 推荐方案

④ **验证 vs 实现边界模糊**
现状：验证阶段问"怎么改"，或实现阶段还在问"是不是这里有问题"
高效路径：明确说"帮我验证假设（不改代码）"或"假设确认了，现在帮我改"

## 协作问题五模式（报告重点分析项）

① **大任务一次性塞入一个会话**
关键数据：检查 `Request interrupted` 频率，占总会话数 ≥50% 需警示

② **不记录中间状态，打断后无法续上**
关键识别：同一文件被重复读取 2+ 次 → 缺少交接记录

③ **会话之间没有上下文传递**
关键识别：同项目多会话中问题描述重复率 >70%

④ **工具没有分流**
关键数据：Cursor 缓存目录有无可用会话，Codex 有无缓存记录

⑤ **没有验收标准**
关键识别：用户提示词中无"怎样算改好了"定义

## 提示词质量四要素框架

```
问题：[现象描述，1-2句]
触发：[操作步骤 + 频率]
期望：[正常应该怎样]
已试：[已排除的或已知信息]
猜测：[可选，让AI直接验证]
```

## 工具选择建议

| 场景 | 推荐工具 |
|------|---------|
| 排查偶发 bug、跨文件逻辑追踪 | Claude Code（长上下文） |
| 边写代码边问细节 | Cursor Chat |
| 一次性轻量代码生成 | Codex |
| 重复性自动化任务 | Cron + Claude Code |
| 需要并行两个独立任务 | 多个会话同时跑，不串行 |

## 飞书输出格式

**默认：整条报告作为一条消息发出**。分块仅作备选（用户反馈格式异常时用）。

格式示范：

```
📊 **AI 编程工具周度复盘**
覆盖：2026-05-19 ~ 2026-05-26
估算口径：...

---

**各工具活跃情况**
✅ Claude Code — 主力使用... | ❌ Cursor — 本周未使用 | ❌ Codex — 本周未使用

---

**按项目分析**
🔴 **项目名**（05-19~05-21）
做了：[...] 问题：[...]
🟡 **效率问题**
• 重复读取同一文件（3次相同描述）
• 被中断频率高（4/8个会话以 Request interrupted 结束）
```

飞书 Markdown 可靠渲染规则：
- ✅ `**粗体标题**` + 正文
- ✅ 纯列表（每行一个 `•`）
- ⚠️ 表格（`|` 分隔，3行以内）
- ❌ 混合（表格+列表+代码块同时用）

## References

- `references/session-analysis.md` — 会话文件结构解析、效率问题判断标准
- `references/patterns.md` — 思维问题/协作问题的详细定义和检测方法
