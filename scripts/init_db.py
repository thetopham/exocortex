"""Initialize the SQLite database for the exocortex service."""
from exocortex import db


def main() -> None:
    db.init_db()
    print(f"Database ready at {db.DB_PATH}")


if __name__ == "__main__":
    main()
