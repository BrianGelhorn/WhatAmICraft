#!/usr/bin/env python3
import argparse
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups/ops"
DEFAULT_KEEP = 10
EXCLUDED_BACKUP_NAMES = {".env", ".env.local", "publishing-secrets.json"}


def wanted_files(root: Path = ROOT) -> list[Path]:
    patterns = [
        ".env",
        ".env.local",
        ".dockerignore",
        "compose.yaml",
        "Dockerfile",
        "package.json",
        "package-lock.json",
        "remotion.config.ts",
        "tsconfig.json",
        "data/**/*",
        "out/*.json",
        "out/*.sqlite3",
        "src/generated/*",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(
            path for path in root.glob(pattern) if path.is_file() and path.name not in EXCLUDED_BACKUP_NAMES
        )
    return sorted(set(files))


def recent_logs(root: Path = ROOT, max_lines: int = 80) -> str:
    chunks = []
    for path in sorted((root / "out/logs").glob("**/*.log"))[-12:]:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
        chunks.append(f"## {path.relative_to(root).as_posix()}\n" + "\n".join(lines))
    return "\n\n".join(chunks) + ("\n" if chunks else "")


def backup(
    keep: int = DEFAULT_KEEP,
    quiet: bool = False,
    root: Path = ROOT,
    backup_dir: Path = BACKUP_DIR,
) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / f"state-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in wanted_files(root):
            archive.write(path, path.relative_to(root).as_posix())
        archive.writestr("out/logs-recent.txt", recent_logs(root))
    try:
        destination.chmod(0o600)
    except OSError:
        pass
    backups = sorted(backup_dir.glob("state-*.zip"), reverse=True)
    for old in backups[keep:]:
        old.unlink(missing_ok=True)
    if not quiet:
        print(f"backup: {destination}")
    return destination


def _safe_member_target(root: Path, member: zipfile.ZipInfo) -> Path:
    relative = PurePosixPath(member.filename)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise RuntimeError(f"Ruta insegura en backup: {member.filename}")
    mode = member.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise RuntimeError(f"Enlace no permitido en backup: {member.filename}")
    root = root.resolve()
    target = (root / Path(*relative.parts)).resolve()
    if root not in target.parents and target != root:
        raise RuntimeError(f"Ruta insegura en backup: {member.filename}")
    return target


def restore(source: Path, root: Path = ROOT) -> None:
    source = source.resolve()
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            target = _safe_member_target(root, member)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not member.is_dir():
                with archive.open(member) as src, target.open("wb") as dst:
                    dst.write(src.read())
    print(f"restore: {source}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup/restore del estado critico sin duplicar videos")
    parser.add_argument("--restore", type=Path, help="Restaura un zip creado por este script")
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP, help="Cantidad de backups a conservar")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.restore:
        restore(args.restore)
    else:
        backup(max(args.keep, 1), args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
