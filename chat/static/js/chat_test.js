// Simple test for WebSocket connection
console.log("Initializing chat test");

function testWebSocket() {
    try {
        // Create a test WebSocket connection
        const testSocket = new WebSocket('ws://' + window.location.host + '/ws/chat/test_room/');
        
        testSocket.onopen = function(e) {
            console.log('Test WebSocket connection established successfully');
            document.getElementById('ws-status').textContent = "WebSocket connected ✅";
            document.getElementById('ws-status').style.color = "green";
            
            // Try sending a test message
            testSocket.send(JSON.stringify({
                'message': 'Test message',
                'username': 'Test User'
            }));
        };
        
        testSocket.onmessage = function(e) {
            console.log('Test message received:', e.data);
            document.getElementById('ws-messages').textContent = "Message received: " + e.data;
        };
        
        testSocket.onclose = function(e) {
            console.log('Test WebSocket connection closed');
            document.getElementById('ws-status').textContent = "WebSocket disconnected ❌";
            document.getElementById('ws-status').style.color = "red";
        };
        
        testSocket.onerror = function(e) {
            console.error('Test WebSocket error:', e);
            document.getElementById('ws-status').textContent = "WebSocket error ❌";
            document.getElementById('ws-status').style.color = "red";
        };
        
        // Clean up after 10 seconds
        setTimeout(() => {
            if (testSocket.readyState === WebSocket.OPEN) {
                testSocket.close();
            }
        }, 10000);
        
        return testSocket;
    } catch (error) {
        console.error('Error creating test WebSocket:', error);
        document.getElementById('ws-status').textContent = "WebSocket creation error ❌";
        document.getElementById('ws-status').style.color = "red";
        return null;
    }
} 