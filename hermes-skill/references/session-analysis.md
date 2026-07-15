# Claude Code 会话分析方法

## 目录结构

```
~/.claude/projects/
  └── -Users-favor-p-GitHub-Work-<project>/
        ├── <session-uuid>.jsonl     # 主会话
        └── <session-uuid>/          # subagent 子会话
              └── subagents/
                    └── agent-<hash>.jsonl
```

项目目录名用 `-` 分隔路径：`item.replace('-Users-favor-p-', '').replace('-', '/')` 得到 `GitHub/Work/ai/daily/pulse`。

## Claude Code .jsonl 消息结构（实测 2026-07）

**正确提取用户消息的方式：**

```python
import json

def get_user_msgs(path):
    """提取用户消息文本，过滤工具返回和 IDE 通知"""
    msgs = []
    with open(path) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get('type') != 'user':
                continue
            msg = obj.get('message', {})
            content = msg.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        txt = item.get('text', '')
                        if txt and 'Base directory for this skill' not in txt:
                            msgs.append(txt)
            elif isinstance(content, str) and content.strip():
                msgs.append(content.strip())
    return msgs
```

**常见 `content` 数组项类型：**
- `type: "text"` → 实际用户输入 ✅
- `type: "tool_result"` → 工具返回（也以 `type: user` 出现，需过滤）
- `type: "image_url"` → 图片附件

**注意：`obj['content']` 是 None，不要用。** 正确路径是 `obj['message']['content']`。

## 效率问题判断标准

### 会话碎片化
- 同一项目 7 天内有 5+ 个会话
- 或 3+ 个会话都以 `Request interrupted` 结束
- 或相邻两个会话间隔 < 30 分钟（说明被打断后重开）

### 上下文丢失
- 新会话中再次出现"读同一文件"或"重复问同一问题"
- 检查方式：提取所有 `user` 消息，对比内容相似度

### 中断检测

**方式 1：搜索 "Request interrupted" 字符串**
```bash
grep -c "Request interrupted" session.jsonl
```

**方式 2：检查 `permissionMode` 拒绝**
```bash
grep -c "Permission for this action was denied" session.jsonl
```

**方式 3：会话大小代理判断**
- 会话 >500KB 且只有 1 条 user message → 疑似单次大任务被中断后重开
- 会话 >1.5MB → 高风险：打断一次损失巨大

### 重复文件读取检测

```bash
grep -o '"file_path":"[^"]*"' session.jsonl | sort | uniq -c | sort -rn
```
同一文件出现 2+ 次 → 标记为重复读取。

## 凌晨会话与 Auto Mode 区分

Claude Code 有 auto mode，凌晨时段（00:00-06:00）的会话不一定是人工。

**判断逻辑：**

```python
def likely_auto_mode(path):
    """判断一个会话是否可能是 Claude Code auto mode 自动运行"""
    msgs = get_user_msgs(path)
    if not msgs:
        return True  # 无用户消息，极可能是 auto mode

    first = msgs[0]
    if '<ide_opened_file>' in first or '<local-command' in first:
        return False  # 人工特征

    if len(first) > 100:
        return False  # 有具体的业务描述

    template_keywords = ['每日', '抓取', '运行', '摘要', '定时', 'backup']
    if any(k in first for k in template_keywords):
        return True

    return None  # 无法判断
```

在总览中，凌晨时段且判断为 auto mode 的会话不计入"纯人工"使用统计，单独注明为 `⚠️ 疑似 auto mode`。

## 首条消息重复检测（会话间无交接的黄金信号）

比对同项目所有会话的 `first user message`，如果 2+ 个会话首条完全相同 → 典型"会话间无交接"问题。

```python
first_msgs = {}
for session in sessions:
    msgs = get_user_msgs(session)
    if msgs:
        first = msgs[0][:100]  # 取前100字符比
        first_msgs[first] = first_msgs.get(first, 0) + 1
repeats = {k: v for k, v in first_msgs.items() if v > 1}
```

## 常见陷阱

1. **`obj['content']` 是 None** — 旧代码或 AI 生成的代码示例常用这个路径，是错的。要用 `obj['message']['content']`。
2. **`find -newer` 日期过滤不可靠** — macOS 对日期字符串支持不稳定。改用 `ls -lh` 列出所有文件后手动按 mtime 筛选。
3. **凌晨时段会话需人工判断** — Claude Code auto mode 可能自动运行，不代表用户主动操作。
4. **subagent 会话独立计算** — subagent 的 mtime 可能晚于主会话（异步完成），统计时单独计入。
5. **`execute_code` 和 `python3 -c` 在 cron 模式下都被阻止** — 唯一可行的方法：用 `write_file` 将 Python 脚本写到 `/tmp/`，然后用 `terminal` 执行 `python3 /tmp/script.py`。
