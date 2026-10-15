"""Provision a development role/database through a local PostgreSQL administrator.

Run through uv with .env loaded. Existing roles/databases are never reconfigured.
The development role may create test databases; it is unsuitable for production.
"""

import getpass
import os

import psycopg
from psycopg import sql


def main() -> None:
    database = os.environ["POSTGRES_DB"]
    role = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    if os.environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.development":
        raise SystemExit("This helper is for development settings only.")
    if os.environ.get("POSTGRES_HOST") not in {"localhost", "127.0.0.1"}:
        raise SystemExit("This helper only provisions a local PostgreSQL database.")

    # Peer authentication for your WSL account; no administrative password in arguments.
    with psycopg.connect(
        dbname="postgres",
        user=getpass.getuser(),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        autocommit=True,
    ) as connection:
        existing_role = connection.execute(
            "SELECT rolsuper, rolcreaterole, rolreplication FROM pg_roles WHERE rolname = %s",
            (role,),
        ).fetchone()
        if existing_role is None:
            connection.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN CREATEDB NOSUPERUSER NOCREATEROLE "
                    "NOREPLICATION PASSWORD {}"
                ).format(sql.Identifier(role), sql.Literal(password))
            )
            print("Created a dedicated development role with test-database creation permission.")
        elif any(existing_role):
            raise SystemExit("The existing project role is privileged; review it manually.")
        else:
            print("Preserved the existing role, including its password and permissions.")

        existing_database = connection.execute(
            "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = %s", (database,)
        ).fetchone()
        if existing_database is None:
            connection.execute(
                sql.SQL("CREATE DATABASE {} OWNER {} ENCODING 'UTF8' TEMPLATE template0").format(
                    sql.Identifier(database), sql.Identifier(role)
                )
            )
            print("Created the project database.")
        elif existing_database[0] != role:
            raise SystemExit("The existing database has another owner; no changes were made to it.")
        else:
            print("Preserved the existing project database.")


if __name__ == "__main__":
    main()
