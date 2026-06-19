import sqlite3
import os
from typing import List
from models import Customer, Order, OrderItem
from logger_config import setup_logger

logger = setup_logger("Database")


class DatabaseManager:
    def __init__(self, db_path: str = "data/delivery.db"):
        if db_path != ":memory:":
            os.makedirs('data', exist_ok=True)
        self.db_path = db_path
        self._conn = None
        self._init_db()

    def _get_connection(self):
        if self._conn is None:
            if self.db_path == ":memory:":
                self._conn = sqlite3.connect(":memory:")
            else:
                self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                address TEXT
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                order_date TEXT NOT NULL,
                status TEXT CHECK(status IN ('новый','в доставке','выполнен','отменён')),
                total REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        logger.info("База данных инициализирована")

    def add_customer(self, customer: Customer) -> int:
        conn = self._get_connection()
        cursor = conn.execute(
            "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
            (customer.name, customer.phone, customer.address)
        )
        conn.commit()
        logger.info(f"Добавлен клиент: {customer.name}")
        return cursor.lastrowid

    def get_customers(self) -> List[Customer]:
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM customers").fetchall()
        return [Customer(**row) for row in rows]

    def delete_customer(self, customer_id: int) -> bool:
        try:
            conn = self._get_connection()
            conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            logger.info(f"Удален клиент ID: {customer_id}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Невозможно удалить клиента ID: {customer_id}, существуют связанные заказы.")
            return False

    def add_order(self, order: Order) -> int:
        conn = self._get_connection()
        cursor = conn.execute(
            "INSERT INTO orders (customer_id, order_date, status, total) VALUES (?, ?, ?, ?)",
            (order.customer_id, order.order_date, order.status, order.total)
        )
        order_id = cursor.lastrowid
        for item in order.items:
            conn.execute(
                "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, item.product_name, item.quantity, item.price)
            )
        conn.commit()
        logger.info(f"Создан заказ ID: {order_id}")
        return order_id

    def update_order(self, order: Order):
        conn = self._get_connection()
        conn.execute(
            "UPDATE orders SET customer_id=?, order_date=?, status=?, total=? WHERE id=?",
            (order.customer_id, order.order_date, order.status, order.total, order.id)
        )
        conn.execute("DELETE FROM order_items WHERE order_id=?", (order.id,))
        for item in order.items:
            conn.execute(
                "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                (order.id, item.product_name, item.quantity, item.price)
            )
        conn.commit()
        logger.info(f"Обновлен заказ ID: {order.id}")

    def delete_order(self, order_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        logger.info(f"Удален заказ ID: {order_id}")

    def get_orders(self, status_filter: str = None, date_filter: str = None) -> List[Order]:
        query = """
            SELECT o.id, o.customer_id, o.order_date, o.status, o.total, c.name as customer_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE 1=1
        """
        params = []
        if status_filter:
            query += " AND o.status = ?"
            params.append(status_filter)
        if date_filter:
            query += " AND o.order_date = ?"
            params.append(date_filter)

        conn = self._get_connection()
        rows = conn.execute(query, params).fetchall()
        orders = []
        for row in rows:
            items_rows = conn.execute(
                "SELECT * FROM order_items WHERE order_id = ?", (row['id'],)
            ).fetchall()
            items = [OrderItem(**ir) for ir in items_rows]
            orders.append(Order(
                id=row['id'], customer_id=row['customer_id'], order_date=row['order_date'],
                status=row['status'], total=row['total'], customer_name=row['customer_name'], items=items
            ))
        return orders

    def get_report(self, period: str = "month") -> dict:
        from datetime import datetime, timedelta
        now = datetime.now()
        if period == "day":
            start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        elif period == "week":
            start_date = (now - timedelta(weeks=1)).strftime("%Y-%m-%d")
        else:
            start_date = (now.replace(day=1)).strftime("%Y-%m-%d")

        conn = self._get_connection()
        status_counts = {row['status']: row['count'] for row in conn.execute(
            "SELECT status, COUNT(*) as count FROM orders GROUP BY status"
        ).fetchall()}

        top_clients = conn.execute("""
            SELECT c.name, SUM(o.total) as total_sum 
            FROM orders o JOIN customers c ON o.customer_id = c.id 
            WHERE o.status != 'отменён'
            GROUP BY c.id ORDER BY total_sum DESC LIMIT 3
        """).fetchall()

        revenue = conn.execute("""
            SELECT SUM(total) FROM orders 
            WHERE order_date >= ? AND status != 'отменён'
        """, (start_date,)).fetchone()[0] or 0.0

        return {
            "status_counts": status_counts,
            "top_clients": [{"name": row['name'], "sum": row['total_sum']} for row in top_clients],
            "revenue": revenue
        }