#!/usr/bin/env python3
"""
Run Alembic downgrade to a target revision (use with caution).
Usage:
  python scripts/db/downgrade.py <target>

Example targets:
  -1         (one revision down)
  base       (initial state)
  <rev_hash> (specific revision)
"""
from pathlib import Path
import sys
from alembic import command
from alembic.config import Config


def main():
    if len(sys.argv) < 2:
        print("Usage: downgrade.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    project_root = Path(__file__).resolve().parents[2]
    cfg_path = project_root / "alembic.ini"
    alembic_cfg = Config(str(cfg_path))
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    command.downgrade(alembic_cfg, target)


if __name__ == "__main__":
    main()

