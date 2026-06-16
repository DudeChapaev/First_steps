import pytest
import os
import sqlite3
from database import DatabaseManager
from models import Customer, Order, OrderItem


@pytest.fixture
def db():
    # Используем базу данных в памяти для тестов
    db = DatabaseManager(":memory:")
    # Добавляем тестового клиента
    db.add_customer(Customer(name="Test Client", phone="123", address="Test Addr"))
    return db


def test_add_and_get_customer(db):
    customers = db.get_customers()
    assert len(customers) == 1
    assert customers[0].name == "Test Client"


def test_delete_customer_with_orders(db):
    # Создаем заказ
    order = Order(customer_id=1, order_date="2026-06-08", status="новый", total=100.0,
                  items=[OrderItem(product_name="A", quantity=1, price=100.0)])
    db.add_order(order)

    # Пытаемся удалить клиента (должно вернуться False из-за RESTRICT)
    result = db.delete_customer(1)
    assert result is False


def test_add_and_get_order(db):
    order = Order(customer_id=1, order_date="2026-06-08", status="в доставке", total=250.0,
                  items=[OrderItem(product_name="Товар 1", quantity=2, price=125.0)])
    db.add_order(order)

    orders = db.get_orders()
    assert len(orders) == 1
    assert orders[0].total == 250.0
    assert len(orders[0].items) == 1