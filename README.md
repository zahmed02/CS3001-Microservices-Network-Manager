# 🚀 MicroNet Manager - Microservices Network Management System

> **Course Project:** CS3001 Computer Networks | **University:** FAST-NUCES Karachi | **Semester:** Fall 2025

A practical implementation of cloud-native microservices networking featuring intelligent API Gateway routing, load balancing, real-time health monitoring, and WebSocket-based ChatOps for system management.

---

## 📁 **Project Structure**
CS3001-Microservices-Network-Manager/
│
├── 📁 frontend/ # Web Dashboard & ChatOps UI
│ ├── 📄 index.html # Main dashboard (HTML)
│ ├── 📄 style.css # Styling (CSS)
│ └── 📄 script.js # WebSocket client & API logic (JavaScript)
│
├── 📁 api_gateway/ # Central API Gateway
│ ├── 📄 main.py # Gateway server + WebSocket ChatOps
│ └── 📄 config.py # Service configuration
│
├── 📁 user_service/ # User Management Microservice
│ └── 📄 server.py # User Service REST API (Port: 8001)
│
├── 📁 product_service/ # Product Catalog Microservice
│ └── 📄 server.py # Product Service REST API (Port: 8002)
│
├── 📁 order_service/ # Order Processing Microservice
│ └── 📄 server.py # Order Service REST API (Port: 8003)
│
├── 📁 client/ # Test Client
│ └── 📄 client.py # CLI client for testing
│

---

## 🛠️ **Prerequisites**

### **Required Software**
- **Python 3.8 or higher** → [Download Python](https://www.python.org/downloads/)
- **Git** (for cloning) → [Download Git](https://git-scm.com/)
- **Modern Web Browser** (Chrome/Firefox/Edge)
- **Command Line/Terminal** access

### **Python Libraries to Install**
Run these commands in your terminal **before starting**:

# Install core dependencies
pip install fastapi uvicorn pydantic

# Install WebSocket support
pip install websockets

# Install HTTP client library
pip install requests

# Alternatively, install all at once:
pip install fastapi uvicorn pydantic websockets requests
