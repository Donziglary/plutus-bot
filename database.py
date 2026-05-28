# database.py
import sqlite3
from config import DB_NAME

def initialize_database():
    """Initializes the SQLite database and creates required tables if they do not exist."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Table to track active open positions for local state recovery
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_positions (
            symbol TEXT PRIMARY KEY,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            amount REAL NOT NULL,
            stop_loss REAL,
            take_profit REAL,
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for historical performance and trade analysis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            amount REAL NOT NULL,
            pnl REAL NOT NULL,
            closed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for maintaining global bot execution state if needed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    initialize_database()
    print("Database infrastructure successfully initialized locally.")