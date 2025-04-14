// Chat WebSocket handler with auto-reconnect functionality
class ChatWebSocket {
    constructor(roomName, username) {
        this.roomName = roomName;
        this.username = username;
        this.connectionAttempts = 0;
        this.maxAttempts = 5;
        this.reconnectDelay = 3000; // 3 seconds delay between reconnection attempts
        this.reconnectTimeout = null;
        this.socket = null;
        this.isConnecting = false;
        this.statusElement = document.getElementById('chat-status');
        
        console.log(`Initializing ChatWebSocket for room "${roomName}" and user "${username}"`);
        
        // Initial connection
        this.connect();
        
        // Setup reconnection on visibility change (when user returns to the tab)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && 
                (!this.socket || this.socket.readyState === WebSocket.CLOSED)) {
                console.log('Page became visible, attempting to reconnect WebSocket');
                this.connect();
            }
        });
    }
    
    updateStatus(status, color = 'black') {
        console.log(`Chat status: ${status}`);
        if (this.statusElement) {
            this.statusElement.textContent = status;
            this.statusElement.style.color = color;
        }
    }
    
    connect() {
        if (this.isConnecting) return;
        this.isConnecting = true;
        this.connectionAttempts++;
        
        if (this.connectionAttempts > this.maxAttempts) {
            this.updateStatus('Connection failed after multiple attempts', 'red');
            console.error('Max reconnection attempts reached');
            this.isConnecting = false;
            return;
        }
        
        this.updateStatus(`Connecting (${this.connectionAttempts}/${this.maxAttempts})...`, 'orange');
        
        try {
            // Use 127.0.0.1 instead of localhost to avoid DNS resolution issues
            const host = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
            const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
            const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsUrl = `${wsProtocol}${host}:${port}/ws/chat/${encodeURIComponent(this.roomName)}/`;
            
            console.log(`Attempting WebSocket connection to ${wsUrl}`);
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = (e) => {
                console.log('WebSocket connection established');
                this.updateStatus('Connected', 'green');
                this.connectionAttempts = 0;
                this.isConnecting = false;
                
                // Announce connection
                this.sendMessage('system', `${this.username} has joined the chat`);
            };
            
            this.socket.onmessage = (e) => {
                console.log('WebSocket message received:', e.data);
                try {
                    const data = JSON.parse(e.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            };
            
            this.socket.onclose = (e) => {
                this.updateStatus('Disconnected', 'red');
                console.warn(`WebSocket closed: ${e.reason || 'Unknown reason'} (Code: ${e.code})`);
                this.isConnecting = false;
                
                // Attempt reconnection
                if (this.connectionAttempts < this.maxAttempts) {
                    console.log(`Attempting to reconnect in ${this.reconnectDelay / 1000}s...`);
                    this.reconnectTimeout = setTimeout(() => this.connect(), this.reconnectDelay);
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Connection error', 'red');
                this.isConnecting = false;
            };
            
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.updateStatus('WebSocket error', 'red');
            this.isConnecting = false;
            
            // Try to reconnect
            if (this.connectionAttempts < this.maxAttempts) {
                this.reconnectTimeout = setTimeout(() => this.connect(), this.reconnectDelay);
            }
        }
    }
    
    sendMessage(type, content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                'type': type,
                'message': content,
                'username': this.username
            }));
            return true;
        } else {
            console.warn('Cannot send message: WebSocket not connected');
            // Attempt to reconnect
            if (!this.isConnecting) {
                this.connect();
            }
            return false;
        }
    }
    
    handleMessage(data) {
        // Override this method in your application to handle incoming messages
        console.log('Message received:', data);
    }
    
    disconnect() {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }
        
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Look for chat container
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        // Extract room name and username from data attributes or use defaults
        const roomName = chatContainer.getAttribute('data-room') || 'general';
        const username = chatContainer.getAttribute('data-username') || 'Guest';
        
        // Initialize WebSocket connection
        const chatWs = new ChatWebSocket(roomName, username);
        
        // Store for global access
        window.chatWs = chatWs;
    }
}); 