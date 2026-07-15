#!/usr/bin/env python3
"""
ai-tool-weekly-review install script

Agent 跑一下这个脚本，自动识别平台并安装 skill：
- Claude Code:  → ~/.claude/skills/ai-tool-weekly-review/
- Hermes:       → ~/.hermes/skills/autonomous-ai-agents/ai-tool-weekly-review/
- Both:         → 两个都装
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()


def detect_platforms() -> list[str]:
    """检测当前环境支持哪些平台。"""
    platforms = []

    claude_skills_dir = Path.home() / ".claude" / "skills"
    if claude_skills_dir.exists() or (Path.home() / ".claude").exists():
        platforms.append("claude-code")

    hermes_skills_dir = Path.home() / ".hermes" / "skills"
    if hermes_skills_dir.exists() or (Path.home() / ".hermes").exists():
        platforms.append("hermes")

    # 也检查是否有对应的源目录（开发/调试用）
    if not platforms:
        # 兜底：检查环境变量
        if os.environ.get("CLAUDE_CODE"):
            platforms.append("claude-code")
        if os.environ.get("HERMES"):
            platforms.append("hermes")

    return platforms


def install_claude_code() -> bool:
    """安装到 Claude Code."""
    dest = Path.home() / ".claude" / "skills" / "ai-tool-weekly-review"
    src = REPO_ROOT / "claude-skill"

    if not src.exists():
        print(f"❌ Claude Code skill 源目录不存在：{src}")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)

    # 软链接（开发友好，更新即生效）
    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)
    else:
        dest.unlink()

    dest.symlink_to(src)
    print(f"✅ Claude Code skill 已安装：{dest} → {src}")
    return True


def install_hermes() -> bool:
    """安装到 Hermes."""
    dest = Path.home() / ".hermes" / "skills" / "autonomous-ai-agents" / "ai-tool-weekly-review"
    src = REPO_ROOT / "hermes-skill"

    if not src.exists():
        print(f"❌ Hermes skill 源目录不存在：{src}")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() or dest.is_symlink():
        existing = dest.resolve() if dest.is_symlink() else None
        if existing == src.resolve():
            print(f"✅ Hermes skill 已安装（软链接）：{dest}")
            return True
        print(f"⚠️  目标已存在，先移除：{dest}")
        if dest.is_symlink():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()

    dest.symlink_to(src)
    print(f"✅ Hermes skill 已安装：{dest} → {src}")
    return True


def main() -> int:
    print("🔍 检测平台...")
    platforms = detect_platforms()

    if not platforms:
        print("❌ 未检测到 Claude Code 或 Hermes 环境，手动指定：")
        print("   python install.py claude-code")
        print("   python install.py hermes")
        print("   python install.py both")
        return 1

    print(f"✅ 检测到平台：{', '.join(platforms)}")

    # 默认安装所有检测到的平台
    targets = sys.argv[1:] if len(sys.argv) > 1 else platforms

    ok = True
    for target in targets:
        if target == "claude-code":
            ok &= install_claude_code()
        elif target == "hermes":
            ok &= install_hermes()
        elif target == "both":
            ok &= install_claude_code()
            ok &= install_hermes()
        else:
            print(f"❌ 未知平台：{target}，跳过")

    if ok:
        print("\n🎉 安装完成！重启 agent 即可使用。")
        print("   触发词：复盘、周度报告、weekly review、AI工具使用审查")
    else:
        print("\n⚠️  部分安装失败，请检查错误信息")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
