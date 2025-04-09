// WebSocket Debug Utility
console.log("WebSocket Debug Utility loaded");

function debugWebSocketConnection(wsUrl) {
    const debugElement = document.getElementById('ws-debug');
    const statusElement = document.getElementById('ws-status');
    const logElement = document.createElement('div');
    logElement.className = 'border p-2 mt-2 bg-light';
    logElement.style.maxHeight = '200px';
    logElement.style.overflow = 'auto';
    debugElement.appendChild(logElement);
    
    function log(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = type === 'error' ? 'text-danger' : (type === 'success' ? 'text-success' : 'text-muted');
        entry.innerHTML = `<small>${new Date().toLocaleTimeString()}: ${message}</small>`;
        logElement.appendChild(entry);
        logElement.scrollTop = logElement.scrollHeight;
        console.log(`[${type}] ${message}`);
    }
    
    log(`Attempting connection to: ${wsUrl}`);
    
    try {
        // Check if WebSockets are supported
        if (!window.WebSocket) {
            log('WebSockets not supported in this browser!', 'error');
            statusElement.textContent = 'WebSockets not supported ❌';
            statusElement.style.color = 'red';
            return null;
        }
        
        // Create WebSocket connection
        const socket = new WebSocket(wsUrl);
        
        // Connection opened
        socket.onopen = function(event) {
            log('Connection established successfully', 'success');
            statusElement.textContent = 'Connected ✅';
            statusElement.style.color = 'green';
            
            // Connection details
            log(`Protocol: ${socket.protocol || 'none'}`);
            log(`URL: ${wsUrl}`);
            
            // Check channel layer
            socket.send(JSON.stringify({
                'message': 'Channel layer test',
                'username': 'Debug Test',
                'type': 'test'
            }));
        };
        
        // Listen for messages
        socket.onmessage = function(event) {
            log(`Message received: ${event.data}`, 'success');
            try {
                const data = JSON.parse(event.data);
                if (data.error) {
                    log(`Error in message: ${data.error}`, 'error');
                }
            } catch (e) {
                log(`Error parsing message: ${e}`, 'error');
            }
        };
        
        // Connection closed
        socket.onclose = function(event) {
            const reason = event.reason || 'Unknown reason';
            const clean = event.wasClean ? 'Clean' : 'Unclean';
            log(`Connection closed: ${clean} close with code ${event.code}. Reason: ${reason}`, 'error');
            statusElement.textContent = `Disconnected (Code: ${event.code}) ❌`;
            statusElement.style.color = 'red';
        };
        
        // Connection error
        socket.onerror = function(error) {
            log('WebSocket error occurred. Check browser console for details.', 'error');
            statusElement.textContent = 'Connection error ❌';
            statusElement.style.color = 'red';
        };
        
        return socket;
    } catch (error) {
        log(`Error creating WebSocket: ${error.message}`, 'error');
        statusElement.textContent = 'WebSocket creation error ❌';
        statusElement.style.color = 'red';
        return null;
    }
}

// Test server environment
function checkServerEnvironment() {
    const debugElement = document.getElementById('ws-debug');
    const envElement = document.createElement('div');
    envElement.className = 'border p-2 mt-2 bg-light';
    debugElement.appendChild(envElement);
    
    envElement.innerHTML = `
        <h6>Browser Environment</h6>
        <small>Browser: ${navigator.userAgent}</small><br>
        <small>WebSocket Support: ${window.WebSocket ? 'Yes ✅' : 'No ❌'}</small><br>
        <small>Secure Context: ${window.isSecureContext ? 'Yes ✅' : 'No ❌'}</small>
    `;
    
    // Fetch server info
    fetch('/chat/api/server-info/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Server info API not available');
            }
            return response.json();
        })
        .then(data => {
            const serverInfo = document.createElement('div');
            serverInfo.className = 'mt-2';
            serverInfo.innerHTML = `
                <h6>Server Environment</h6>
                <small>Channels Version: ${data.channels_version || 'Unknown'}</small><br>
                <small>Redis Available: ${data.redis_available ? 'Yes ✅' : 'No ❌'}</small><br>
                <small>ASGI Server: ${data.asgi_server || 'Unknown'}</small>
            `;
            envElement.appendChild(serverInfo);
        })
        .catch(error => {
            const serverInfo = document.createElement('div');
            serverInfo.className = 'mt-2 text-danger';
            serverInfo.innerHTML = `<small>Error fetching server info: ${error.message}</small>`;
            envElement.appendChild(serverInfo);
        });
} 