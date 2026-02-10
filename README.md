# MicroServices Network Manager

A cloud-native microservices management platform with an integrated API gateway and real-time ChatOps interface. This project demonstrates a complete microservices architecture with service orchestration, load balancing, and interactive network management capabilities.

## Project Overview

MicroNet Manager is a comprehensive system for managing and monitoring microservices in a networked environment. It features:

- **API Gateway**: Centralized entry point for all microservices with load balancing and health monitoring
- **Three Core Microservices**: User, Product, and Order services with RESTful APIs
- **Real-time ChatOps**: WebSocket-based command interface for interactive service management
- **Role-based Access Control**: Separate interfaces for managers and clients with different permissions
- **Service Health Monitoring**: Automatic health checks and status reporting
- **Load Balancing**: Round-robin load distribution for product service requests

## Architecture

The system follows a distributed architecture with the following components:

1. **API Gateway** (Port 8000): Main entry point that routes requests to appropriate services
2. **User Service** (Port 8001): Manages user data and authentication
3. **Product Service** (Port 8002): Handles product catalog and inventory
4. **Order Service** (Port 8003): Manages orders and transactions
5. **Web Frontend**: Interactive dashboard for service management
6. **WebSocket ChatOps**: Real-time command interface for system operations

## Key Features

### Service Management
- Start/stop individual microservices
- Real-time health status monitoring
- Service failure simulation and recovery
- Automatic health checks every 10 seconds

### Data Operations
- Complete CRUD operations for users, products, and orders
- Search and filtering capabilities
- Purchase and order processing workflows
- Inventory management with stock tracking

### Network Features
- Load balancing between service instances
- Request routing with timeout handling
- Service discovery and endpoint management
- Connection pooling and resource management

### ChatOps Interface
- Real-time WebSocket communication
- Command-based service control
- Role-specific command permissions
- System-wide broadcast notifications
- Interactive help and command history

### Dashboard Interface
- Visual service status indicators
- Role-based UI (Manager/Client views)
- Real-time activity logs
- System architecture visualization
- One-click service testing

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Communication**: REST APIs, WebSocket, gRPC (protobuf)
- **Deployment**: Uvicorn ASGI server
- **Protocol**: HTTP/1.1, WebSocket protocol

## Project Structure

```
project-root/
├── api_gateway/
│   ├── main.py              # Main API gateway application
│   ├── config.py            # Configuration settings
│   └── ...                  # Other gateway files
├── user_service/
│   └── server.py            # User service implementation
├── product_service/
│   └── server.py            # Product service implementation
├── order_service/
│   └── server.py            # Order service implementation
├── frontend/
│   ├── index.html           # Main dashboard
│   ├── style.css            # Styling
│   └── script.js            # Frontend logic
├── protobuf/
│   ├── user.proto           # gRPC service definition
│   ├── user_pb2.py          # Generated Python classes
│   └── user_pb2_grpc.py     # Generated gRPC client/server
└── test_grpc.py             # gRPC test client
```

## Usage Scenarios

1. **Service Orchestration**: Manage microservices lifecycle through API or ChatOps
2. **Load Testing**: Test load balancing with concurrent requests
3. **Fault Tolerance**: Simulate service failures and test recovery mechanisms
4. **System Monitoring**: Real-time monitoring of all services and their health status
5. **Interactive Management**: Use ChatOps for command-line style system administration
6. **Role-based Operations**: Different interfaces for system administrators and regular users

The system is designed as an educational tool for understanding microservices architecture, API gateways, and real-time system management while providing practical, production-like features for service orchestration and monitoring.
