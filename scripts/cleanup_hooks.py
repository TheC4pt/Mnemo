#!/usr/bin/env python3
"""Script to uninstall all Mnemo hooks while keeping the memory database (.mnemo/)."""

import sys
import json
import shutil
from pathlib import Path

def cleanup_hooks(repo_path: Path):
    repo_root = repo_path.resolve()
    print(f"[*] Cleaning up Mnemo hooks in: {repo_root}")

    # 1. Clean up git hooks
    git_hooks_dir = repo_root / ".git" / "hooks"
    if git_hooks_dir.exists():
        pre_commit_hook = git_hooks_dir / "pre-commit"
        if pre_commit_hook.exists():
            try:
                content = pre_commit_hook.read_text(encoding="utf-8")
                # If it's the default mnemo-only hook script, delete it.
                # Otherwise, remove the mnemo check line.
                if "Mnemo pre-commit hook" in content or content.strip() == '#/bin/sh\n# Mnemo validation\nmnemo check':
                    pre_commit_hook.unlink()
                    print("  [+] Removed Mnemo pre-commit hook file")
                elif "mnemo check" in content:
                    lines = [line for line in content.splitlines() if "mnemo check" not in line and "# Mnemo validation" not in line]
                    pre_commit_hook.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    print("  [+] Removed Mnemo check from existing pre-commit hook")
            except Exception as e:
                print(f"  [-] Failed to clean up git pre-commit hook: {e}")

    # 2. Remove Mnemo-generated Kiro files
    mnemo_kiro_files = [
        repo_root / ".kiro" / "hooks" / "agent-spawn.sh",
        repo_root / ".kiro" / "hooks" / "user-prompt-submit.sh",
        repo_root / ".kiro" / "hooks" / "pre-tool-use.sh",
        repo_root / ".kiro" / "hooks" / "post-tool-use.sh",
        repo_root / ".kiro" / "hooks" / "stop.sh",
        repo_root / ".kiro" / "agents" / "mnemo-enhanced.json",
        repo_root / ".kiro" / "skills" / "mnemo" / "SKILL.md",
        repo_root / ".kiro" / "settings" / "mcp.json",
    ]
    for f in mnemo_kiro_files:
        if f.exists():
            try:
                f.unlink()
                print(f"  [+] Removed {f.relative_to(repo_root)}")
            except Exception as e:
                print(f"  [-] Failed to remove Kiro file {f}: {e}")

    # Clean up empty Kiro directories left behind
    for d in [
        repo_root / ".kiro" / "skills" / "mnemo",
        repo_root / ".kiro" / "hooks",
        repo_root / ".kiro" / "agents",
        repo_root / ".kiro" / "skills",
        repo_root / ".kiro" / "settings",
    ]:
        if d.exists() and not any(d.iterdir()):
            try:
                d.rmdir()
            except Exception:
                pass

    # 3. Clean up Claude settings.json
    claude_settings = repo_root / ".claude" / "settings.json"
    if claude_settings.exists():
        try:
            data = json.loads(claude_settings.read_text(encoding="utf-8"))
            changed = False
            if "hooks" in data:
                del data["hooks"]
                changed = True
            if "mcpServers" in data and "mnemo" in data["mcpServers"]:
                del data["mcpServers"]["mnemo"]
                if not data["mcpServers"]:
                    del data["mcpServers"]
                changed = True
            if changed:
                claude_settings.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print("  [+] Removed Mnemo hooks/MCP from .claude/settings.json")
        except Exception as e:
            print(f"  [-] Failed to clean up .claude/settings.json: {e}")

    # Remove Mnemo section from CLAUDE.md
    claude_md = repo_root / "CLAUDE.md"
    if claude_md.exists():
        try:
            content = claude_md.read_text(encoding="utf-8")
            marker = "## Mnemo — Persistent Memory"
            if marker in content:
                before = content.split(marker)[0].rstrip()
                if before:
                    claude_md.write_text(before + "\n", encoding="utf-8")
                else:
                    claude_md.unlink()
                print("  [+] Removed Mnemo section from CLAUDE.md")
        except Exception as e:
            print(f"  [-] Failed to clean up CLAUDE.md: {e}")

    # 4. Clean up Antigravity schemas in home directory
    mcp_dir = Path.home() / ".gemini" / "antigravity" / "mcp" / "mnemo"
    if mcp_dir.exists():
        try:
            shutil.rmtree(mcp_dir)
            print("  [+] Removed Antigravity MCP schemas")
        except Exception as e:
            print(f"  [-] Failed to remove Antigravity MCP directory: {e}")

    print("\n[+] Hook cleanup complete! Stored memory database (.mnemo/) remains untouched.")

if __name__ == "__main__":
    path = Path(".") if len(sys.argv) < 2 else Path(sys.argv[1])
    cleanup_hooks(path)
