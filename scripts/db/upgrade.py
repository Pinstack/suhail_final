#!/usr/bin/env python3
"""
Run Alembic migrations to the latest (head).
Usage:
  python scripts/db/upgrade.py [target]

If target is omitted, defaults to 'head'.
"""
from pathlib import Path
import sys
from alembic import command
from alembic.config import Config


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "head"
    project_root = Path(__file__).resolve().parents[2]
    cfg_path = project_root / "alembic.ini"
    alembic_cfg = Config(str(cfg_path))
    # Ensure script_location points to our alembic directory
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    command.upgrade(alembic_cfg, target)


if __name__ == "__main__":
    main()

