from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import uuid

class OrderItem(BaseModel):
    item_id: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: float

class CustomerInfo(BaseModel):
    name: str
    phone: str
    address: str
    notes: Optional[str] = None

class CreateOrderRequest(BaseModel):
    restaurant_id: str
    items: List[OrderItem]
    customer: CustomerInfo

class Order(BaseModel):
    id: str
    restaurant_id: str
    items: List[OrderItem]
    customer: CustomerInfo
    total_amount: float
    status: str
    created_at: datetime

app = FastAPI(title="China Restaurant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Erlaubt Anfragen von allen Domains
    allow_credentials=False, # Bei allow_origins=["*"] MUSS das False sein
    allow_methods=["*"], # Erlaubt GET, POST, OPTIONS etc.
    allow_headers=["*"], # Erlaubt alle Header


)

ORDERS_DB: list[Order] = []

with open("menu.json", "r", encoding="utf-8") as f:
    MENU_DATA = json.load(f)

def calculate_total(items: List[OrderItem]) -> float:
    return sum(i.quantity * i.unit_price for i in items)

@app.get("/restaurants/{restaurant_id}/menu")
def get_menu(restaurant_id: str):
    menu = MENU_DATA.get(restaurant_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Speisekarte nicht gefunden")
    return menu

@app.post("/restaurants/{restaurant_id}/orders", response_model=Order)
def create_order(restaurant_id: str, payload: CreateOrderRequest):
    if payload.restaurant_id != restaurant_id:
        raise HTTPException(status_code=400, detail="restaurant_id passt nicht zur URL")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Keine Artikel in der Bestellung")

    order_id = str(uuid.uuid4())
    total = calculate_total(payload.items)

    order = Order(
        id=order_id,
        restaurant_id=restaurant_id,
        items=payload.items,
        customer=payload.customer,
        total_amount=total,
        status="pending_payment",
        created_at=datetime.utcnow(),
    )

    ORDERS_DB.append(order)
    return order

@app.get("/restaurants/{restaurant_id}/orders", response_model=List[Order])
def list_orders(restaurant_id: str):
    return [o for o in ORDERS_DB if o.restaurant_id == restaurant_id]
