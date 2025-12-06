from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import uvicorn
import time
import sys
import os

# Add project root to path for shared modules if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

app = FastAPI(title="Product Service")

# In-memory database
products_db = {}
product_id_counter = 1

# Add some sample products
products_db["1"] = {
    "id": "1",
    "name": "Laptop",
    "price": 999.99,
    "description": "High-performance laptop with 16GB RAM and 512GB SSD",
    "category": "electronics",
    "stock": 10,
    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
}

products_db["2"] = {
    "id": "2", 
    "name": "Wireless Mouse",
    "price": 29.99,
    "description": "Ergonomic wireless mouse with long battery life",
    "category": "electronics",
    "stock": 50,
    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
}

products_db["3"] = {
    "id": "3",
    "name": "Mechanical Keyboard",
    "price": 79.99,
    "description": "RGB mechanical keyboard with blue switches",
    "category": "electronics", 
    "stock": 25,
    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
}

product_id_counter = 4

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str = ""
    category: str = "general"
    stock: int = 0

class ProductUpdate(BaseModel):
    name: str = None
    price: float = None
    description: str = None
    category: str = None
    stock: int = None

class PurchaseRequest(BaseModel):
    quantity: int

@app.post("/products/")
def create_product(product: ProductCreate):
    global product_id_counter
    product_id = str(product_id_counter)
    products_db[product_id] = {
        "id": product_id,
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "category": product.category,
        "stock": product.stock,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    product_id_counter += 1
    print(f"✅ Created product: {products_db[product_id]}")
    return products_db[product_id]

@app.get("/products/{product_id}")
def get_product(product_id: str):
    print(f"🔍 Getting product {product_id}")
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}")
def update_product(product_id: str, product: ProductUpdate):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.name:
        products_db[product_id]["name"] = product.name
    if product.price:
        products_db[product_id]["price"] = product.price
    if product.description:
        products_db[product_id]["description"] = product.description
    if product.category:
        products_db[product_id]["category"] = product.category
    if product.stock is not None:
        products_db[product_id]["stock"] = product.stock
    
    products_db[product_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"✏️ Updated product: {products_db[product_id]}")
    return products_db[product_id]

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    deleted_product = products_db.pop(product_id)
    print(f"🗑️ Deleted product: {deleted_product}")
    return {"message": "Product deleted", "product": deleted_product}

@app.get("/products/")
def list_products(category: str = None, min_price: float = None, max_price: float = None):
    filtered_products = []
    
    for product in products_db.values():
        if category and product["category"] != category:
            continue
        if min_price and product["price"] < min_price:
            continue
        if max_price and product["price"] > max_price:
            continue
        filtered_products.append(product)
    
    print(f"📋 Listing products (total: {len(filtered_products)})")
    return {
        "total_products": len(filtered_products),
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price
        },
        "products": filtered_products
    }

@app.post("/products/{product_id}/restock")
def restock_product(product_id: str, quantity: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    products_db[product_id]["stock"] += quantity
    print(f"📦 Restocked product {product_id} with {quantity} units")
    return {
        "message": f"Restocked {quantity} units",
        "product": products_db[product_id]
    }

@app.post("/products/{product_id}/purchase")
def purchase_product(product_id: str, purchase: PurchaseRequest):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if products_db[product_id]["stock"] < purchase.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    products_db[product_id]["stock"] -= purchase.quantity
    total_price = products_db[product_id]["price"] * purchase.quantity
    
    print(f"🛒 Purchased {purchase.quantity} units of product {product_id} for ${total_price}")
    return {
        "message": f"Purchased {purchase.quantity} units",
        "total_price": total_price,
        "remaining_stock": products_db[product_id]["stock"],
        "product": products_db[product_id]
    }

@app.get("/search/products/")
def search_products(query: str = ""):
    results = []
    for product_id, product in products_db.items():
        if (query.lower() in product["name"].lower() or 
            query.lower() in product["description"].lower() or
            query.lower() in product["category"].lower()):
            results.append(product)
    
    print(f"🔎 Search for '{query}' found {len(results)} products")
    return {
        "query": query,
        "results": results,
        "total_found": len(results)
    }

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "product_service",
        "total_products": len(products_db),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/stats")
def get_stats():
    total_value = sum(product["price"] * product["stock"] for product in products_db.values())
    return {
        "total_products": len(products_db),
        "total_stock": sum(product["stock"] for product in products_db.values()),
        "total_inventory_value": total_value,
        "last_product_id": product_id_counter - 1
    }

# Test endpoint for API Gateway
@app.get("/test")
def test():
    return {"message": "Product Service REST endpoint working"}

if __name__ == "__main__":
    print("✅ Product Service (REST) starting on port 8002")
    print("🛍️ Available endpoints:")
    print("   POST /products/ - Create product")
    print("   GET /products/{id} - Get product")
    print("   PUT /products/{id} - Update product") 
    print("   DELETE /products/{id} - Delete product")
    print("   GET /products/ - List products with filters")
    print("   POST /products/{id}/restock - Restock product")
    print("   POST /products/{id}/purchase - Purchase product")
    print("   GET /search/products/ - Search products")
    print("   GET /health - Health check")
    print("   GET /stats - Service statistics")
    print("   GET /test - Test endpoint")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")