import requests
import socket
import time

def test_services():
    print("=== TESTING MICROSERVICES VIA API GATEWAY ===\n")
    
    # Test User Service (REST - updated from gRPC)
    print("1. Testing User Service (REST):")
    try:
        response = requests.get("http://localhost:8000/users/123")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Product Service (REST with load balancing)
    print("\n2. Testing Product Service (REST with Load Balancing):")
    for i in range(3):
        try:
            response = requests.get("http://localhost:8000/products/1")
            if response.status_code == 200:
                data = response.json()
                print(f"   Request {i+1}: {data} (Instance: {data.get('load_balanced_instance', 'N/A')})")
            else:
                print(f"   Request {i+1}: Error {response.status_code}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test Order Service (REST)
    print("\n3. Testing Order Service (REST):")
    try:
        response = requests.get("http://localhost:8000/orders/2")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check status
    print("\n4. Checking System Status:")
    try:
        response = requests.get("http://localhost:8000/management/status")
        status = response.json()
        print(f"   Services: { {k: v['healthy'] for k, v in status['services'].items()} }")
        print(f"   Total Requests: {status['total_requests']}")
        print(f"   Load Balancer State: {status['load_balancer_state']}")
    except Exception as e:
        print(f"   Error: {e}")

def chatops_demo():
    print("\n" + "="*60)
    print("=== CHATOPS NETWORK MANAGEMENT ===")
    print("Connecting to ChatOps server...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 9999))
            s.settimeout(5.0)
            
            # Read welcome message
            welcome = s.recv(1024).decode()
            print(welcome, end='')
            
            # Test commands
            commands = ["status", "fail product", "status", "recover product", "status", "help"]
            
            for cmd in commands:
                print(f"\nSending command: {cmd}")
                s.sendall(cmd.encode())
                response = s.recv(1024).decode()
                print(response, end='')
                time.sleep(1)  # Small delay between commands
            
            s.sendall(b"exit")
            
    except Exception as e:
        print(f"Failed to connect to ChatOps: {e}")

if __name__ == "__main__":
    test_services()
    chatops_demo()