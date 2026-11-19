"""Manage a private, loopback-only PostgreSQL cluster for MTA TransitPulse.

Run: python src/local_postgres.py setup|start|status|stop|connect
Cluster and generated password live beside the project in .mta-local-postgres.
"""

import json
import os
import secrets
import socket
import subprocess
import sys
from pathlib import Path

from psycopg.conninfo import make_conninfo


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / ".mta-local-postgres"
CLUSTER = BASE / "cluster"
CONFIG = BASE / "connection.json"


def config():
    if not CONFIG.exists():
        raise RuntimeError("Local MTA PostgreSQL is not configured; run: python src/local_postgres.py setup")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def connection_info():
    settings = config()
    return make_conninfo(
        host="127.0.0.1", port=settings["port"], dbname="postgres",
        user=settings["user"], password=settings["password"], connect_timeout=5,
    )


def is_running():
    return subprocess.run(["pg_ctl", "-D", str(CLUSTER), "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def start():
    settings = config()
    if is_running():
        print(f"MTA PostgreSQL already running on 127.0.0.1:{settings['port']}")
        return
    subprocess.run([
        "pg_ctl", "-D", str(CLUSTER), "-o", f"-p {settings['port']} -h 127.0.0.1",
        "-l", str(BASE / "server.log"), "-w", "start",
    ], check=True, stdout=subprocess.DEVNULL)
    print(f"MTA PostgreSQL running on 127.0.0.1:{settings['port']}")


def setup():
    if CONFIG.exists() or CLUSTER.exists():
        raise RuntimeError("A local MTA PostgreSQL configuration or cluster already exists; no files were replaced")
    BASE.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(36)
    pwfile = BASE / "initdb_password.txt"
    try:
        pwfile.write_text(password + "\n", encoding="utf-8")
        subprocess.run([
            "initdb", "-D", str(CLUSTER), "-A", "scram-sha-256", "-U", "mta_admin",
            "--pwfile", str(pwfile), "--no-instructions",
        ], check=True, stdout=subprocess.DEVNULL)
    finally:
        pwfile.unlink(missing_ok=True)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    CONFIG.write_text(json.dumps({"user": "mta_admin", "password": password, "port": port}, indent=2), encoding="utf-8")
    start()
    print(f"Connection details stored in {CONFIG}")


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "setup":
        setup()
    elif action == "start":
        start()
    elif action == "status":
        if CONFIG.exists():
            settings = config()
            print(f"{'running' if is_running() else 'stopped'} on 127.0.0.1:{settings['port']}")
        else:
            print("not configured")
    elif action == "stop":
        if is_running():
            subprocess.run(["pg_ctl", "-D", str(CLUSTER), "-m", "fast", "-w", "stop"], check=True, stdout=subprocess.DEVNULL)
            print("MTA PostgreSQL stopped")
        else:
            print("MTA PostgreSQL already stopped")
    elif action == "connect":
        start()
        settings = config()
        env = os.environ.copy()
        env["PGPASSWORD"] = settings["password"]
        subprocess.run([
            "psql", "-h", "127.0.0.1", "-p", str(settings["port"]),
            "-U", settings["user"], "-d", "postgres",
        ], env=env, check=True)
    else:
        raise SystemExit("Use setup, start, status, stop, or connect")


if __name__ == "__main__":
    main()
