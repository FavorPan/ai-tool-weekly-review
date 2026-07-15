"""Generate reports from analysis results."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime


def generate_report(result: dict, start_date: str, end_date: str) -> str:
    """Render analysis results into a human-readable report."""

    lines = [
        f"📊 **AI 编程工具周度复盘**",
        f"覆盖：{start_date} ~ {end_date}",
        "估算口径：数据来源为 .jsonl 会话文件，以会话数量 + 文件大小作为代理指标",
        "",
        "---",
        "",
        "**一、各工具活跃情况**",
        f"✅ Claude Code — {result['manual_sessions']} 个人工会话（{result['total_size_kb']:.0f} KB）",
        f"⚠️  疑似 auto mode — {result['auto_mode_sessions']} 个（凌晨时段，可能非人工）",
        f"❌ Cursor — 本周未使用",
        f"❌ Codex — 本周未使用",
        "",
        f"中断率：{result['interrupt_rate_pct']:.1f}%（{result['interrupted_sessions']}/{result['total_sessions']} 个会话）",
        "",
        "---",
        "",
        "**二、按项目分析**",
    ]

    for proj in result["project_stats"]:
        lines.append("")
        lines.append(f"🔵 **{proj['name']}**（{proj['manual_sessions']} 个人工会话，{proj['total_size_kb']:.0f} KB）")

        if proj["interrupted_sessions"] > 0:
            lines.append(f"  • 中断：{proj['interrupted_sessions']}/{proj['total_sessions']} 个会话被打断")

        if proj["auto_mode_sessions"] > 0:
            lines.append(f"  • auto mode：{proj['auto_mode_sessions']} 个（凌晨时段）")

        if proj["sessions"]:
            msgs = [s.user_messages[0][:80] for s in proj["sessions"] if s.user_messages]
            if msgs:
                lines.append(f"  • 任务摘要：{msgs[0]}")
                if len(msgs) > 1:
                    lines.append(f"  • 另 {len(msgs) - 1} 个会话")

    # Thinking patterns
    if result["thinking_flags"]:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**三、思维问题**")
        for f in result["thinking_flags"]:
            severity_map = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            emoji = severity_map.get(f["severity"], "•")
            lines.append(f"{emoji} **{f['pattern']}**：{f['description']}")

    # Collaboration patterns
    if result["collaboration_flags"]:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**四、协作问题**")
        for f in result["collaboration_flags"]:
            severity_map = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            emoji = severity_map.get(f["severity"], "•")
            lines.append(f"{emoji} **{f['pattern']}**：{f['description']}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**五、优化建议**")
    lines.append("")
    lines.append("1. **交接记录**：每完成一个阶段，在项目目录写 `SESSION_SUMMARY.md`，记录已确认/未确认/下一步，下个会话开头先读这个文件")
    lines.append("2. **任务拆分**：大任务拆成 < 500KB 的子任务，每个会话专注一个目标，减少打断损失")
    lines.append("3. **提示词四要素**：按「问题 / 触发 / 期望 / 已试」结构描述问题，减少 AI 猜测轮次")
    lines.append("4. **定量描述**：用「连续操作 3 次以上出现」替代「偶尔/经常」，帮助 AI 制定排查策略")
    lines.append("5. **先说业务问题**：先描述业务约束和期望行为，再问技术方案，避免技术选型先于问题定义")

    lines.append("")
    lines.append(f"_生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}_")

    return "\n".join(lines)


def send_to_feishu(webhook_url: str, content: str) -> bool:
    """Send report to Feishu via webhook."""
    if not webhook_url:
        webhook_url = os.environ.get("FEISHU_WEBHOOK", "")

    if not webhook_url:
        print("❌ 未设置 FEISHU_WEBHOOK 环境变量，跳过飞书推送")
        return False

    payload = json.dumps({"msg_type": "text", "content": {"text": content}}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"❌ 飞书推送失败：{e}")
        return False
