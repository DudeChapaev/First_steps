from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Customer:
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    address: str = ""

@dataclass
class OrderItem:
    id: Optional[int] = None
    order_id: Optional[int] = None
    product_name: str = ""
    quantity: int = 1
    price: float = 0.0

@dataclass
class Order:
    id: Optional[int] = None
    customer_id: int = 0
    order_date: str = ""
    status: str = "новый"
    total: float = 0.0
    items: List[OrderItem] = None
    customer_name: str = ""

    def __post_init__(self):
        if self.items is None:
            self.items = []