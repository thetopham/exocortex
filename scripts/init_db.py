from exocortex.db import init_db


if __name__ == "__main__":
    init_db()
    print("Database initialized at", init_db.__globals__["DB_PATH"])
