import json
import xml.etree.ElementTree as ET
from models import Order, OrderItem
from database import DatabaseManager
from logger_config import setup_logger

logger = setup_logger("ExportImport")


class DataExporter:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def export_json(self, filepath: str):
        orders = self.db.get_orders()
        data = [{
            "id": o.id, "customer_id": o.customer_id, "customer_name": o.customer_name,
            "order_date": o.order_date, "status": o.status, "total": o.total,
            "items": [{"product_name": i.product_name, "quantity": i.quantity, "price": i.price} for i in o.items]
        } for o in orders]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Экспорт в JSON выполнен: {filepath}")

    def import_json(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            if not all(k in item for k in ['customer_id', 'order_date', 'status', 'total', 'items']):
                logger.warning(f"Пропущена некорректная запись: {item}")
                continue
            order = Order(
                customer_id=item['customer_id'], order_date=item['order_date'],
                status=item['status'], total=item['total'],
                items=[OrderItem(product_name=i['product_name'], quantity=i['quantity'], price=i['price']) for i in
                       item['items']]
            )
            self.db.add_order(order)
        logger.info(f"Импорт из JSON выполнен: {filepath}")

    def export_xml(self, filepath: str):
        orders = self.db.get_orders()
        root = ET.Element("orders")
        for o in orders:
            order_elem = ET.SubElement(root, "order", id=str(o.id))
            ET.SubElement(order_elem, "customer_id").text = str(o.customer_id)
            ET.SubElement(order_elem, "order_date").text = o.order_date
            ET.SubElement(order_elem, "status").text = o.status
            ET.SubElement(order_elem, "total").text = str(o.total)
            items_elem = ET.SubElement(order_elem, "items")
            for i in o.items:
                item_elem = ET.SubElement(items_elem, "item")
                ET.SubElement(item_elem, "product_name").text = i.product_name
                ET.SubElement(item_elem, "quantity").text = str(i.quantity)
                ET.SubElement(item_elem, "price").text = str(i.price)
        ET.ElementTree(root).write(filepath, encoding='utf-8', xml_declaration=True)
        logger.info(f"Экспорт в XML выполнен: {filepath}")

    def import_xml(self, filepath: str):
        tree = ET.parse(filepath)
        for order_elem in tree.getroot().findall("order"):
            try:
                items = [OrderItem(
                    product_name=item_elem.find("product_name").text,
                    quantity=int(item_elem.find("quantity").text),
                    price=float(item_elem.find("price").text)
                ) for item_elem in order_elem.find("items").findall("item")]

                order = Order(
                    customer_id=int(order_elem.find("customer_id").text),
                    order_date=order_elem.find("order_date").text,
                    status=order_elem.find("status").text,
                    total=float(order_elem.find("total").text),
                    items=items
                )
                self.db.add_order(order)
            except Exception as e:
                logger.warning(f"Ошибка импорта XML заказа: {e}")
        logger.info(f"Импорт из XML выполнен: {filepath}")