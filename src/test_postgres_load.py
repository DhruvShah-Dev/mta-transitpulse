"""End-to-end loader smoke test in a temporary local PostgreSQL cluster."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="mta_pg_test_", dir=ROOT) as temporary:
        cluster = Path(temporary).resolve()
        if cluster.parent != ROOT:
            raise RuntimeError("Unexpected temporary cluster location")
        subprocess.run(["initdb", "-D", str(cluster), "-A", "trust", "-U", "mta_test", "--no-instructions"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["pg_ctl", "-D", str(cluster), "-o", "-p 55432 -h 127.0.0.1", "-l", str(cluster / "server.log"), "-w", "start"], check=True, stdout=subprocess.DEVNULL)
        try:
            env = os.environ.copy()
            env["MTA_DATABASE_URL"] = "host=127.0.0.1 port=55432 dbname=postgres user=mta_test"
            subprocess.run([sys.executable, str(ROOT / "src" / "load_postgres.py")], cwd=ROOT, env=env, check=True)
        finally:
            subprocess.run(["pg_ctl", "-D", str(cluster), "-m", "immediate", "-w", "stop"], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
