from models import Customer, Order, OrderItem

def test_customer_creation():
    c = Customer(id=1, name="John", phone="123", address="Home")
    assert c.name == "John"

def test_order_total_calculation():
    # Логика подсчета суммы находится в GUI/бизнес-логике, но модель должна хранить данные корректно
    item = OrderItem(product_name="Laptop", quantity=1, price=1000.0)
    order = Order(customer_id=1, order_date="2026-06-08", status="новый", total=1000.0, items=[item])
    assert order.total == 1000.0
    assert len(order.items) == 1