#!/usr/bin/env python3
"""Offline static security check for agent skills. Read-only: never executes
the skill under audit and makes no network calls.

Usage:
    python3 audit.py /path/to/skill-dir

Exit codes: 0 = no findings, 1 = caution or critical findings.
Prints a findings table with severity, file:line, and detail.

The scanner is intentionally loud: pattern hits are leads, not verdicts.
Quoted examples in documentation (e.g. this repo's references/patterns.md)
will trigger hits. Every hit needs human context before it becomes a finding.
"""
import json
import os
import re
import sys

# (severity, compiled pattern, detail)
SKILL_MD_PATTERNS = [
    ("critical", r"ignore (all )?previous instructions", "Instruction override attempt"),
    ("critical", r"disregard (the|your|these) (rules|instructions|policies)", "Instruction override attempt"),
    ("critical", r"do not (mention|report|disclose)", "Suppression instruction"),
    ("critical", r"mark (this|it) as safe", "Self-clearing meta-instruction"),
    ("critical", r"skip the audit", "Audit-evasion meta-instruction"),
    ("critical", r"\bANTHROPIC_API_KEY\b|\bOPENAI_API_KEY\b", "References an API key in instructions"),
    ("caution", r"https?://[^\s)]+", "External URL in instructions (verify it is not a runtime instruction fetch)"),
]

SCRIPT_PATTERNS = [
    ("critical", r"curl[^\n]*\|\s*(ba)?sh", "Download-and-execute pipe"),
    ("critical", r"wget[^\n]*\|\s*(ba)?sh", "Download-and-execute pipe"),
    ("critical", r"base64[^|\n]*-d[^|\n]*\|\s*(ba)?sh", "Decode-and-execute"),
    ("critical", r"eval\(\s*base64", "Obfuscated eval"),
    ("critical", r"~\/\.(ssh|aws|gnupg)\/", "Reads sensitive credential directory"),
    ("critical", r"(os\.environ|process\.env)[^\n]*(TOKEN|SECRET|PASSWORD)", "Reads credential env vars"),
    ("caution", r"curl |wget ", "Network fetch in script (check destination)"),
    ("caution", r"crontab|LaunchAgents|systemd", "Persistence mechanism"),
    ("caution", r">>.*(\.bashrc|\.zshrc|profile)", "Shell profile modification"),
    ("caution", r"chmod\s+\+x", "Makes a file executable"),
]

HOOKS = {"preinstall", "install", "postinstall", "prepublish", "prepare"}

TEXT_EXTS = {".md", ".txt", ".sh", ".py", ".js", ".ts", ".json", ".yaml", ".yml"}


def scan_file(root, rel, patterns):
    findings = []
    path = os.path.join(root, rel)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                for sev, pat, detail in patterns:
                    if re.search(pat, line, re.IGNORECASE):
                        findings.append((sev, f"{rel}:{i}", detail))
                        break
    except OSError as e:
        findings.append(("caution", rel, f"Could not read file: {e}"))
    return findings


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 audit.py /path/to/skill-dir", file=sys.stderr)
        sys.exit(2)
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"Not a directory: {root}", file=sys.stderr)
        sys.exit(2)

    findings = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            _, ext = os.path.splitext(fn)
            if ext.lower() not in TEXT_EXTS and fn != "SKILL.md":
                continue
            if fn == "SKILL.md":
                findings += scan_file(root, rel, SKILL_MD_PATTERNS)
            else:
                findings += scan_file(root, rel, SCRIPT_PATTERNS)

    pkg = os.path.join(root, "package.json")
    if os.path.isfile(pkg):
        try:
            with open(pkg) as f:
                scripts = json.load(f).get("scripts", {})
            for hook in HOOKS & set(scripts):
                findings.append(("critical", f"package.json:{hook}", f"Lifecycle hook '{hook}' runs at install time"))
        except (OSError, json.JSONDecodeError) as e:
            findings.append(("caution", "package.json", f"Could not parse: {e}"))

    if not findings:
        print("No findings. Static pass is clean (absence of hits is not proof of safety).")
        sys.exit(0)

    worst = "caution" if all(f[0] == "caution" for f in findings) else "critical"
    print(f"{'SEVERITY':<10} {'LOCATION':<50} DETAIL")
    for sev, loc, detail in findings:
        print(f"{sev:<10} {loc:<50} {detail}")
    print(f"\n{len(findings)} finding(s). Worst severity: {worst}.")
    sys.exit(1)


if __name__ == "__main__":
    main()
