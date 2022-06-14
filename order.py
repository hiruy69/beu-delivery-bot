from dataclasses import dataclass, field
from typing import List
import random
import string
from enum import Enum, unique
def get_id() -> str:
    return ''.join(random.choice(string.digits) for _ in range(5))

class Status(Enum):
    PENDING = 1
    COMPLETED = 2
    CANCELLED = 3
    INCOMING = 4

@dataclass
class User:
    username: str 
    phone: str 
    id: str = field(default_factory=get_id, repr=False)


@dataclass
class Vendor:
    name: str 
    phone: str
    address: str 
    chat_id: str
    id: str = field(default_factory=get_id, repr=False)

@dataclass
class Food:
    name: str 
    stock: int
    vendor: Vendor 
    price: float 
    description: str
    id: str = field(default_factory=get_id, repr=False)

@dataclass
class Order:
    user: User
    quantity: int
    food: Food
    status:  Status = field(default=Status.INCOMING)
    id: str = field(default_factory=get_id, repr=False)


def register_as_vendor(address: str, name: str, phone: str) -> Vendor:
    vendor = Vendor(name=name, phone=phone, address=address)
    return vendor




user = User(username='hiruy',phone='123456789')
vendor = Vendor(name='vendor',phone='329763759',chat_id="1960956629",address='address')
product = Food(name='product',stock=10,vendor=vendor,price=70,description='description')

orders = [Order(quantity=2,user=user,food=product) for _ in range(3)]

foods = [Food(name='product',stock=10,vendor=vendor,price=70,description="description") for _ in range(4)]

vendors = [Vendor(name='vendor',phone='329763759',chat_id="1960956629",address='address') for _ in range(3)]

