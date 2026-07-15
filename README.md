# AI Tool Weekly Review

对 Claude Code、Cursor、Codex 的使用情况进行结构化周度复盘。分析会话文件中的任务分布、效率问题、提示词质量，给出可执行的优化建议。

**核心功能：**
- 自动扫描 Claude Code `.jsonl` 会话文件
- 按项目聚类分析任务量和效率
- 检测会话碎片化、上下文丢失、中断频率等常见问题
- 识别"同任务重复开新会话"等协作陷阱
- 输出结构化报告，支持飞书 Webhook 推送

---

## 自动安装（推荐）

克隆后，agent 直接运行安装脚本，自动识别平台并安装：

```bash
git clone https://github.com/FavorPan/ai-tool-weekly-review.git
cd ai-tool-weekly-review
python3 install.py
```

`install.py` 会自动检测 Claude Code 和 Hermes 环境并安装对应 skill：
- **Claude Code** → `~/.claude/skills/ai-tool-weekly-review/`
- **Hermes** → `~/.hermes/skills/autonomous-ai-agents/ai-tool-weekly-review/`

也可手动指定：
```bash
python3 install.py claude-code   # 只装 Claude Code
python3 install.py hermes        # 只装 Hermes
python3 install.py both          # 两个都装
```

---

## 手动安装

### Claude Code

```bash
mkdir -p ~/.claude/skills/ai-tool-weekly-review
cp -r claude-skill/* ~/.claude/skills/ai-tool-weekly-review/
```

### Hermes

```bash
mkdir -p ~/.hermes/skills/autonomous-ai-agents/ai-tool-weekly-review
cp -r hermes-skill/* ~/.hermes/skills/autonomous-ai-agents/ai-tool-weekly-review/
```

---

## 触发词

> 复盘、周度报告、使用分析、weekly review、AI工具使用审查

---

## CLI 工具（可选安装）

如需独立的命令行分析工具：

```bash
pip install -e .
python -m ai_tool_weekly_review --days 7
python -m ai_tool_weekly_review --start 2026-07-01 --end 2026-07-14 --feishu
```

---

## 数据来源

| 工具 | 数据路径 |
|------|---------|
| Claude Code | `~/.claude/projects/` |
| Cursor | `~/Library/Application Support/Cursor/` |
| Codex | `~/.claude/` |

> 注意：数据来源为 `.jsonl` 会话文件，无法精确还原使用时长，以**会话数量 + 文件大小**作为代理指标。

---

## 报告结构

```
一、总览
  - 各工具活跃情况（会话数 / 总容量）
  - 估算口径说明

二、按项目分析（按会话量排序）
  - 任务摘要
  - 效率问题（打断频率、重复读取、上下文丢失）

三、思维问题与协作问题
  - 最常见的思维陷阱（4种）
  - 最常见的协作陷阱（5种）
  - 可执行的改进建议
```

---

## 思维问题四模式

| 模式 | 表现 | 高效路径 |
|------|------|---------|
| 先查代码、后建假设 | 发现现象 → 直接读代码 → 在代码里找原因 | 发现现象 → 描述路径 → 提出假设 → 反推验证 |
| 对问题只定性不定量 | 说"偶尔"、"有时候"，不给概率 | 给出"偶发约 1/N，连续操作 X 次以上" |
| 把技术问题和业务问题混在一起问 | 问"debounce 能否实现" | 先说业务问题 + 约束，让 AI 推荐方案 |
| 验证 vs 实现边界模糊 | 验证阶段问"怎么改" | 明确说"帮我验证假设（不改代码）"或"现在帮我改" |

---

## 协作问题五模式

| 模式 | 表现 | 检测信号 |
|------|------|---------|
| 大任务一次性塞入一个会话 | 打断后全部重来 | `Request interrupted` 频率 ≥ 50% |
| 不记录中间状态，打断后无法续上 | 新会话从头读代码 | 同一文件被重复读取 2+ 次 |
| 会话之间没有上下文传递 | 会话 A 确认了方案，会话 B 又从头描述 | 同项目多会话问题描述重复率 > 70% |
| 工具没有分流 | 所有任务都往 Claude Code 塞 | Cursor/Codex 缓存空置 |
| 没有验收标准 | AI 交付即结束，用户自己判断 | 提示词中无"怎样算改好了"定义 |

---

## 项目结构

```
ai-tool-weekly-review/
├── hermes-skill/              ← Hermes skill（YAML frontmatter + markdown）
│   ├── SKILL.md
│   └── references/
│       ├── session-analysis.md
│       └── patterns.md
├── claude-skill/              ← Claude Code skill（同格式，去掉 Hermes 特有字段）
│   └── SKILL.md
├── install.py                 ← 自动安装脚本（agent 可直接运行）
├── src/                       ← 可选 CLI 工具
│   └── ai_tool_weekly_review/
├── pyproject.toml
└── README.md
```

---

## License

MIT
