from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
import threading
import time
from typing import Dict, List
import os
import json
import uuid
import subprocess

# CREATE THE MAIN FASTAPI APPLICATION
app = FastAPI(title="MicroNet Manager API Gateway")

# GET THE PROJECT ROOT DIRECTORY FOR ABSOLUTE PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# 3 MICROSERVICE DETAILS (SUCH AS THEIR ADDRESS/PORT, THEIR LOCATION, DEFINED HERE)
services: Dict = {
    "user": {
        "host": "http://localhost:8001", 
        "type": "rest", 
        "healthy": True,
        "process": None,
        "port": 8001,
        "command": ["python", os.path.join(project_root, "user_service", "server.py")],
        "status": "stopped"
    },
    "product": {
        "host": "http://localhost:8002", 
        "type": "rest", 
        "healthy": True,
        "process": None,
        "port": 8002,
        "command": ["python", os.path.join(project_root, "product_service", "server.py")],
        "status": "stopped"
    },
    "order": {
        "host": "http://localhost:8003", 
        "type": "rest", 
        "healthy": True,
        "process": None,
        "port": 8003,
        "command": ["python", os.path.join(project_root, "order_service", "server.py")],
        "status": "stopped"
    }
}

# LOAD BALANCING INITIAL STATE
current_product_instance = 0
request_count = 0

# WEBSOCKECT CONNECTION MANAGER
class ConnectionManager:
    def __init__(self):
        # Store all active WebSocket connections
        self.active_connections: List[WebSocket] = []
        # Map WebSocket connections to user IDs
        self.connection_users: Dict[WebSocket, str] = {}
        # Track user roles for each connection
        self.user_roles: Dict[WebSocket, str] = {}

    # Connect a new WebSocket client
    async def connect(self, websocket: WebSocket, user_id: str, role: str = "client"):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_users[websocket] = user_id
        self.user_roles[websocket] = role
        print(f"WebSocket connected for user {user_id} with role {role}. Total: {len(self.active_connections)}")

    # Disconnect a WebSocket client
    def disconnect(self, websocket: WebSocket):
        user_id = self.connection_users.get(websocket, "Unknown")
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_users:
            del self.connection_users[websocket]
        if websocket in self.user_roles:
            del self.user_roles[websocket]
        print(f"WebSocket disconnected for user {user_id}. Total: {len(self.active_connections)}")

    # Send a message to a specific WebSocket client
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    # Broadcast a message to all connected WebSocket clients
    async def broadcast(self, message: str, exclude: WebSocket = None):
        disconnected = []
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    # Get the role of a WebSocket client
    def get_user_role(self, websocket: WebSocket) -> str:
        return self.user_roles.get(websocket, "client")

manager = ConnectionManager()

# Get the absolute path to the frontend directory
frontend_path = os.path.join(project_root, "frontend")

print(f"Current directory: {current_dir}")
print(f"Project root: {project_root}")
print(f"Frontend path: {frontend_path}")

# Serve frontend static files
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    print("✅ Frontend static files mounted at /static")
    print(f"✅ Serving from: {frontend_path}")
else:
    print(f"❌ Frontend directory not found at {frontend_path}")
    # Debug: list contents of project root
    print(f"Contents of {project_root}:")
    try:
        for item in os.listdir(project_root):
            print(f"  - {item}")
    except Exception as e:
        print(f"Error listing directory: {e}")

# Serve the main frontend page
@app.get("/")
async def serve_frontend():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"error": "Frontend not found", "path": index_path}

# Health check endpoint for the API gateway
@app.get("/health")
def health():
    return {"status": "healthy", "service": "api_gateway"}

# WebSocket endpoint for real-time ChatOps
@app.websocket("/ws/chatops")
async def websocket_endpoint(websocket: WebSocket):
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    # Get role from query parameter or default to client
    role = "client"
    try:
        if websocket.query_params.get("role"):
            role = websocket.query_params.get("role")
    except:
        pass
        
    await manager.connect(websocket, user_id, role)
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "system",
            "message": f"🔌 Connected to Network Management ChatOps! Role: {role}",
            "user_id": "system",
            "timestamp": time.time()
        }
        await manager.send_personal_message(json.dumps(welcome_msg), websocket)
        
        # Send connection info
        info_msg = {
            "type": "system",
            "message": f"Your User ID: {user_id} | Role: {role} | Type 'help' for commands",
            "user_id": "system", 
            "timestamp": time.time()
        }
        await manager.send_personal_message(json.dumps(info_msg), websocket)
        
        while True:
            data = await websocket.receive_text()
            user_role = manager.get_user_role(websocket)
            await handle_chatops_command(data, websocket, user_id, user_role)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Notify other clients about disconnection
        disconnect_msg = {
            "type": "system",
            "message": f"User {user_id} disconnected",
            "user_id": "system",
            "timestamp": time.time()
        }
        await manager.broadcast(json.dumps(disconnect_msg))
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Handle ChatOps commands from WebSocket clients
async def handle_chatops_command(command: str, websocket: WebSocket, user_id: str, user_role: str):
    """Handle ChatOps commands via WebSocket with bidirectional communication"""
    command = command.strip()
    print(f"WebSocket received from {user_id} (role: {user_role}): {command}")
    
    try:
        # Echo the command back to the sender and broadcast to others
        echo_msg = {
            "type": "command_sent",
            "message": command,
            "user_id": user_id,
            "timestamp": time.time()
        }
        await manager.send_personal_message(json.dumps(echo_msg), websocket)
        
        # Broadcast command to other clients (only if not sensitive)
        if not command.startswith(('start ', 'stop ', 'create ', 'update ', 'delete ')):
            broadcast_msg = {
                "type": "command_received", 
                "message": f"User {user_id} executed: {command}",
                "user_id": user_id,
                "timestamp": time.time()
            }
            await manager.broadcast(json.dumps(broadcast_msg), websocket)
        
        # Process the command
        response = await process_command(command, user_id, user_role)
        
        # Send response back to sender
        await manager.send_personal_message(json.dumps(response), websocket)
        
        # Broadcast response to other clients if it's a status-changing command
        if command.startswith(('fail ', 'recover ', 'start ', 'stop ')):
            broadcast_response = {
                "type": "system_broadcast",
                "message": f"System updated by {user_id}: {response['message']}",
                "user_id": "system",
                "timestamp": time.time()
            }
            await manager.broadcast(json.dumps(broadcast_response), websocket)
            
    except Exception as e:
        error_response = {
            "type": "error",
            "message": f"❌ Error processing command: {str(e)}",
            "user_id": "system",
            "timestamp": time.time()
        }
        await manager.send_personal_message(json.dumps(error_response), websocket)

# Process and execute ChatOps commands
async def process_command(command: str, user_id: str, user_role: str) -> Dict:
    """Process the actual command and return response"""
    command_lower = command.lower()
    
    if command_lower == "status":
        # Create serializable status data
        status_data = {
            "services": {k: {"status": v["status"], "healthy": v["healthy"]} for k, v in services.items()},
            "total_requests": request_count,
            "load_balancer_state": current_product_instance
        }
        
        message = "=== NETWORK STATUS ===\n"
        for service, info in status_data["services"].items():
            status = "✅ RUNNING" if info["status"] == "running" else "❌ STOPPED"
            health = "HEALTHY" if info["healthy"] else "UNHEALTHY"
            message += f"{service.upper():<10}: {status} ({health})\n"
        
        message += f"\nTotal Requests: {status_data['total_requests']}"
        message += f"\nLoad Balancer State: {status_data['load_balancer_state']}"
        
        return {
            "type": "command_response",
            "message": message,
            "user_id": "system",
            "timestamp": time.time()
        }
        
    elif command_lower.startswith("start "):
        if user_role != "manager":
            return {
                "type": "error",
                "message": "❌ Only managers can start services",
                "user_id": "system",
                "timestamp": time.time()
            }
        
        service_name = command_lower.split(" ")[1].lower()
        if service_name in services:
            success, msg = await start_service_process(service_name)
            if success:
                return {
                    "type": "command_response", 
                    "message": f"✅ {msg}",
                    "user_id": "system",
                    "timestamp": time.time()
                }
            else:
                return {
                    "type": "error",
                    "message": f"❌ {msg}",
                    "user_id": "system",
                    "timestamp": time.time()
                }
        return {
            "type": "error",
            "message": f"❌ Service '{service_name}' not found",
            "user_id": "system", 
            "timestamp": time.time()
        }
            
    elif command_lower.startswith("stop "):
        if user_role != "manager":
            return {
                "type": "error",
                "message": "❌ Only managers can stop services",
                "user_id": "system",
                "timestamp": time.time()
            }
        
        service_name = command_lower.split(" ")[1].lower()
        if service_name in services:
            success, msg = await stop_service_process(service_name)
            if success:
                return {
                    "type": "command_response",
                    "message": f"✅ {msg}", 
                    "user_id": "system",
                    "timestamp": time.time()
                }
            else:
                return {
                    "type": "error",
                    "message": f"❌ {msg}",
                    "user_id": "system",
                    "timestamp": time.time()
                }
        return {
            "type": "error",
            "message": f"❌ Service '{service_name}' not found",
            "user_id": "system",
            "timestamp": time.time()
        }
            
    elif command_lower.startswith("fail "):
        service_name = command_lower.split(" ")[1].lower()
        if service_name in services:
            services[service_name]["healthy"] = False
            return {
                "type": "command_response", 
                "message": f"✅ Simulated failure for {service_name} service",
                "user_id": "system",
                "timestamp": time.time()
            }
        return {
            "type": "error",
            "message": f"❌ Service '{service_name}' not found",
            "user_id": "system", 
            "timestamp": time.time()
        }
            
    elif command_lower.startswith("recover "):
        service_name = command_lower.split(" ")[1].lower()
        if service_name in services:
            services[service_name]["healthy"] = True
            return {
                "type": "command_response",
                "message": f"✅ Recovered {service_name} service", 
                "user_id": "system",
                "timestamp": time.time()
            }
        return {
            "type": "error",
            "message": f"❌ Service '{service_name}' not found",
            "user_id": "system",
            "timestamp": time.time()
        }

    elif command_lower.startswith("create user "):
        # Extract user data from command: create user John john@example.com
        parts = command.split(" ")
        if len(parts) >= 4:
            name = parts[2]
            email = parts[3]
            try:
                # Create user through API gateway
                user_data = {"name": name, "email": email}
                response = requests.post(
                    f"{services['user']['host']}/users/",
                    json=user_data,
                    timeout=5
                )
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "type": "command_response",
                        "message": f"✅ Created user: {user_data['name']} (ID: {user_data['id']})",
                        "user_id": "system",
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "type": "error",
                        "message": f"❌ Failed to create user: {response.text}",
                        "user_id": "system",
                        "timestamp": time.time()
                    }
            except Exception as e:
                return {
                    "type": "error",
                    "message": f"❌ Failed to create user: {str(e)}",
                    "user_id": "system",
                    "timestamp": time.time()
                }
        else:
            return {
                "type": "error",
                "message": "❌ Usage: create user <name> <email>",
                "user_id": "system",
                "timestamp": time.time()
            }
            
    elif command_lower == "help":
        help_text = """=== AVAILABLE COMMANDS ===
status                    - Show service health status
start <service>          - Start a service (Manager only)
stop <service>           - Stop a service (Manager only)
fail <service>           - Simulate service failure  
recover <service>        - Recover a service
create user <name> <email> - Create a new user
help                     - Show this help
clear                    - Clear chat history
users                    - Show connected users

Examples:
  start user
  stop product
  fail user
  recover product
  create user John john@example.com
  status
"""
        return {
            "type": "command_response",
            "message": help_text,
            "user_id": "system",
            "timestamp": time.time()
        }
            
    elif command_lower == "users":
        user_count = len(manager.active_connections)
        manager_count = sum(1 for role in manager.user_roles.values() if role == "manager")
        client_count = user_count - manager_count
        
        return {
            "type": "command_response",
            "message": f"Connected users: {user_count} (Managers: {manager_count}, Clients: {client_count})",
            "user_id": "system", 
            "timestamp": time.time()
        }
            
    elif command_lower == "clear":
        return {
            "type": "clear_chat",
            "user_id": "system",
            "timestamp": time.time()
        }
            
    else:
        return {
            "type": "error",
            "message": "❌ Unknown command. Type 'help' for available commands.",
            "user_id": "system",
            "timestamp": time.time()
        }

# Start a service as a subprocess
async def start_service_process(service_name: str):
    """Start a service as a subprocess"""
    service = services[service_name]
    
    if service["status"] == "running":
        return False, f"{service_name} service is already running"
    
    try:
        service["status"] = "starting"
        print(f"Starting service {service_name} with command: {service['command']}")
        
        # Start the service process
        process = subprocess.Popen(
            service["command"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        service["process"] = process
        service["status"] = "running"
        
        # Wait a bit for service to start
        time.sleep(3)
        
        # Check if service started successfully
        try:
            response = requests.get(f"{service['host']}/health", timeout=2)
            service["healthy"] = response.status_code == 200
            return True, f"Started {service_name} service"
        except:
            service["healthy"] = False
            return False, f"Service {service_name} started but not responding"
        
    except Exception as e:
        service["status"] = "stopped"
        service["process"] = None
        return False, f"Failed to start {service_name}: {str(e)}"

# Stop a service process
async def stop_service_process(service_name: str):
    """Stop a service process"""
    service = services[service_name]
    
    if service["status"] != "running":
        return False, f"{service_name} service is not running"
    
    try:
        service["status"] = "stopping"
        
        # Terminate the process if we started it
        if service["process"]:
            service["process"].terminate()
            try:
                service["process"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                service["process"].kill()
                service["process"].wait()
            service["process"] = None
        
        service["status"] = "stopped"
        service["healthy"] = False
        
        return True, f"Stopped {service_name} service"
        
    except Exception as e:
        service["status"] = "running"  # Revert status if failed to stop
        return False, f"Failed to stop {service_name}: {str(e)}"

# Background health check for all services
def health_check():
    """Background health check for all services"""
    while True:
        for service_name, service_info in services.items():
            # Skip health check for services that are stopped by manager and don't have a process
            if service_info["status"] == "stopped" and service_info["process"] is None:
                continue
                
            try:
                response = requests.get(f"{service_info['host']}/health", timeout=2)
                is_healthy = response.status_code == 200
                
                # Only update status if service is not manually stopped by manager
                if service_info["status"] != "stopped":
                    service_info["healthy"] = is_healthy
                    service_info["status"] = "running" if is_healthy else "stopped"
                
                print(f"Health check for {service_name}: reachable={is_healthy}, status={service_info['status']}")
                
            except Exception as e:
                # Service is not reachable
                if service_info["status"] != "stopped":
                    service_info["healthy"] = False
                    service_info["status"] = "stopped"
                print(f"Health check failed for {service_name}: {e}")
        
        # Log status without process objects
        status_summary = {k: {'status': v['status'], 'healthy': v['healthy']} for k, v in services.items()}
        print(f"Health status: {status_summary}")
        time.sleep(10)

# Get a specific user by ID
@app.get("/users/{user_id}")
def get_user(user_id: str):
    global request_count
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["user"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="User service has been stopped by manager")
    
    if not services["user"]["healthy"]:
        raise HTTPException(status_code=503, detail="User service unavailable")
    
    try:
        response = requests.get(f"{services['user']['host']}/users/{user_id}")
        return response.json()
    except Exception as e:
        services["user"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"User service error: {e}")

# Create a new user
@app.post("/users/")
def create_user(user_data: dict):
    global request_count
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["user"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="User service has been stopped by manager")
    
    if not services["user"]["healthy"]:
        raise HTTPException(status_code=503, detail="User service unavailable")
    
    try:
        response = requests.post(f"{services['user']['host']}/users/", json=user_data)
        return response.json()
    except Exception as e:
        services["user"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"User service error: {e}")

# Get a specific product by ID with load balancing
@app.get("/products/{product_id}")
def get_product(product_id: str):
    global request_count, current_product_instance
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["product"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="Product service has been stopped by manager")
    
    if not services["product"]["healthy"]:
        raise HTTPException(status_code=503, detail="Product service unavailable")
    
    instance = current_product_instance
    current_product_instance = (current_product_instance + 1) % 2
    
    try:
        response = requests.get(f"{services['product']['host']}/products/{product_id}")
        return {**response.json(), "load_balanced_instance": instance}
    except Exception as e:
        services["product"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"Product service error: {e}")

# Create a new product
@app.post("/products/")
def create_product(product_data: dict):
    global request_count
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["product"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="Product service has been stopped by manager")
    
    if not services["product"]["healthy"]:
        raise HTTPException(status_code=503, detail="Product service unavailable")
    
    try:
        response = requests.post(f"{services['product']['host']}/products/", json=product_data)
        return response.json()
    except Exception as e:
        services["product"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"Product service error: {e}")

# Purchase a product
@app.post("/products/{product_id}/purchase")
def purchase_product(product_id: str, purchase_data: dict):
    global request_count
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["product"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="Product service has been stopped by manager")
    
    if not services["product"]["healthy"]:
        raise HTTPException(status_code=503, detail="Product service unavailable")
    
    try:
        response = requests.post(f"{services['product']['host']}/products/{product_id}/purchase", json=purchase_data)
        return response.json()
    except Exception as e:
        services["product"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"Product service error: {e}")

# Get a specific order by ID
@app.get("/orders/{order_id}")
def get_order(order_id: str):
    global request_count
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["order"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="Order service has been stopped by manager")
    
    if not services["order"]["healthy"]:
        raise HTTPException(status_code=503, detail="Order service unavailable")
    
    try:
        response = requests.get(f"{services['order']['host']}/orders/{order_id}")
        return response.json()
    except Exception as e:
        services["order"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"Order service error: {e}")

# Create a new order
@app.post("/orders/")
def create_order(order_data: dict):
    global request_count
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["order"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="Order service has been stopped by manager")
    
    if not services["order"]["healthy"]:
        raise HTTPException(status_code=503, detail="Order service unavailable")
    
    try:
        response = requests.post(f"{services['order']['host']}/orders/", json=order_data)
        return response.json()
    except Exception as e:
        services["order"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"Order service error: {e}")

# Update an existing order
@app.put("/orders/{order_id}")
def update_order(order_id: str, order_data: dict):
    global request_count
    request_count += 1
    
    # Check if service is marked as stopped in gateway
    if services["order"]["status"] == "stopped":
        raise HTTPException(status_code=503, detail="Order service has been stopped by manager")
    
    if not services["order"]["healthy"]:
        raise HTTPException(status_code=503, detail="Order service unavailable")
    
    try:
        response = requests.put(f"{services['order']['host']}/orders/{order_id}", json=order_data)
        return response.json()
    except Exception as e:
        services["order"]["healthy"] = False
        raise HTTPException(status_code=503, detail=f"Order service error: {e}")

# Get current system status and service health
@app.get("/management/status")
def get_status():
    # Create a serializable copy of services without process objects
    serializable_services = {}
    for service_name, service_info in services.items():
        serializable_services[service_name] = {
            "host": service_info["host"],
            "type": service_info["type"], 
            "healthy": service_info["healthy"],
            "port": service_info["port"],
            "status": service_info["status"]
        }
    
    return {
        "services": serializable_services,
        "total_requests": request_count,
        "load_balancer_state": current_product_instance
    }

# Start a specific service (manager role required)
@app.post("/management/start/{service_name}")
async def start_service(service_name: str, request: Request):
    # Get role from header
    user_role = request.headers.get('user-role', 'client')
    
    print(f"Start service request for {service_name} from role: {user_role}")
    
    if user_role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can start services")
    
    if service_name in services:
        success, message = await start_service_process(service_name)
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=500, detail=message)
    raise HTTPException(status_code=404, detail="Service not found")

# Stop a specific service (manager role required)
@app.post("/management/stop/{service_name}")
async def stop_service(service_name: str, request: Request):
    # Get role from header
    user_role = request.headers.get('user-role', 'client')
    
    print(f"Stop service request for {service_name} from role: {user_role}")
    
    if user_role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can stop services")
    
    if service_name in services:
        success, message = await stop_service_process(service_name)
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=500, detail=message)
    raise HTTPException(status_code=404, detail="Service not found")

# Simulate a service failure for testing
@app.post("/management/simulate_failure/{service_name}")
def simulate_failure(service_name: str):
    if service_name in services:
        services[service_name]["healthy"] = False
        return {"message": f"Simulated failure for {service_name}"}
    return {"error": "Service not found"}

# Recover a service from failure state
@app.post("/management/recover/{service_name}")
def recover_service(service_name: str):
    if service_name in services:
        services[service_name]["healthy"] = True
        return {"message": f"Recovered {service_name}"}
    return {"error": "Service not found"}

# Start the application
if __name__ == "__main__":
    # Start health check in background
    health_thread = threading.Thread(target=health_check, daemon=True)
    health_thread.start()
    
    import uvicorn
    print("API Gateway starting on http://localhost:8000")
    print("Frontend available at: http://localhost:8000")
    print("WebSocket ChatOps available at: ws://localhost:8000/ws/chatops")
    print(f"Serving frontend from: {frontend_path}")
    print("Note: Services start in 'stopped' state. Use management controls to start them.")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")