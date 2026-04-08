"""
SQLite Backup / Export Strategy (Sprint 2, Mission 1)

Provides:
- On-demand and scheduled DB backup to timestamped files.
- PRAGMA integrity_check before every backup.
- Restore from backup with pre-restore validation.
- Cleanup of old backups beyond a retention window.
"""
from __future__ import annotations

import logging
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKUP_DIR = getattr(settings, "BACKUP_DIR", settings.BASE_DIR / "backups")
RETENTION_DAYS = int(getattr(settings, "BACKUP_RETENTION_DAYS", 30))
DB_PATH = settings.DATABASES["default"]["NAME"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_backup_dir() -> Path:
    """Create the backup directory if it doesn't exist."""
    path = Path(BACKUP_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _run_integrity_check(db_path: str | Path) -> Dict[str, Any]:
    """
    Run ``PRAGMA integrity_check`` and ``PRAGMA foreign_key_check``
    against the given SQLite database.

    Returns:
        {
            "ok": bool,
            "integrity": list[str],
            "foreign_keys": list[tuple],
        }
    """
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute("PRAGMA integrity_check;")
        integrity_rows = [row[0] for row in cursor.fetchall()]
        integrity_ok = integrity_rows == ["ok"]

        cursor = conn.execute("PRAGMA foreign_key_check;")
        fk_issues = cursor.fetchall()

        return {
            "ok": integrity_ok and len(fk_issues) == 0,
            "integrity": integrity_rows,
            "foreign_keys": fk_issues,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_integrity(db_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """Run integrity checks on the live database (or a given path)."""
    target = str(db_path or DB_PATH)
    result = _run_integrity_check(target)
    level = logging.INFO if result["ok"] else logging.ERROR
    logger.log(level, "Integrity check on %s: %s", target, result)
    return result


def create_backup(*, tag: str = "") -> Dict[str, Any]:
    """
    Create a timestamped backup of the live SQLite DB.

    Steps:
    1. Run integrity check on live DB.
    2. Use ``sqlite3.Connection.backup()`` for a safe online copy.
    3. Run integrity check on the backup.

    Args:
        tag: Optional string appended to the filename for labelling.

    Returns:
        {
            "success": bool,
            "backup_path": str | None,
            "pre_check": dict,
            "post_check": dict | None,
            "timestamp": str,
        }
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{tag}" if tag else ""
    backup_dir = _ensure_backup_dir()
    backup_filename = f"lifeos_backup_{timestamp}{suffix}.sqlite3"
    backup_path = backup_dir / backup_filename

    # Step 1: pre-check
    pre_check = check_integrity()
    if not pre_check["ok"]:
        logger.error("Pre-backup integrity check FAILED — backup aborted")
        return {
            "success": False,
            "backup_path": None,
            "pre_check": pre_check,
            "post_check": None,
            "timestamp": timestamp,
        }

    # Step 2: online backup
    try:
        source = sqlite3.connect(str(DB_PATH))
        dest = sqlite3.connect(str(backup_path))
        source.backup(dest)
        dest.close()
        source.close()
        logger.info("Backup created: %s", backup_path)
    except Exception as exc:
        logger.error("Backup copy failed: %s", exc)
        return {
            "success": False,
            "backup_path": None,
            "pre_check": pre_check,
            "post_check": None,
            "timestamp": timestamp,
        }

    # Step 3: post-check
    post_check = check_integrity(backup_path)
    if not post_check["ok"]:
        logger.error("Post-backup integrity check FAILED — backup may be corrupt")
        backup_path.unlink(missing_ok=True)
        return {
            "success": False,
            "backup_path": None,
            "pre_check": pre_check,
            "post_check": post_check,
            "timestamp": timestamp,
        }

    return {
        "success": True,
        "backup_path": str(backup_path),
        "pre_check": pre_check,
        "post_check": post_check,
        "timestamp": timestamp,
    }


def list_backups() -> List[Dict[str, Any]]:
    """Return metadata for all existing backups, newest first."""
    backup_dir = _ensure_backup_dir()
    files = sorted(backup_dir.glob("lifeos_backup_*.sqlite3"), reverse=True)
    results = []
    for f in files:
        stat = f.stat()
        results.append({
            "path": str(f),
            "filename": f.name,
            "size_bytes": stat.st_size,
            "created_at": datetime.utcfromtimestamp(stat.st_ctime).isoformat(),
        })
    return results


def restore_from_backup(backup_path: str | Path) -> Dict[str, Any]:
    """
    Restore the live DB from a backup file.

    Steps:
    1. Validate the backup exists and passes integrity check.
    2. Create a safety snapshot of the current live DB.
    3. Replace the live DB with the backup.

    Returns:
        {"success": bool, "safety_snapshot": str | None, ...}
    """
    backup_path = Path(backup_path)
    if not backup_path.exists():
        return {"success": False, "error": "Backup file not found"}

    # Validate backup integrity
    check = check_integrity(backup_path)
    if not check["ok"]:
        return {"success": False, "error": "Backup failed integrity check", "details": check}

    # Safety snapshot
    safety = create_backup(tag="pre_restore_safety")

    # Replace live DB
    try:
        shutil.copy2(str(backup_path), str(DB_PATH))
        logger.info("Restored DB from %s", backup_path)
        return {
            "success": True,
            "restored_from": str(backup_path),
            "safety_snapshot": safety.get("backup_path"),
        }
    except Exception as exc:
        logger.error("Restore failed: %s", exc)
        return {"success": False, "error": str(exc)}


def cleanup_old_backups(retention_days: int = RETENTION_DAYS) -> int:
    """Delete backups older than *retention_days*. Returns count deleted."""
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    backup_dir = _ensure_backup_dir()
    deleted = 0
    for f in backup_dir.glob("lifeos_backup_*.sqlite3"):
        modified = datetime.utcfromtimestamp(f.stat().st_mtime)
        if modified < cutoff:
            f.unlink()
            deleted += 1
            logger.info("Deleted old backup: %s", f.name)
    return deleted
