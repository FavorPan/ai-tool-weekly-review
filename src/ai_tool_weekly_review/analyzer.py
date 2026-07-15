"""Analyze session data for efficiency patterns."""

from __future__ import annotations

from collections import defaultdict

from .scanner import SessionInfo, detect_interrupted


def analyze_sessions(sessions: list[SessionInfo]) -> dict:
    """Run all analysis checks on a list of sessions."""

    # ── 1. Overview ────────────────────────────────────────────────
    total = len(sessions)
    manual = [s for s in sessions if not s.likely_auto_mode]
    auto_mode = [s for s in sessions if s.likely_auto_mode]
    interrupted = [s for s in sessions if s.interrupted]
    total_size_kb = sum(s.size_kb for s in sessions)

    # ── 2. Per-project aggregation ─────────────────────────────────
    project_map: dict[str, list[SessionInfo]] = defaultdict(list)
    for s in sessions:
        project_map[s.project].append(s)

    project_stats = []
    for project, ss in sorted(project_map.items(), key=lambda x: -len(x[1])):
        manual_ss = [s for s in ss if not s.likely_auto_mode]
        project_stats.append(
            {
                "name": project,
                "total_sessions": len(ss),
                "manual_sessions": len(manual_ss),
                "auto_mode_sessions": len(ss) - len(manual_ss),
                "total_size_kb": sum(s.size_kb for s in ss),
                "interrupted_sessions": sum(1 for s in ss if s.interrupted),
                "sessions": ss,
            }
        )

    # ── 3. Repeated first-message (no handover signal) ─────────────
    first_msg_map: dict[str, list[SessionInfo]] = defaultdict(list)
    for s in manual:
        if s.user_messages:
            key = s.user_messages[0][:100]
            first_msg_map[key].append(s)

    repeated_first = {k: ss for k, ss in first_msg_map.items() if len(ss) > 1}

    # ── 4. Large-session risk ───────────────────────────────────────
    large_risk = [s for s in sessions if s.size_kb > 1500 and s.interrupted]

    # ── 5. Interruption rate ────────────────────────────────────────
    interrupt_rate = len(interrupted) / total * 100 if total else 0

    # ── 6. Tool usage (Claude Code = only supported right now) ──────
    tool_usage = {
        "claude_code": len(sessions),
        "cursor": 0,  # Cursor analysis not yet implemented
        "codex": 0,
    }

    # ── 7. Thinking patterns (heuristic flags) ──────────────────────
    thinking_flags = _analyze_thinking_patterns(sessions)
    collaboration_flags = _analyze_collaboration_patterns(sessions, repeated_first, interrupt_rate)

    return {
        "total_sessions": total,
        "manual_sessions": len(manual),
        "auto_mode_sessions": len(auto_mode),
        "interrupted_sessions": len(interrupted),
        "interrupt_rate_pct": round(interrupt_rate, 1),
        "total_size_kb": round(total_size_kb, 1),
        "project_stats": project_stats,
        "repeated_first": repeated_first,
        "large_risk_sessions": large_risk,
        "tool_usage": tool_usage,
        "thinking_flags": thinking_flags,
        "collaboration_flags": collaboration_flags,
    }


def _analyze_thinking_patterns(sessions: list[SessionInfo]) -> list[dict]:
    """Heuristics for common thinking pitfalls."""
    flags: list[dict] = []
    all_text = " ".join(" ".join(s.user_messages) for s in sessions)

    # Pattern 1: "先查代码、后建假设" — lots of file paths but no hypothesis
    if "read_file" in all_text or "读取" in all_text:
        if not any(k in all_text for k in ["可能", "估计", "应该是", "猜测", "怀疑"]):
            flags.append(
                {
                    "pattern": "先查代码、后建假设",
                    "description": "描述了很多现象但没有提出猜测，让 AI 在代码里找原因",
                    "severity": "medium",
                }
            )

    # Pattern 2: "对问题只定性不定量" — vague frequency words
    vague_words = ["偶尔", "有时候", "经常", "总是", "一直"]
    vague_count = sum(all_text.count(w) for w in vague_words)
    if vague_count >= 3:
        flags.append(
            {
                "pattern": "对问题只定性不定量",
                "description": f"检测到 {vague_count} 次模糊描述（偶尔/有时候等），建议给出具体概率和触发条件",
                "severity": "low",
            }
        )

    return flags


def _analyze_collaboration_patterns(
    sessions: list[SessionInfo],
    repeated_first: dict[str, list[SessionInfo]],
    interrupt_rate: float,
) -> list[dict]:
    """Heuristics for common collaboration pitfalls."""
    flags: list[dict] = []

    # Pattern 1: High interruption rate
    if interrupt_rate >= 30:
        flags.append(
            {
                "pattern": "会话频繁被打断",
                "description": f"中断率 {interrupt_rate:.0f}%（≥30% 为警戒线），大任务被拆散，上下文损失严重",
                "severity": "high",
            }
        )

    # Pattern 2: Repeated first messages across sessions (no handover)
    for key, ss in repeated_first.items():
        flags.append(
            {
                "pattern": "同任务重复开新会话",
                "description": f"「{key[:60]}...」重复出现在 {len(ss)} 个会话，每次都重新描述，无交接记录",
                "severity": "high",
                "count": len(ss),
            }
        )

    # Pattern 3: Large session with interruption
    for s in sessions:
        if s.size_kb > 1500 and s.interrupted:
            flags.append(
                {
                    "pattern": "超大单会话风险",
                    "description": f"会话 {s.path.name} 大小 {s.size_kb:.0f}KB 且被打断，上下文损失巨大",
                    "severity": "high",
                }
            )

    return flags
