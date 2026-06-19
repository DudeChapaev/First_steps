import pytest
import os
from datetime import datetime
from database import DatabaseManager
from models import Customer, Order, OrderItem


@pytest.fixture
def db():
    # Используем базу данных в памяти для быстрых и изолированных тестов
    db = DatabaseManager(":memory:")
    db.add_customer(Customer(name="Test Client", phone="123", address="Test Addr"))
    db.add_customer(Customer(name="Test Client 2", phone="456", address="Test Addr 2"))
    return db


def test_add_and_get_customer(db):
    customers = db.get_customers()
    assert len(customers) == 2
    assert customers[0].name == "Test Client"


def test_delete_customer_with_orders(db):
    order = Order(customer_id=1, order_date="2026-06-08", status="новый", total=100.0,
                  items=[OrderItem(product_name="A", quantity=1, price=100.0)])
    db.add_order(order)

    # Попытка удалить клиента с заказами должна вернуть False
    result = db.delete_customer(1)
    assert result is False
    assert len(db.get_customers()) == 2


def test_delete_customer_without_orders(db):
    # У клиента 2 нет заказов, его можно удалить
    result = db.delete_customer(2)
    assert result is True
    assert len(db.get_customers()) == 1


def test_add_and_get_order(db):
    order = Order(customer_id=1, order_date="2026-06-08", status="в доставке", total=250.0,
                  items=[OrderItem(product_name="Товар 1", quantity=2, price=125.0)])
    db.add_order(order)

    orders = db.get_orders()
    assert len(orders) == 1
    assert orders[0].total == 250.0
    assert len(orders[0].items) == 1


def test_update_order(db):
    order = Order(customer_id=1, order_date="2026-06-08", status="новый", total=100.0,
                  items=[OrderItem(product_name="A", quantity=1, price=100.0)])
    order_id = db.add_order(order)

    # Обновляем заказ
    updated_order = Order(
        id=order_id, customer_id=1, order_date="2026-06-09",
        status="выполнен", total=200.0,
        items=[OrderItem(product_name="B", quantity=2, price=100.0)]
    )
    db.update_order(updated_order)

    orders = db.get_orders()
    assert len(orders) == 1
    assert orders[0].status == "выполнен"
    assert orders[0].total == 200.0
    assert orders[0].items[0].product_name == "B"


def test_delete_order(db):
    order = Order(customer_id=1, order_date="2026-06-08", status="новый", total=100.0,
                  items=[OrderItem(product_name="A", quantity=1, price=100.0)])
    order_id = db.add_order(order)

    db.delete_order(order_id)
    assert len(db.get_orders()) == 0


def test_get_orders_with_filters(db):
    db.add_order(Order(customer_id=1, order_date="2026-06-01", status="новый", total=10.0))
    db.add_order(Order(customer_id=1, order_date="2026-06-02", status="выполнен", total=20.0))
    db.add_order(Order(customer_id=2, order_date="2026-06-01", status="новый", total=30.0))

    # Фильтр по статусу
    new_orders = db.get_orders(status_filter="новый")
    assert len(new_orders) == 2

    # Фильтр по дате
    date_orders = db.get_orders(date_filter="2026-06-02")
    assert len(date_orders) == 1


def test_get_report(db):
    today = datetime.now().strftime("%Y-%m-%d")
    db.add_order(Order(customer_id=1, order_date=today, status="выполнен", total=500.0,
                       items=[OrderItem(product_name="X", quantity=1, price=500.0)]))
    db.add_order(Order(customer_id=1, order_date=today, status="отменён", total=100.0,
                       items=[OrderItem(product_name="Y", quantity=1, price=100.0)]))

    report = db.get_report("month")

    # Отмененные заказы не должны идти в выручку
    assert report["revenue"] == 500.0
    assert report["status_counts"]["выполнен"] == 1
    assert report["status_counts"]["отменён"] == 1

    # Топ клиентов
    assert len(report["top_clients"]) == 1
    assert report["top_clients"][0]["name"] == "Test Client"
    assert report["top_clients"][0]["sum"] == 500.0