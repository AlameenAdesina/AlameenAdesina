#!/usr/bin/env python3
"""
File Backup & Cleanup Automation (Linux)
- Discovers files by extension under --source-dirs
- Copies into date-stamped folder under --backup-dir (preserving relative paths)
- Optional deletion of old backup folders older than --retention-days (only with --delete-old)
- Dry-run by default for safety

WHY: Reduce manual toil for backups, improve auditability with logs, and enable safe, schedulable automation.

Author: You (Al-ameen Adesina)
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timedelta

# ---------- Helpers ----------

def setup_logger(log_path: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger("backup_cleanup")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG if verbose else logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console (summary-level) handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Backup files by extension from source dirs to a date-stamped folder; optional cleanup of old backups."
    )
    p.add_argument("--source-dirs", nargs="+", required=True, help="One or more source directories.")
    p.add_argument("--backup-dir", required=True, help="Backup root directory.")
    p.add_argument("--extensions", nargs="+", required=True, help="Extensions to include (e.g., .txt .log .csv).")
    p.add_argument("--retention-days", type=int, default=30, help="Retention window for old backups (days).")
    p.add_argument("--dry-run", action="store_true", help="Preview actions without performing them.")
    p.add_argument("--delete-old", action="store_true", help="Actually delete old backups older than retention-days.")
    p.add_argument("--exclude", nargs="*", default=[], help="Exclude patterns (substring match on path parts).")
    p.add_argument("--log-path", default="/var/log/backup_cleanup.log", help="Path to log file.")
    p.add_argument("--verbose", action="store_true", help="Verbose logging.")
    return p.parse_args()


def is_excluded(path: Path, excludes: list[str]) -> bool:
    parts = {str(path), path.name}
    # Also check each path component
    parts |= set(path.parts)
    for ex in excludes:
        if not ex:
            continue
        for part in parts:
            if ex in part:
                return True
    return False


def safe_relpath(file_path: Path, source_roots: list[Path]) -> Path:
    """
    Compute the relative path of file_path under the nearest matching source root.
    """
    file_path = file_path.resolve()
    for root in source_roots:
        try:
            rel = file_path.relative_to(root.resolve())
            return rel
        except ValueError:
            continue
    # Fallback: use file name only if not under any root
    return Path(file_path.name)


def approx_filehash(path: Path, block_size: int = 1024 * 1024) -> str:
    """
    Optional: compute a checksum for verification if needed.
    Not strictly required for performance-sensitive runs.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def files_equal(src: Path, dst: Path) -> bool:
    """
    Quick equality check using size and mtime.
    This avoids heavy hashing for large files under normal circumstances.
    """
    if not dst.exists():
        return False
    try:
        s1, s2 = src.stat(), dst.stat()
        return (s1.st_size == s2.st_size) and (int(s1.st_mtime) == int(s2.st_mtime))
    except OSError:
        return False


def atomic_copy(src: Path, dst: Path):
    """
    Copy file to dst using a temporary file then atomic rename, preserving mtime.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_dst = dst.with_suffix(dst.suffix + ".tmp_copy")
    shutil.copy2(src, tmp_dst)
    os.replace(tmp_dst, dst)  # atomic on same filesystem


def discover_files(sources: list[Path], exts: set[str], excludes: list[str], logger: logging.Logger):
    for root in sources:
        if not root.exists():
            logger.warning(f"Source dir missing: {root}")
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            cur_dir = Path(dirpath)
            # filter subdirs by exclude (in-place to prune traversal)
            dirnames[:] = [d for d in dirnames if not is_excluded(cur_dir / d, excludes)]
            for fn in filenames:
                path = cur_dir / fn
                if is_excluded(path, excludes):
                    continue
                if path.suffix.lower() in exts:
                    yield path


def cleanup_old_backups(backup_root: Path, retention_days: int, do_delete: bool, logger: logging.Logger) -> int:
    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = 0
    if not backup_root.exists():
        return 0
    for child in sorted(backup_root.iterdir()):
        if not child.is_dir():
            continue
        # Expect subdir format YYYYMMDD_HHMMSS
        try:
            dt = datetime.strptime(child.name, "%Y%m%d_%H%M%S")
        except ValueError:
            # Skip unknown folders
            continue
        if dt < cutoff:
            if do_delete:
                shutil.rmtree(child, ignore_errors=True)
                logger.info(f"Deleted old backup: {child}")
            else:
                logger.info(f"(Dry) Would delete old backup: {child}")
            deleted += 1
    return deleted


def main():
    args = parse_args()

    backup_root = Path(args.backup_dir)
    log_path = Path(args.log_path)
    logger = setup_logger(log_path, args.verbose)

    # Normalize inputs
    source_dirs = [Path(p).resolve() for p in args.source_dirs]
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.extensions}
    excludes = args.exclude or []

    # Validations
    for src in source_dirs:
        if not src.exists():
            logger.warning(f"Source dir does not exist: {src}")
    backup_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_root = backup_root / stamp

    # Summary counters
    discovered = 0
    copied = 0
    skipped = 0
    failed = 0
    total_bytes = 0

    logger.info("=== Backup Run Start ===")
    logger.info(f"Sources: {', '.join(map(str, source_dirs))}")
    logger.info(f"Backup root: {backup_root}")
    logger.info(f"Destination (timestamped): {dest_root}")
    logger.info(f"Extensions: {sorted(exts)}")
    logger.info(f"Excludes: {excludes}")
    logger.info(f"Retention days: {args.retention_days}")
    logger.info(f"Dry-run: {args.dry_run} | Delete-old: {args.delete_old}")

    files = list(discover_files(source_dirs, exts, excludes, logger))
    discovered = len(files)

    if not args.dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)

    for src in files:
        try:
            rel = safe_relpath(src, source_dirs)
            dst = dest_root / rel
            if args.dry_run:
                logger.info(f"(Dry) Would copy: {src} -> {dst}")
                continue

            if files_equal(src, dst):
                logger.debug(f"Skip (same size+mtime): {src}")
                skipped += 1
                continue

            atomic_copy(src, dst)
            # preserve timestamps precisely
            shutil.copystat(src, dst)
            total_bytes += src.stat().st_size
            copied += 1
            logger.debug(f"Copied: {src} -> {dst}")
        except Exception as e:
            failed += 1
            logger.error(f"Failed to copy {src}: {e}")

    # Optional cleanup
    deleted_backups = cleanup_old_backups(backup_root, args.retention_days, (args.delete_old and not args.dry_run), logger)

    # Summary
    logger.info("=== Backup Run Summary ===")
    logger.info(f"Discovered: {discovered} | Copied: {copied} | Skipped: {skipped} | Failed: {failed}")
    logger.info(f"Backups deleted: {deleted_backups}")
    size_mb = round(total_bytes / (1024 * 1024), 2)
    logger.info(f"Total bytes copied: {total_bytes} (~{size_mb} MB)")
    logger.info("=== Backup Run End ===")

    # Exit code
    if failed > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
