# paper_exchange.py
import sqlite3
from config import DB_NAME, ACCOUNT_RISK_PER_TRADE, LEVERAGE

class PaperExchange:
    def __init__(self, initial_balance: float = 10000.0):
        self.db_name = DB_NAME
        self._init_simulation_balance(initial_balance)

    def _init_simulation_balance(self, initial_balance: float):
        """Sets up a virtual cash balance in the local database if it doesn't exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM bot_state WHERE key='virtual_balance'")
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO bot_state (key, value) VALUES ('virtual_balance', ?)", (str(initial_balance),))
            conn.commit()
        conn.close()

    def get_balance(self) -> float:
        """Returns the current simulated free USDT balance."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM bot_state WHERE key='virtual_balance'")
        balance = float(cursor.fetchone()[0])
        conn.close()
        return balance

    def update_balance(self, amount: float):
        """Updates the simulated balance dynamically."""
        current_balance = self.get_balance()
        new_balance = current_balance + amount
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE bot_state SET value=? WHERE key='virtual_balance'", (str(new_balance),))
        conn.commit()
        conn.close()

    def calculate_order_size(self, current_price: float) -> float:
        """Calculates the position size based on 20% account risk and 20x leverage."""
        balance = self.get_balance()
        allocated_capital = balance * ACCOUNT_RISK_PER_TRADE
        
        # Buying power is multiplied by leverage
        buying_power = allocated_capital * LEVERAGE
        position_amount = buying_power / current_price
        return position_amount