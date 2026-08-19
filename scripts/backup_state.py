#!/usr/bin/env python3
import argparse
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups/ops"
DEFAULT_KEEP = 10


def wanted_files() -> list[Path]:
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
        files.extend(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(set(files))


def recent_logs(max_lines: int = 80) -> str:
    chunks = []
    for path in sorted((ROOT / "out/logs").glob("**/*.log"))[-12:]:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
        chunks.append(f"## {path.relative_to(ROOT).as_posix()}\n" + "\n".join(lines))
    return "\n\n".join(chunks) + ("\n" if chunks else "")


def backup(keep: int, quiet: bool = False) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destination = BACKUP_DIR / f"state-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in wanted_files():
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("out/logs-recent.txt", recent_logs())
    try:
        destination.chmod(0o600)
    except OSError:
        pass
    backups = sorted(BACKUP_DIR.glob("state-*.zip"), reverse=True)
    for old in backups[keep:]:
        old.unlink(missing_ok=True)
    if not quiet:
        print(f"backup: {destination}")
    return destination


def restore(source: Path) -> None:
    source = source.resolve()
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            target = (ROOT / member.filename).resolve()
            if ROOT.resolve() not in target.parents and target != ROOT.resolve():
                raise RuntimeError(f"Ruta insegura en backup: {member.filename}")
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
