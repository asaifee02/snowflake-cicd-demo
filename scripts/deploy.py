
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DATABASE = "SALES_DEV"
MIGRATION_DIR = Path("sql/migrations")
BOOTSTRAP = Path(
    "sql/bootstrap/01_deployment_tracking.sql"
)
VALIDATION = Path("tests/validate_dev.sql")

PATTERN = re.compile(
    r"^(V[0-9]{3})__[a-z0-9_]+\.sql$"
)


def run_sql(query=None, filename=None, variables=None):
    command = [
        "snow", "sql", "-x",
        "--format", "JSON",
    ]

    if filename:
        command += ["-f", str(filename)]
    else:
        command += ["-q", query]

    for key, value in (variables or {}).items():
        command += ["-D", f"{key}={value}"]

    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout


def query_rows(query):
    output = run_sql(query=query)
    rows = json.loads(output)

    if not isinstance(rows, list):
        raise RuntimeError(
            "Unexpected Snowflake JSON response"
        )

    return rows


def sql_literal(value):
    # Used for values only, never SQL identifiers.
    return "'" + value.replace("'", "''") + "'"


def checksum(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def bootstrap():
    print("Preparing deployment metadata...")
    run_sql(filename=BOOTSTRAP)


def get_existing_migrations():
    rows = query_rows(f"""
        SELECT VERSION, CHECKSUM
        FROM {DATABASE}.CI_CD.SCHEMA_MIGRATIONS
    """)

    existing = {}

    for row in rows:
        version = row["VERSION"]

        if version in existing:
            raise RuntimeError(
                f"Duplicate ledger version: {version}"
            )

        existing[version] = row["CHECKSUM"]

    return existing


def apply_migrations(git_sha):
    existing = get_existing_migrations()
    seen = set()

    migrations = sorted(
        MIGRATION_DIR.glob("V*.sql")
    )

    for file in migrations:
        match = PATTERN.fullmatch(file.name)

        if not match:
            raise RuntimeError(
                f"Invalid migration filename: {file.name}"
            )

        version = match.group(1)

        if version in seen:
            raise RuntimeError(
                f"Duplicate migration: {version}"
            )

        seen.add(version)
        digest = checksum(file)

        if version in existing:
            if existing[version] != digest:
                raise RuntimeError(
                    f"Checksum mismatch: {file.name}. "
                    "Applied migrations are immutable."
                )

            print(f"SKIP {file.name}")
            continue

        if existing and version < max(existing):
            raise RuntimeError(
                f"Out-of-order migration: {file.name}"
            )

        print(f"APPLY {file.name}", flush=True)

        run_sql(
            filename=file,
            variables={"database": DATABASE},
        )

        run_sql(query=f"""
            INSERT INTO
                {DATABASE}.CI_CD.SCHEMA_MIGRATIONS
                (VERSION, FILE_NAME, CHECKSUM, GIT_SHA)
            VALUES (
                {sql_literal(version)},
                {sql_literal(file.name)},
                {sql_literal(digest)},
                {sql_literal(git_sha)}
            )
        """)

        existing[version] = digest
        print(f"RECORDED {version}", flush=True)

    # Detect migrations recorded in Snowflake but
    # absent from the checked-out repository.
    missing = set(existing) - seen
    if missing:
        raise RuntimeError(
            "Applied migration files missing: "
            + ", ".join(sorted(missing))
        )


def validate():
    print("Running DEV validation...", flush=True)
    run_sql(
        filename=VALIDATION,
        variables={"database": DATABASE},
    )


def record_release(git_sha, deployment_id):
    run_sql(query=f"""
        INSERT INTO
            {DATABASE}.CI_CD.DEPLOYMENT_HISTORY
            (DEPLOYMENT_ID, GIT_SHA,
             ENVIRONMENT, STATUS)
        VALUES (
            {sql_literal(deployment_id)},
            {sql_literal(git_sha)},
            'DEV',
            'SUCCESS'
        )
    """)


def main():
    git_sha = os.environ["GITHUB_SHA"]
    deployment_id = os.environ["GITHUB_RUN_ID"]
    attempt = os.environ["GITHUB_RUN_ATTEMPT"]

    if not re.fullmatch(r"[0-9a-f]{40}", git_sha):
        raise ValueError("Invalid Git commit SHA")

    if not deployment_id.isdecimal():
        raise ValueError("Invalid deployment ID")

    if not attempt.isdecimal():
        raise ValueError("Invalid run attempt")

    bootstrap()
    apply_migrations(git_sha)
    validate()

    record_release(
        git_sha,
        f"{deployment_id}-{attempt}",
    )

    print(
        f"SUCCESS: deployed {git_sha} to {DATABASE}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"DEPLOYMENT FAILED: {error}", file=sys.stderr)
        sys.exit(1)
