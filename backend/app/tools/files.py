import os
from pathlib import Path

# Sandbox: only allow reads inside this directory
_ALLOWED_ROOT = Path(os.getenv("FILES_ROOT", str(Path.home()))).resolve()


def _safe_path(relative: str) -> Path | None:
    target = (_ALLOWED_ROOT / relative).resolve()
    if _ALLOWED_ROOT in target.parents or target == _ALLOWED_ROOT:
        return target
    return None


def read_file(path: str) -> str:
    """Read a file from the allowed root directory."""
    safe = _safe_path(path)
    if safe is None:
        return f"Access denied: '{path}' is outside the allowed directory."
    if not safe.exists():
        return f"File not found: {path}"
    if safe.is_dir():
        children = [p.name for p in safe.iterdir()]
        return f"'{path}' is a directory. Contents: {children}"
    content = safe.read_text(errors="replace")
    if len(content) > 8000:
        content = content[:8000] + "\n\n[...truncated]"
    return content


def list_files(path: str = ".") -> str:
    """List files in a directory under the allowed root."""
    safe = _safe_path(path)
    if safe is None:
        return f"Access denied: '{path}' is outside the allowed directory."
    if not safe.exists():
        return f"Directory not found: {path}"
    if not safe.is_dir():
        return f"'{path}' is a file, not a directory."
    items = sorted(safe.iterdir(), key=lambda p: (p.is_file(), p.name))
    lines = [f"{'📁' if p.is_dir() else '📄'} {p.name}" for p in items[:50]]
    return "\n".join(lines) or "(empty directory)"
