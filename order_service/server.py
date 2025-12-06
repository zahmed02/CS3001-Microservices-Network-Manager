from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import time
import random
import sys
import os

# Add project root to path for shared modules if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

app = FastAPI(title="Order Service")

# In-memory database
orders_db = {}
order_id_counter = 1

# Add some sample orders
orders_db["1"] = {
    "id": "1",
    "user_id": "1",
    "items": [
        {"product_id": "1", "quantity": 1, "price": 999.99},
        {"product_id": "2", "quantity": 2, "price": 29.99}
    ],
    "total_amount": 1059.97,
    "status": "completed",
    "shipping_address": "123 Main St, New York, NY 10001",
    "created_at": "2024-01-15 10:30:00",
    "updated_at": "2024-01-20 14:45:00"
}

orders_db["2"] = {
    "id": "2",
    "user_id": "2", 
    "items": [
        {"product_id": "3", "quantity": 1, "price": 79.99}
    ],
    "total_amount": 79.99,
    "status": "processing",
    "shipping_address": "456 Oak Ave, Los Angeles, CA 90210",
    "created_at": "2024-01-18 16:20:00",
    "updated_at": "2024-01-18 16:20:00"
}

orders_db["3"] = {
    "id": "3",
    "user_id": "1",
    "items": [
        {"product_id": "2", "quantity": 1, "price": 29.99}
    ],
    "total_amount": 29.99,
    "status": "shipped",
    "shipping_address": "123 Main St, New York, NY 10001",
    "created_at": "2024-01-10 09:15:00",
    "updated_at": "2024-01-12 11:30:00"
}

order_id_counter = 4

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem]
    shipping_address: str

class OrderUpdate(BaseModel):
    status: str = None
    shipping_address: str = None

# Order status flow: pending -> confirmed -> shipped -> delivered
VALID_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

@app.post("/orders/")
def create_order(order: OrderCreate):
    global order_id_counter
    order_id = str(order_id_counter)
    
    # Calculate total amount
    total_amount = sum(item.price * item.quantity for item in order.items)
    
    orders_db[order_id] = {
        "id": order_id,
        "user_id": order.user_id,
        "items": [item.dict() for item in order.items],
        "total_amount": total_amount,
        "status": "pending",
        "shipping_address": order.shipping_address,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    order_id_counter += 1
    print(f"✅ Created order: {order_id} for user {order.user_id}, total: ${total_amount}")
    return orders_db[order_id]

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    print(f"🔍 Getting order {order_id}")
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.put("/orders/{order_id}")
def update_order(order_id: str, order_update: OrderUpdate):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order_update.status:
        if order_update.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
        orders_db[order_id]["status"] = order_update.status
    
    if order_update.shipping_address:
        orders_db[order_id]["shipping_address"] = order_update.shipping_address
    
    orders_db[order_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"✏️ Updated order: {order_id} to status: {orders_db[order_id]['status']}")
    return orders_db[order_id]

@app.delete("/orders/{order_id}")
def cancel_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    orders_db[order_id]["status"] = "cancelled"
    orders_db[order_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"❌ Cancelled order: {order_id}")
    return {"message": "Order cancelled", "order": orders_db[order_id]}

@app.get("/orders/")
def list_orders(user_id: str = None, status: str = None):
    filtered_orders = []
    
    for order in orders_db.values():
        if user_id and order["user_id"] != user_id:
            continue
        if status and order["status"] != status:
            continue
        filtered_orders.append(order)
    
    print(f"📋 Listing orders (total: {len(filtered_orders)})")
    return {
        "total_orders": len(filtered_orders),
        "filters": {
            "user_id": user_id,
            "status": status
        },
        "orders": filtered_orders
    }

@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if orders_db[order_id]["status"] != "pending":
        raise HTTPException(status_code=400, detail="Order can only be confirmed from pending status")
    
    orders_db[order_id]["status"] = "confirmed"
    orders_db[order_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"✅ Confirmed order: {order_id}")
    return {"message": "Order confirmed", "order": orders_db[order_id]}

@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, tracking_number: str = None):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if orders_db[order_id]["status"] != "confirmed":
        raise HTTPException(status_code=400, detail="Order must be confirmed before shipping")
    
    orders_db[order_id]["status"] = "shipped"
    orders_db[order_id]["tracking_number"] = tracking_number or f"TRACK{random.randint(100000, 999999)}"
    orders_db[order_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚚 Shipped order: {order_id} with tracking: {orders_db[order_id]['tracking_number']}")
    return {"message": "Order shipped", "order": orders_db[order_id]}

@app.post("/orders/{order_id}/deliver")
def deliver_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if orders_db[order_id]["status"] != "shipped":
        raise HTTPException(status_code=400, detail="Order must be shipped before delivery")
    
    orders_db[order_id]["status"] = "delivered"
    orders_db[order_id]["delivered_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    orders_db[order_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"🎉 Delivered order: {order_id}")
    return {"message": "Order delivered", "order": orders_db[order_id]}

@app.get("/users/{user_id}/orders")
def get_user_orders(user_id: str):
    user_orders = [order for order in orders_db.values() if order["user_id"] == user_id]
    print(f"📦 Found {len(user_orders)} orders for user {user_id}")
    return {
        "user_id": user_id,
        "total_orders": len(user_orders),
        "orders": user_orders
    }

@app.get("/health")
def health():
    status_counts = {}
    for order in orders_db.values():
        status = order["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "status": "healthy", 
        "service": "order_service",
        "total_orders": len(orders_db),
        "order_statuses": status_counts,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/stats")
def get_stats():
    total_revenue = sum(order["total_amount"] for order in orders_db.values() if order["status"] != "cancelled")
    status_counts = {}
    for order in orders_db.values():
        status = order["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total_orders": len(orders_db),
        "total_revenue": total_revenue,
        "order_statuses": status_counts,
        "last_order_id": order_id_counter - 1
    }

# Test endpoint for API Gateway
@app.get("/test")
def test():
    return {"message": "Order Service REST endpoint working"}

if __name__ == "__main__":
    print("✅ Order Service (REST) starting on port 8003")
    print("📦 Available endpoints:")
    print("   POST /orders/ - Create order")
    print("   GET /orders/{id} - Get order")
    print("   PUT /orders/{id} - Update order") 
    print("   DELETE /orders/{id} - Cancel order")
    print("   GET /orders/ - List orders with filters")
    print("   POST /orders/{id}/confirm - Confirm order")
    print("   POST /orders/{id}/ship - Ship order")
    print("   POST /orders/{id}/deliver - Deliver order")
    print("   GET /users/{user_id}/orders - Get user orders")
    print("   GET /health - Health check")
    print("   GET /stats - Service statistics")
    print("   GET /test - Test endpoint")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")