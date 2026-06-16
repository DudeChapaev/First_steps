import pytest
import os
from database import DatabaseManager
from data_export import DataExporter
from models import Customer, Order, OrderItem


@pytest.fixture
def setup_data(tmp_path):
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    db.add_customer(Customer(name="Export Client", phone="999", address="Nowhere"))
    order = Order(customer_id=1, order_date="2026-01-01", status="выполнен", total=500.0,
                  items=[OrderItem(product_name="Book", quantity=2, price=250.0)])
    db.add_order(order)

    exporter = DataExporter(db)
    return exporter, tmp_path


def test_export_import_json(setup_data):
    exporter, tmp_path = setup_data
    json_file = tmp_path / "test.json"

    exporter.export_json(str(json_file))
    assert json_file.exists()

    # Очищаем БД и импортируем
    exporter.db._get_connection().execute("DELETE FROM orders")
    exporter.db._get_connection().execute("DELETE FROM order_items")

    exporter.import_json(str(json_file))
    orders = exporter.db.get_orders()
    assert len(orders) == 1
    assert orders[0].items[0].product_name == "Book"


def test_export_import_xml(setup_data):
    exporter, tmp_path = setup_data
    xml_file = tmp_path / "test.xml"

    exporter.export_xml(str(xml_file))
    assert xml_file.exists()

    exporter.db._get_connection().execute("DELETE FROM orders")
    exporter.db._get_connection().execute("DELETE FROM order_items")

    exporter.import_xml(str(xml_file))
    orders = exporter.db.get_orders()
    assert len(orders) == 1
    assert orders[0].total == 500.0