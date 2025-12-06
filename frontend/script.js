// Configuration
const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/chatops';

// WebSocket variables
let websocket = null;
let isConnected = false;
let currentUserId = null;
let currentUserRole = 'client';

// DOM Elements
const statusElements = {
    user: document.getElementById('user-status'),
    product: document.getElementById('product-status'),
    order: document.getElementById('order-status'),
    gateway: document.getElementById('gateway-status')
};

const serviceCards = {
    user: document.getElementById('user-service'),
    product: document.getElementById('product-service'),
    order: document.getElementById('order-service'),
    gateway: document.getElementById('gateway-service')
};

// Role Management
function updateUIForRole() {
    const roleSelect = document.getElementById('user-role');
    currentUserRole = roleSelect.value;
    
    // Update role displays
    document.getElementById('current-role-display').textContent = currentUserRole.charAt(0).toUpperCase() + currentUserRole.slice(1);
    document.getElementById('current-role-display').className = `role-badge ${currentUserRole}`;
    document.getElementById('current-role-chat').textContent = currentUserRole;
    
    // Show/hide manager-only elements
    const managerElements = document.querySelectorAll('.manager-only');
    managerElements.forEach(el => {
        el.style.display = currentUserRole === 'manager' ? 'block' : 'none';
    });
    
    addLog(`Role changed to: ${currentUserRole}`);
    
    // Reconnect WebSocket with new role if connected
    if (isConnected) {
        disconnectWebSocket();
        setTimeout(() => connectWebSocket(), 1000);
    }
}

// WebSocket Functions
function connectWebSocket() {
    try {
        const role = currentUserRole;
        const wsUrl = `${WS_URL}?role=${role}`;
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function(event) {
            isConnected = true;
            updateWebSocketStatus('🟢 Connected', 'connected');
            document.getElementById('chatops-input').disabled = false;
            document.getElementById('send-button').disabled = false;
            document.getElementById('chatops-input').placeholder = `Type a command as ${role}...`;
            addChatMessage('system', `Connected to ChatOps as ${role}`, 'system');
            addLog(`WebSocket connected as ${role}`);
        };
        
        websocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        websocket.onclose = function(event) {
            isConnected = false;
            currentUserId = null;
            updateWebSocketStatus('🔴 Disconnected', 'disconnected');
            addChatMessage('system', 'WebSocket connection closed.', 'system');
            document.getElementById('chatops-input').disabled = true;
            document.getElementById('send-button').disabled = true;
            document.getElementById('chatops-input').placeholder = "Disconnected - Click Connect";
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            addChatMessage('error', 'WebSocket connection error. Check if server is running.');
        };
        
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        addChatMessage('error', `Failed to connect: ${error.message}`);
    }
}

function disconnectWebSocket() {
    if (websocket) {
        websocket.close();
        websocket = null;
        currentUserId = null;
    }
}

function updateWebSocketStatus(text, className) {
    const statusElement = document.getElementById('websocket-status');
    statusElement.textContent = text;
    statusElement.className = className;
}

function sendChatOpsCommand() {
    const input = document.getElementById('chatops-input');
    const command = input.value.trim();
    
    if (command && isConnected) {
        websocket.send(command);
        input.value = '';
    } else if (!isConnected) {
        addChatMessage('error', 'Not connected to WebSocket. Click "Connect WebSocket" first.');
    }
}

function sendQuickCommand(command) {
    if (isConnected) {
        websocket.send(command);
    } else {
        addChatMessage('error', 'Not connected to WebSocket. Click "Connect WebSocket" first.');
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'system':
            addChatMessage('system', data.message, data.user_id);
            break;
        case 'command_sent':
            addChatMessage('command_sent', data.message, data.user_id);
            break;
        case 'command_received':
            addChatMessage('command_received', data.message, data.user_id);
            break;
        case 'command_response':
            addChatMessage('command_response', data.message, data.user_id);
            break;
        case 'system_broadcast':
            addChatMessage('system_broadcast', data.message, data.user_id);
            break;
        case 'error':
            addChatMessage('error', data.message, data.user_id);
            break;
        case 'clear_chat':
            clearChat();
            break;
        default:
            addChatMessage('system', `Unknown message: ${JSON.stringify(data)}`, 'system');
    }
}

function addChatMessage(type, content, user_id = 'system') {
    const chat = document.getElementById('chatops-chat');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'timestamp';
    timestampSpan.textContent = `[${timestamp}]`;
    
    const userSpan = document.createElement('span');
    userSpan.className = 'user-id';
    
    // Determine user display name
    let displayUser = user_id;
    if (user_id === 'system') {
        displayUser = '🤖 System';
        userSpan.style.color = '#6c757d';
    } else if (user_id === currentUserId) {
        displayUser = '👤 You';
        userSpan.style.color = '#007bff';
    } else {
        displayUser = `👥 ${user_id}`;
        userSpan.style.color = '#28a745';
    }
    
    userSpan.textContent = `${displayUser}: `;
    
    const contentSpan = document.createElement('span');
    contentSpan.className = 'content';
    
    // Format content with line breaks
    contentSpan.innerHTML = content.replace(/\n/g, '<br>');
    
    messageDiv.appendChild(timestampSpan);
    messageDiv.appendChild(userSpan);
    messageDiv.appendChild(contentSpan);
    chat.appendChild(messageDiv);
    
    // Auto-scroll to bottom
    chat.scrollTop = chat.scrollHeight;
    
    // Add to activity logs for important messages
    if (type === 'system' || type === 'error' || type === 'system_broadcast') {
        addLog(`ChatOps [${user_id}]: ${content.substring(0, 50)}${content.length > 50 ? '...' : ''}`);
    }
}

function clearChat() {
    const chat = document.getElementById('chatops-chat');
    chat.innerHTML = '';
    addChatMessage('system', 'Chat history cleared.', 'system');
}

async function startService(serviceName) {
    if (currentUserRole !== 'manager') {
        addLog('Error: Only managers can start services');
        alert('Only managers can start services!');
        return;
    }
    
    try {
        console.log(`Starting ${serviceName} as ${currentUserRole}`);
        
        const response = await fetch(`${API_BASE_URL}/management/start/${serviceName}`, {
            method: 'POST',
            headers: {
                'user-role': currentUserRole,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }
        
        const data = await response.json();
        addLog(`Started ${serviceName} service: ${data.message}`);
        setTimeout(fetchSystemStatus, 2000); // Refresh status after start
    } catch (error) {
        console.error('Start service error:', error);
        addLog(`Error starting ${serviceName}: ${error.message}`);
        alert(`Failed to start ${serviceName}: ${error.message}`);
    }
}

async function stopService(serviceName) {
    if (currentUserRole !== 'manager') {
        addLog('Error: Only managers can stop services');
        alert('Only managers can stop services!');
        return;
    }
    
    try {
        console.log(`Stopping ${serviceName} as ${currentUserRole}`);
        
        const response = await fetch(`${API_BASE_URL}/management/stop/${serviceName}`, {
            method: 'POST',
            headers: {
                'user-role': currentUserRole,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }
        
        const data = await response.json();
        addLog(`Stopped ${serviceName} service: ${data.message}`);
        setTimeout(fetchSystemStatus, 1000); // Refresh status after stop
    } catch (error) {
        console.error('Stop service error:', error);
        addLog(`Error stopping ${serviceName}: ${error.message}`);
        alert(`Failed to stop ${serviceName}: ${error.message}`);
    }
}

// Data Operations
async function createUser() {
    const name = prompt("Enter user name:");
    if (!name) return;
    
    const email = prompt("Enter user email:");
    if (!email) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'user-role': currentUserRole
            },
            body: JSON.stringify({ name, email })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Created user: ${data.name} (ID: ${data.id})`);
        document.getElementById('test-results').textContent = 
            `✅ Created User:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error creating user: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error creating user:\n${error.message}`;
    }
}

async function listUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/users/1`); // Get first user as example
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Retrieved user: ${data.name}`);
        document.getElementById('test-results').textContent = 
            `📋 User Details:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error listing users: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error listing users:\n${error.message}`;
    }
}

async function searchUsers() {
    const query = prompt("Enter search query for users:");
    if (!query) return;
    
    addLog(`Searching users for: ${query}`);
    document.getElementById('test-results').textContent = `Searching users for: ${query}...`;
}

async function createProduct() {
    const name = prompt("Enter product name:");
    if (!name) return;
    
    const price = parseFloat(prompt("Enter product price:"));
    if (isNaN(price)) return;
    
    const description = prompt("Enter product description:") || "";
    const category = prompt("Enter product category:") || "general";
    const stock = parseInt(prompt("Enter initial stock:")) || 0;
    
    try {
        const response = await fetch(`${API_BASE_URL}/products/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'user-role': currentUserRole
            },
            body: JSON.stringify({ 
                name, 
                price, 
                description, 
                category, 
                stock 
            })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Created product: ${data.name} ($${data.price})`);
        document.getElementById('test-results').textContent = 
            `✅ Created Product:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error creating product: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error creating product:\n${error.message}`;
    }
}

async function listProducts() {
    try {
        const response = await fetch(`${API_BASE_URL}/products/1`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Retrieved product: ${data.name}`);
        document.getElementById('test-results').textContent = 
            `🛍️ Product Details:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error listing products: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error listing products:\n${error.message}`;
    }
}

async function purchaseProduct() {
    const productId = prompt("Enter product ID to purchase:");
    if (!productId) return;
    
    const quantity = parseInt(prompt("Enter quantity:"));
    if (isNaN(quantity)) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/products/${productId}/purchase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'user-role': currentUserRole
            },
            body: JSON.stringify({ quantity })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Purchased ${quantity} of product ${productId} for $${data.total_price}`);
        document.getElementById('test-results').textContent = 
            `🛒 Purchase Result:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error purchasing product: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error purchasing product:\n${error.message}`;
    }
}

async function createOrder() {
    const userId = prompt("Enter your user ID:");
    if (!userId) return;
    
    const shippingAddress = prompt("Enter shipping address:");
    if (!shippingAddress) return;
    
    // For simplicity, we'll create an order with one item
    const productId = prompt("Enter product ID for order:");
    if (!productId) return;
    
    const quantity = parseInt(prompt("Enter quantity:"));
    if (isNaN(quantity)) return;
    
    const price = parseFloat(prompt("Enter product price:"));
    if (isNaN(price)) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'user-role': currentUserRole
            },
            body: JSON.stringify({ 
                user_id: userId,
                shipping_address: shippingAddress,
                items: [
                    {
                        product_id: productId,
                        quantity: quantity,
                        price: price
                    }
                ]
            })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Created order: #${data.id} for user ${data.user_id} - $${data.total_amount}`);
        document.getElementById('test-results').textContent = 
            `📦 Order Created:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error creating order: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error creating order:\n${error.message}`;
    }
}

async function listOrders() {
    try {
        const response = await fetch(`${API_BASE_URL}/orders/1`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Retrieved order: #${data.id}`);
        document.getElementById('test-results').textContent = 
            `📋 Order Details:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error listing orders: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error listing orders:\n${error.message}`;
    }
}

async function updateOrderStatus() {
    const orderId = prompt("Enter order ID to update:");
    if (!orderId) return;
    
    const status = prompt("Enter new status (pending/confirmed/shipped/delivered/cancelled):");
    if (!status) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${orderId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'user-role': currentUserRole
            },
            body: JSON.stringify({ status })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        addLog(`Updated order ${orderId} to status: ${data.status}`);
        document.getElementById('test-results').textContent = 
            `✏️ Order Updated:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        addLog(`Error updating order: ${error.message}`);
        document.getElementById('test-results').textContent = 
            `❌ Error updating order:\n${error.message}`;
    }
}

// Utility Functions
function addLog(message) {
    const logs = document.getElementById('activity-logs');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.textContent = `[${timestamp}] ${message}`;
    logs.appendChild(logEntry);
    logs.scrollTop = logs.scrollHeight;
}

async function fetchSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/management/status`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        console.log("System status data:", data);
        
        // Update service status with better detection
        for (const [serviceName, serviceInfo] of Object.entries(data.services)) {
            const isRunning = serviceInfo.status === 'running';
            const isHealthy = serviceInfo.healthy;
            
            updateStatus(serviceName, isHealthy, serviceInfo.status);
        }
        
        document.getElementById('total-requests').textContent = data.total_requests;
        document.getElementById('lb-state').textContent = data.load_balancer_state;
        document.getElementById('active-connections').textContent = Object.keys(data.services).length;
        
        return data;
    } catch (error) {
        console.error('Error fetching system status:', error);
        addLog(`Error fetching system status: ${error.message}`);
        
        // Fallback: set all services to unknown status
        updateStatus('user', false, 'unknown');
        updateStatus('product', false, 'unknown');
        updateStatus('order', false, 'unknown');
        updateStatus('gateway', false, 'unknown');
        
        return null;
    }
}

function updateStatus(service, isHealthy, status) {
    const statusElement = statusElements[service];
    const card = serviceCards[service];
    
    if (statusElement && card) {
        if (status === 'running' && isHealthy) {
            statusElement.textContent = '🟢 RUNNING';
            statusElement.style.color = '#28a745';
            card.classList.add('healthy');
            card.classList.remove('unhealthy');
        } else if (status === 'running' && !isHealthy) {
            statusElement.textContent = '🟡 RUNNING (UNHEALTHY)';
            statusElement.style.color = '#ffc107';
            card.classList.add('unhealthy');
            card.classList.remove('healthy');
        } else if (status === 'stopped') {
            statusElement.textContent = '🔴 STOPPED (BLOCKED)';
            statusElement.style.color = '#dc3545';
            card.classList.add('unhealthy');
            card.classList.remove('healthy');
        } else {
            statusElement.textContent = '⚪ UNKNOWN';
            statusElement.style.color = '#6c757d';
            card.classList.remove('healthy', 'unhealthy');
        }
    }
}

async function testUserService() {
    addLog('Testing User Service (REST)...');
    try {
        const response = await fetch(`${API_BASE_URL}/users/123`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        document.getElementById('test-results').textContent = 
            `👤 User Service Response:\n${JSON.stringify(data, null, 2)}`;
        addLog('User Service test completed successfully');
    } catch (error) {
        document.getElementById('test-results').textContent = 
            `❌ User Service Error:\n${error.message}`;
        addLog(`User Service test failed: ${error.message}`);
    }
}

async function testProductService() {
    addLog('Testing Product Service (REST)...');
    try {
        const response = await fetch(`${API_BASE_URL}/products/1`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        document.getElementById('test-results').textContent = 
            `🛍️ Product Service Response:\n${JSON.stringify(data, null, 2)}`;
        addLog('Product Service test completed successfully');
    } catch (error) {
        document.getElementById('test-results').textContent = 
            `❌ Product Service Error:\n${error.message}`;
        addLog(`Product Service test failed: ${error.message}`);
    }
}

async function testOrderService() {
    addLog('Testing Order Service (REST)...');
    try {
        const response = await fetch(`${API_BASE_URL}/orders/2`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        document.getElementById('test-results').textContent = 
            `📦 Order Service Response:\n${JSON.stringify(data, null, 2)}`;
        addLog('Order Service test completed successfully');
    } catch (error) {
        document.getElementById('test-results').textContent = 
            `❌ Order Service Error:\n${error.message}`;
        addLog(`Order Service test failed: ${error.message}`);
    }
}

async function testLoadBalancing() {
    addLog('Testing Load Balancing with 3 consecutive requests...');
    const results = [];
    
    for (let i = 0; i < 3; i++) {
        try {
            const response = await fetch(`${API_BASE_URL}/products/1`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            results.push(`Request ${i + 1}: Instance ${data.load_balanced_instance}`);
            addLog(`Load balancing request ${i + 1} routed to instance ${data.load_balanced_instance}`);
        } catch (error) {
            results.push(`Request ${i + 1}: ERROR - ${error.message}`);
            addLog(`Load balancing request ${i + 1} failed: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    document.getElementById('test-results').textContent = 
        `🔀 Load Balancing Test Results:\n${results.join('\n')}`;
    addLog('Load balancing test completed');
}

async function testAllServices() {
    addLog('Testing all services...');
    const results = [];
    
    try {
        // Test User Service
        const userResponse = await fetch(`${API_BASE_URL}/users/123`);
        results.push(`User Service: ${userResponse.ok ? '✅ OK' : '❌ FAILED'}`);
        
        // Test Product Service  
        const productResponse = await fetch(`${API_BASE_URL}/products/1`);
        results.push(`Product Service: ${productResponse.ok ? '✅ OK' : '❌ FAILED'}`);
        
        // Test Order Service
        const orderResponse = await fetch(`${API_BASE_URL}/orders/2`);
        results.push(`Order Service: ${orderResponse.ok ? '✅ OK' : '❌ FAILED'}`);
        
        document.getElementById('test-results').textContent = 
            `🧪 All Services Test:\n${results.join('\n')}`;
        addLog('All services test completed');
    } catch (error) {
        document.getElementById('test-results').textContent = 
            `❌ All Services Test Error:\n${error.message}`;
        addLog(`All services test failed: ${error.message}`);
    }
}

async function simulateFailure() {
    if (currentUserRole !== 'manager') {
        alert('Only managers can simulate failures!');
        return;
    }
    
    const serviceSelect = document.getElementById('service-select');
    const service = serviceSelect.value;
    
    addLog(`Simulating failure for ${service} service...`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/management/simulate_failure/${service}`, {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        addLog(`Success: ${data.message}`);
        setTimeout(fetchSystemStatus, 1000);
    } catch (error) {
        addLog(`Error simulating failure: ${error.message}`);
    }
}

async function recoverService() {
    if (currentUserRole !== 'manager') {
        alert('Only managers can recover services!');
        return;
    }
    
    const serviceSelect = document.getElementById('service-select');
    const service = serviceSelect.value;
    
    addLog(`Recovering ${service} service...`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/management/recover/${service}`, {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        addLog(`Success: ${data.message}`);
        setTimeout(fetchSystemStatus, 1000);
    } catch (error) {
        addLog(`Error recovering service: ${error.message}`);
    }
}

// Initialize Dashboard
async function initializeDashboard() {
    addLog('Dashboard initialized');
    addLog('Connecting to API Gateway...');
    
    // Set up role UI
    updateUIForRole();
    
    // Initial status check
    await fetchSystemStatus();
    
    // Update status every 5 seconds
    setInterval(fetchSystemStatus, 5000);
    
    // Auto-connect WebSocket after a delay
    setTimeout(() => {
        addChatMessage('system', 'Select your role and click "Connect WebSocket" to start ChatOps.', 'system');
    }, 2000);
    
    addLog('Dashboard ready! Use the buttons to interact with services.');
}

// Add Enter key support for chat input
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatops-input');
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatOpsCommand();
        }
    });
    
    initializeDashboard();
});