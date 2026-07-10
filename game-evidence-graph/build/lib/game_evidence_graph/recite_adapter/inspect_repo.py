from __future__ import annotations

import subprocess
from pathlib import Path


def inspect_repo(repo_path: str | Path) -> dict:
    path = Path(repo_path)
    files = sorted(str(p.relative_to(path)) for p in path.rglob("*") if p.is_file() and ".git" not in p.parts)
    commit = "unknown"
    try:
        commit = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        pass
    license_files = [f for f in files if f.lower().startswith("license")]
    return {
        "repo_path": str(path),
        "repo_url": "local ReCITE/ReVITE reference repository",
        "commit": commit,
        "license_files": license_files,
        "python_modules": [f for f in files if f.endswith(".py")],
        "prompt_files": [f for f in files if "prompt" in f.lower() or f.endswith(".txt")],
    }
