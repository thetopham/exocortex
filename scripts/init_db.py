from exocortex import db


def main() -> None:
    db.init_db()
    print(f"Initialized database at {db.DB_PATH}")


if __name__ == "__main__":
    main()
