
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DATABASES = {
    "DEV": "SALES_DEV",
    "STAGING": "SALES_STAGING",
    "CI": None,
}

MIGRATION_DIR = Path("sql/migrations")
BOOTSTRAP = Path(
    "sql/bootstrap/01_deployment_tracking.sql"
)
MIGRATION_PATTERN = re.compile(
    r"^(V\d{3})__[a-z0-9_]+\.sql$"
)


def execute(query=None, file=None, variables=None):
    command = ["snow", "sql", "-x", "--format", "JSON", "--enhanced-exit-codes"]

    if file is not None:
        command += ["-f", str(file)]
    else:
        command += ["-q", query]

    for key, value in (variables or {}).items():
        command += ["-D", f"{key}={value}"]

    result = subprocess.run(
        command, check=True,
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print("Snowflake CLI command failed", flush=True)
        print("Command:", command, flush=True)
        print("Exit code:", result.returncode, flush=True)

        if result.stdout:
            print("STDOUT:", result.stdout, flush=True)

        if result.stderr:
            print("STDERR:", result.stderr, flush=True)

        raise RuntimeError(
            f"Snowflake SQL execution failed: "
            f"exit code {result.returncode}"
        )

    return result.stdout


def rows(query):
    data = json.loads(execute(query=query))
    if not isinstance(data, list):
        raise RuntimeError("Unexpected SQL JSON output")
    return data


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_migrations():
    migrations = {}
    versions = set()

    for path in sorted(MIGRATION_DIR.glob("*.sql")):
        match = MIGRATION_PATTERN.fullmatch(path.name)

        if not match:
            raise RuntimeError(
                f"Invalid migration name: {path.name}"
            )

        version = match.group(1)

        if version in versions:
            raise RuntimeError(
                f"Duplicate migration version: {version}"
            )

        versions.add(version)
        migrations[version] = (path, sha256(path))

    return migrations


def load_history(database):
    history = {}

    for row in rows(f"""
        SELECT VERSION, FILE_NAME, CHECKSUM
        FROM {database}.CI_CD.SCHEMA_MIGRATIONS
    """):
        version = row["VERSION"]

        if version in history:
            raise RuntimeError(
                f"Duplicate ledger record: {version}"
            )

        history[version] = (
            row["FILE_NAME"],
            row["CHECKSUM"]
        )

    return history


def verify_history(files, history):
    # Perform ALL comparisons before new DDL.
    for version, (filename, digest) in history.items():
        if version not in files:
            raise RuntimeError(
                f"Missing applied migration: {version}"
            )

        path, actual_digest = files[version]

        if filename != path.name:
            raise RuntimeError(
                f"Filename mismatch: {version}"
            )

        if digest != actual_digest:
            raise RuntimeError(
                f"Checksum mismatch: {path.name}"
            )

    pending = [
        version for version in files
        if version not in history
    ]

    if pending and history:
        if min(pending) < max(history):
            raise RuntimeError(
                "Out-of-order migration detected"
            )

    return sorted(pending)


def run(database, environment, git_sha, run_id):
    execute(
        file=BOOTSTRAP,
        variables={"database": database}
    )

    files = discover_migrations()
    history = load_history(database)
    pending = verify_history(files, history)

    print("Migration history verified", flush=True)

    for version in pending:
        path, digest = files[version]

        print(f"Applying {path.name}", flush=True)

        execute(
            file=path,
            variables={"database": database}
        )

        execute(query=f"""
            INSERT INTO
                {database}.CI_CD.SCHEMA_MIGRATIONS
                (VERSION, FILE_NAME, CHECKSUM, GIT_SHA)
            VALUES (
                {literal(version)},
                {literal(path.name)},
                {literal(digest)},
                {literal(git_sha)}
            )
        """)

        print(f"Recorded {version}", flush=True)

    if environment == "STAGING":
        validation = "tests/validate_staging.sql"
    else:
        validation = "tests/validate_dev.sql"

    execute(
        file=validation,
        variables={"database": database}
    )

    execute(query=f"""
        INSERT INTO
            {database}.CI_CD.DEPLOYMENT_HISTORY
            (DEPLOYMENT_ID, GIT_SHA,
             ENVIRONMENT, STATUS)
        VALUES (
            {literal(run_id)},
            {literal(git_sha)},
            {literal(environment)},
            'SUCCESS'
        )
    """)

    print(
        f"SUCCESS: {environment} / {database} / {git_sha}",
        flush=True
    )


def main():
    environment = os.environ["DEPLOY_ENVIRONMENT"]
    database = os.environ["DEPLOY_DATABASE"]

    if environment not in DATABASES:
        raise ValueError("Invalid environment")

    expected = DATABASES[environment]

    if environment == "CI":
        if not re.fullmatch(
            r"CI_PR_[0-9]+_[0-9]+", database
        ):
            raise ValueError("Invalid CI database name")
    elif database != expected:
        raise ValueError(
            f"{environment} must target {expected}"
        )

    sha = os.environ["GITHUB_SHA"]
    run_id = (
        os.environ["GITHUB_RUN_ID"] + "-"
        + os.environ["GITHUB_RUN_ATTEMPT"]
    )

    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid Git SHA")

    if not re.fullmatch(r"[0-9]+-[0-9]+", run_id):
        raise ValueError("Invalid run ID")

    run(database, environment, sha, run_id)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"DEPLOYMENT FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
