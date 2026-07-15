"""CLI entry point for ai-tool-weekly-review."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta

from .analyzer import analyze_sessions
from .reporter import generate_report, send_to_feishu
from .scanner import scan_recent_days, scan_claude_projects


def main() -> int:
    parser = argparse.ArgumentParser(description="AI coding tool weekly review")
    parser.add_argument("--days", type=int, default=7, help="Scan last N days (default: 7)")
    parser.add_argument(
        "--start", type=str, default=None, help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end", type=str, default=None, help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Write report to file"
    )
    parser.add_argument(
        "--feishu", action="store_true", help="Send report to Feishu webhook"
    )
    parser.add_argument(
        "--feishu-url", type=str, default=None, help="Feishu webhook URL (overrides env)"
    )
    args = parser.parse_args()

    # Parse date range
    if args.start and args.end:
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
            end_date = datetime.strptime(args.end, "%Y-%m-%d")
        except ValueError:
            print("❌ 日期格式错误，请使用 YYYY-MM-DD")
            return 1
    elif args.start or args.end:
        print("❌ 需要同时指定 --start 和 --end")
        return 1
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"🔍 扫描 {start_str} ~ {end_str} 的会话数据...")

    # Scan
    sessions = scan_claude_projects(start_date, end_date)
    if not sessions:
        print("⚠️  未找到任何会话数据，检查日期范围或 Claude Code 路径是否正确")
        return 0

    print(f"✅ 找到 {len(sessions)} 个会话，总计 {sum(s.size_kb for s in sessions):.0f} KB")

    # Analyze
    result = analyze_sessions(sessions)

    # Generate report
    report = generate_report(result, start_str, end_str)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"📄 报告已保存到 {args.output}")
    else:
        print("")
        print(report)

    # Feishu
    if args.feishu:
        webhook = args.feishu_url or os.environ.get("FEISHU_WEBHOOK", "")
        if webhook:
            ok = send_to_feishu(webhook, report)
            if ok:
                print("✅ 报告已发送到飞书")
            else:
                print("❌ 飞书推送失败")
                return 1
        else:
            print("⚠️  未设置 FEISHU_WEBHOOK，跳过飞书推送")

    return 0


if __name__ == "__main__":
    sys.exit(main())
