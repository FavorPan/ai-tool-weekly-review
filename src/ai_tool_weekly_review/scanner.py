"""Claude Code .jsonl scanner."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class SessionInfo:
    path: Path
    project: str
    size_kb: float
    mtime: datetime
    user_messages: list[str] = field(default_factory=list)
    interrupted: bool = False
    likely_auto_mode: bool = False

    @property
    def first_message_preview(self) -> str:
        return self.user_messages[0][:100] if self.user_messages else ""


def path_to_project(name: str) -> str:
    """Convert Claude Code project dir name to readable path."""
    # e.g. -Users-favor-p-GitHub-Work-ai-daily-pulse → GitHub/Work/ai-daily-pulse
    if name.startswith("-Users-"):
        name = name.replace("-Users-", "", 1)
    return name.replace("-", "/")


def get_user_messages(path: Path) -> list[str]:
    """Extract user message texts from a .jsonl session file."""
    msgs: list[str] = []
    try:
        with open(path) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                if obj.get("type") != "user":
                    continue

                msg = obj.get("message", {})
                content = msg.get("content", [])

                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            txt = item.get("text", "")
                            # Filter IDE notifications and local-command
                            if txt and "Base directory for this skill" not in txt:
                                msgs.append(txt)
                elif isinstance(content, str) and content.strip():
                    msgs.append(content.strip())
    except (OSError, IOError):
        pass
    return msgs


def detect_interrupted(path: Path) -> bool:
    """Check if a session was interrupted."""
    try:
        with open(path) as f:
            content = f.read()
            return "Request interrupted" in content or "Permission for this action was denied" in content
    except (OSError, IOError):
        return False


def detect_auto_mode(messages: list[str]) -> bool:
    """Guess if a session was auto mode (no real user input)."""
    if not messages:
        return True

    first = messages[0]
    # Manual: has IDE file open or local command
    if "<ide_opened_file>" in first or "<local-command" in first:
        return False

    # Manual: has real business description
    if len(first) > 100:
        return False

    # Template keywords → likely auto mode
    template_keywords = ["每日", "抓取", "运行", "摘要", "定时", "backup"]
    if any(k in first for k in template_keywords):
        return True

    return False  # can't tell, assume manual


def scan_claude_projects(
    start_date: datetime,
    end_date: datetime,
    claude_projects_dir: Path | None = None,
) -> list[SessionInfo]:
    """Scan Claude Code projects and return sessions within the date range."""
    if claude_projects_dir is None:
        claude_projects_dir = Path.home() / ".claude" / "projects"

    if not claude_projects_dir.exists():
        return []

    sessions: list[SessionInfo] = []

    for item in claude_projects_dir.iterdir():
        if not item.is_dir():
            continue

        project = path_to_project(item.name)

        for f in item.iterdir():
            if not f.suffix == ".jsonl":
                continue

            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if not (start_date <= mtime <= end_date):
                continue

            # Skip subagent folders
            if f.stem.count("-") > 3:
                continue

            size_kb = f.stat().st_size / 1024
            msgs = get_user_messages(f)
            interrupted = detect_interrupted(f)
            auto_mode = detect_auto_mode(msgs)

            sessions.append(
                SessionInfo(
                    path=f,
                    project=project,
                    size_kb=size_kb,
                    mtime=mtime,
                    user_messages=msgs,
                    interrupted=interrupted,
                    likely_auto_mode=auto_mode,
                )
            )

    return sessions


def scan_recent_days(days: int = 7, claude_projects_dir: Path | None = None) -> list[SessionInfo]:
    """Convenience: scan sessions from the last N days."""
    end = datetime.now()
    start = end - timedelta(days=days)
    return scan_claude_projects(start, end, claude_projects_dir)
