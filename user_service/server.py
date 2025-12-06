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

app = FastAPI(title="User Service")

# In-memory database (replace with real DB in production)
users_db = {}
user_id_counter = 1

# Add some sample users
users_db["1"] = {
    "id": "1",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2024-01-15 10:30:00"
}

users_db["2"] = {
    "id": "2", 
    "name": "Jane Smith",
    "email": "jane@example.com",
    "created_at": "2024-01-16 14:20:00"
}

users_db["3"] = {
    "id": "3",
    "name": "Bob Johnson",
    "email": "bob@example.com",
    "created_at": "2024-01-17 09:15:00"
}

user_id_counter = 4

class UserCreate(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: str = None
    email: str = None

@app.post("/users/")
def create_user(user: UserCreate):
    global user_id_counter
    user_id = str(user_id_counter)
    users_db[user_id] = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    user_id_counter += 1
    print(f"✅ Created user: {users_db[user_id]}")
    return users_db[user_id]

@app.get("/users/{user_id}")
def get_user(user_id: str):
    print(f"🔍 Getting user {user_id}")
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}")
def update_user(user_id: str, user: UserUpdate):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.name:
        users_db[user_id]["name"] = user.name
    if user.email:
        users_db[user_id]["email"] = user.email
    
    users_db[user_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"✏️ Updated user: {users_db[user_id]}")
    return users_db[user_id]

@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = users_db.pop(user_id)
    print(f"🗑️ Deleted user: {deleted_user}")
    return {"message": "User deleted", "user": deleted_user}

@app.get("/users/")
def list_users():
    print(f"📋 Listing all users (total: {len(users_db)})")
    return {
        "total_users": len(users_db),
        "users": list(users_db.values())
    }

@app.get("/search/users/")
def search_users(query: str = ""):
    results = []
    for user_id, user in users_db.items():
        if (query.lower() in user["name"].lower() or 
            query.lower() in user["email"].lower()):
            results.append(user)
    
    print(f"🔎 Search for '{query}' found {len(results)} users")
    return {
        "query": query,
        "results": results,
        "total_found": len(results)
    }

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "user_service",
        "total_users": len(users_db),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/stats")
def get_stats():
    return {
        "total_users": len(users_db),
        "last_user_id": user_id_counter - 1,
        "service_uptime": "running"
    }

# Test endpoint for API Gateway
@app.get("/test")
def test():
    return {"message": "User Service REST endpoint working"}

if __name__ == "__main__":
    print("✅ User Service (REST) starting on port 8001")
    print("📝 Available endpoints:")
    print("   POST /users/ - Create user")
    print("   GET /users/{id} - Get user")
    print("   PUT /users/{id} - Update user") 
    print("   DELETE /users/{id} - Delete user")
    print("   GET /users/ - List all users")
    print("   GET /search/users/ - Search users")
    print("   GET /health - Health check")
    print("   GET /stats - Service statistics")
    print("   GET /test - Test endpoint")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")