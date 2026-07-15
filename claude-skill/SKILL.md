---
name: ai-tool-weekly-review
description: |
  对 Claude Code、Cursor、Codex 的使用情况进行结构化周度复盘。分析会话文件中的任务分布、效率问题、提示词质量，给出可执行的优化建议。
  触发：weekly review、周度复盘、这一周我做了什么、哪里效率低、AI工具使用审查
---

# AI Tool Weekly Review

对 Claude Code、Cursor、Codex 的使用情况进行结构化周度复盘。

## 数据源

| 工具 | 路径 |
|------|------|
| Claude Code | `~/.claude/projects/` |
| Cursor | `~/Library/Application Support/Cursor/` |
| Codex | `~/.claude/` |

> 估算口径：数据来源为 .jsonl 会话文件，以**会话数量 + 文件大小**作为代理指标，无法精确还原使用时长。

## .jsonl 会话结构

```python
import json

for line in open('session.jsonl'):
    obj = json.loads(line.strip())
    if obj.get('type') == 'user':
        # 正确路径：content 在 obj['message']['content']，不是 obj['content']
        msg = obj.get('message', {})
        content = msg.get('content', [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '')
                    if text and 'Base directory for this skill' not in text:
                        print(text[:300])
```

`content` 数组项类型：
- `type: "text"` → 实际用户输入 ✅
- `type: "tool_result"` → 工具返回（需过滤）
- `type: "image_url"` → 图片附件

## 数据收集流程

### Step 1: 扫描 Claude Code 项目

```python
import os
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=7)
projects_dir = os.path.expanduser("~/.claude/projects/")

for item in os.listdir(projects_dir):
    item_path = os.path.join(projects_dir, item)
    if not os.path.isdir(item_path):
        continue
    # 项目名转换：-Users-favor-p-GitHub-Work-ai-daily-pulse → GitHub/Work/ai-daily-pulse
    project = item.replace('-Users-', '', 1).replace('-', '/')
    for f in os.listdir(item_path):
        if not f.endswith('.jsonl'):
            continue
        fpath = os.path.join(item_path, f)
        mtime = datetime.fromtimestamp(os.stat(fpath).st_mtime)
        if start_date <= mtime <= end_date:
            size_kb = os.stat(fpath).st_size / 1024
            # 提取用户消息、判断中断、判断 auto mode...
```

### Step 2: 判断 auto mode（凌晨时段）

```python
def likely_auto_mode(messages):
    if not messages:
        return True  # 无用户消息，极可能是 auto mode
    first = messages[0]
    if '<ide_opened_file>' in first or '<local-command' in first:
        return False  # 人工特征
    if len(first) > 100:
        return False  # 有具体业务描述
    template_keywords = ['每日', '抓取', '运行', '摘要', '定时', 'backup']
    if any(k in first for k in template_keywords):
        return True
    return False
```

## 报告结构

```
一、总览
  - 各工具活跃情况（会话数 / 总容量）
  - 估算口径说明

二、按项目分析（按会话量排序）
  - 任务摘要
  - 效率问题（打断频率、重复读取、上下文丢失）

三、思维问题与协作问题
  - 最常见的思维陷阱
  - 最常见的协作陷阱
  - 可执行的改进建议
```

## 思维问题四模式

| 模式 | 表现 | 高效路径 |
|------|------|---------|
| 先查代码、后建假设 | 发现现象 → 直接读代码 → 在代码里找原因 | 发现现象 → 描述路径 → 提出假设 → 反推验证 |
| 对问题只定性不定量 | 说"偶尔"、"有时候"，不给概率 | 给出"偶发约 1/N，连续操作 X 次以上" |
| 把技术问题和业务问题混在一起问 | 问"debounce 能否实现" | 先说业务问题 + 约束，让 AI 推荐方案 |
| 验证 vs 实现边界模糊 | 验证阶段问"怎么改" | 明确说"帮我验证假设（不改代码）"或"现在帮我改" |

## 协作问题五模式

| 模式 | 表现 | 检测信号 |
|------|------|---------|
| 大任务一次性塞入一个会话 | 打断后全部重来 | `Request interrupted` 频率 ≥ 50% |
| 不记录中间状态，打断后无法续上 | 新会话从头读代码 | 同一文件被重复读取 2+ 次 |
| 会话之间没有上下文传递 | 会话 A 确认了方案，会话 B 又从头描述 | 同项目多会话问题描述重复率 > 70% |
| 工具没有分流 | 所有任务都往 Claude Code 塞 | Cursor/Codex 缓存空置 |
| 没有验收标准 | AI 交付即结束，用户自己判断 | 提示词中无"怎样算改好了"定义 |

## 首条消息重复检测（黄金信号）

同项目多个会话的首条用户消息如果完全相同 → 典型"会话间无交接"问题：

```python
first_msgs = {}
for session in sessions:
    msgs = get_user_messages(session)
    if msgs:
        first = msgs[0][:100]
        first_msgs[first] = first_msgs.get(first, 0) + 1
repeats = {k: v for k, v in first_msgs.items() if v > 1}
```

## 飞书输出格式

默认整条发送，不要拆分。

- ✅ `**粗体标题**` + 正文
- ✅ 纯列表（每行一个 `•`）
- ⚠️ 表格（`|` 分隔，3行以内）
- ❌ 混合（表格+列表+代码块同时用）
